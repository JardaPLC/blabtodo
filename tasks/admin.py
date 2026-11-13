"""
The management pages for tasks, rooms and finished tasks.

For now these are Django's own admin pages. The touch-friendly task editor replaces them
for everyday use in milestone 2.
"""

import segno
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from . import cards
from .forms import RoomAdminForm, TaskAdminForm
from .models import Completion, Room, Task

# Changing any of these changes on which days the task is scheduled.
RULE_FIELDS = {"repeat", "interval", "weekdays", "day_of_month", "start_date", "end_date"}


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    form = RoomAdminForm
    list_display = ["label", "position", "is_active"]
    list_editable = ["position", "is_active"]

    @admin.display(description=_("room"))
    def label(self, room):
        return f"{room.emoji}  {room.name}"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    form = TaskAdminForm
    list_display = ["label", "room", "repeat", "next_card_date", "is_active"]
    list_filter = ["is_active", "room", "repeat"]
    actions = ["show_today", "skip_waiting_card", "print_stickers"]
    fieldsets = [
        (None, {"fields": ["picture", "names", "hint", "room", "effort", "faces"]}),
        (
            _("When"),
            {
                "fields": [
                    "repeat",
                    "interval",
                    "weekdays",
                    "day_of_month",
                    "start_date",
                    "end_date",
                    "day_only",
                ]
            },
        ),
        (_("State"), {"fields": ["is_active", "next_card_date"]}),
    ]

    @admin.display(description=_("task"))
    def label(self, task):
        return f"{task.emoji}  {task.name}"

    def get_urls(self):
        stickers = self.admin_site.admin_view(self.stickers_view)
        return [path("stickers/", stickers, name="tasks_task_stickers"), *super().get_urls()]

    @admin.action(description=_("Print QR stickers"))
    def print_stickers(self, request, queryset):
        chosen = ",".join(str(pk) for pk in queryset.values_list("pk", flat=True))
        return redirect(reverse("admin:tasks_task_stickers") + "?ids=" + chosen)

    def stickers_view(self, request):
        """
        A page of QR stickers for the chosen tasks.

        Each code holds the full address of the task's scan page, as this browser reached
        the app. That is why the stickers are printed from the address the family uses.
        """
        ids = [int(part) for part in request.GET.get("ids", "").split(",") if part.isdigit()]
        stickers = []
        for task in Task.objects.filter(pk__in=ids, is_active=True):
            address = request.build_absolute_uri(reverse("task-qr", args=[task.ensure_qr_key()]))
            code = segno.make(address, error="m").svg_inline(omitsize=True, title=task.name)
            stickers.append((task, mark_safe(code)))  # noqa: S308 - segno escapes the title
        context = {"stickers": stickers, "address": request.build_absolute_uri("/")}
        return TemplateResponse(request, "tasks/stickers.html", context)

    def has_delete_permission(self, request, obj=None):
        # A task that was never done can be deleted, for example one added by mistake.
        # Once it has been done, it can only be switched off, so that the archive stays
        # whole. (Deleting several from the list is checked the same way: the database
        # refuses to delete a task that has finished cards, and the page says which.)
        if obj is not None and obj.completions.exists():
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        day = cards.today()
        date_set_by_hand = "next_card_date" in form.changed_data and obj.next_card_date is not None
        date_cleared_by_hand = "next_card_date" in form.changed_data and obj.next_card_date is None
        switched_on_again = change and "is_active" in form.changed_data and obj.is_active

        if date_set_by_hand:
            pass
        elif not change:
            cards.plan_first_card(obj)
        elif switched_on_again:
            cards.plan_from(obj, day)
        elif date_cleared_by_hand or RULE_FIELDS & set(form.changed_data):
            cards.replan_after_edit(obj, day)
        super().save_model(request, obj, form, change)

    @admin.action(description=_("Show the card today"))
    def show_today(self, request, queryset):
        day = cards.today()
        for task in queryset:
            cards.show_today(task, day)
        self.message_user(request, _("Done."), messages.SUCCESS)

    @admin.action(description=_("Skip the waiting card (not needed this time)"))
    def skip_waiting_card(self, request, queryset):
        day = cards.today()
        skipped = 0
        for task in queryset:
            if cards.is_waiting(task, day):
                cards.skip(task, day)
                skipped += 1
        message = ngettext("%(count)d card skipped.", "%(count)d cards skipped.", skipped)
        self.message_user(request, message % {"count": skipped}, messages.SUCCESS)


@admin.register(Completion)
class CompletionAdmin(admin.ModelAdmin):
    list_display = ["task", "card_date", "done_at", "who", "note", "points"]
    list_filter = ["done_by", "task"]
    date_hierarchy = "done_at"
    actions = ["put_card_back"]
    fields = ["task", "card_date", "done_at", "done_by", "recorded_on", "note", "points"]
    readonly_fields = ["task", "card_date", "recorded_on"]

    @admin.display(description=_("done by"))
    def who(self, completion):
        return ", ".join(str(person) for person in completion.done_by.all())

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("task").prefetch_related("done_by")

    def has_add_permission(self, request):
        # A finished task is recorded by marking its card done on the Today screen.
        return False

    @admin.action(description=_("Undo: put the card back as if it had not been done"))
    def put_card_back(self, request, queryset):
        undone, refused = 0, 0
        for completion in queryset.order_by("-card_date"):
            try:
                cards.undo(completion)
                undone += 1
            except cards.CannotUndo:
                refused += 1
        if undone:
            message = ngettext("%(count)d card put back.", "%(count)d cards put back.", undone)
            self.message_user(request, message % {"count": undone}, messages.SUCCESS)
        if refused:
            self.message_user(
                request,
                _("Only the latest finished card of a task can be put back."),
                messages.WARNING,
            )
