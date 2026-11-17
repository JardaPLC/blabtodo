"""
The adult view: tasks and rooms edited in the app, on a phone, after an adult's PIN.

Django's admin pages stay for people, devices and anything unusual; these pages are for
everyday changes. Both use the same rules (`cards.plan_after_edit`, the model checks).
"""

from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from people.adults import adult_required

from . import cards, catalogue
from .forms import RoomEditForm, TaskEditForm
from .labels import repeat_summary
from .models import Room, Task
from .stickers import stickers_context

# The choice on the catalogue page for a task or room with no catalogue picture.
OWN = "own"


def _samples(kind: str) -> list:
    """
    The catalogue's pictures as unsaved tasks or rooms, sorted by name, so that each can be
    drawn with `_picture.html` in whatever picture set this device shows.
    """
    model, entries = (Task, catalogue.TASKS) if kind == "tasks" else (Room, catalogue.ROOMS)
    samples = [model(picture=entry.key, names={"cs": str(entry.name)}) for entry in entries]
    return sorted(samples, key=lambda sample: sample.name.casefold())


@require_GET
@adult_required
def home(request):
    return render(request, "tasks/manage/home.html")


def _preview(form, model, entries_by_key) -> dict:
    """The picture the editor shows as chosen, no picture, and the chosen picture's name."""
    key = form["picture"].value() or ""
    entry = entries_by_key.get(key)
    return {
        "preview": model(picture=key),
        "blank": model(picture=""),
        "picture_name": str(entry.name) if entry else "",
    }


# ---- Tasks ----


@require_GET
@adult_required
def task_list(request):
    """Every task, grouped by room in the rooms' order; tasks not in use at the end."""
    day = cards.today()
    tasks = list(Task.objects.select_related("room").order_by("id"))
    for task in tasks:
        task.summary = repeat_summary(task)
        task.waiting = cards.is_waiting(task, day)
    in_use = [task for task in tasks if task.is_active]
    groups = []
    for room in Room.objects.all():
        room_tasks = [task for task in in_use if task.room_id == room.pk]
        if room_tasks:
            groups.append({"title": room.name, "room": room, "tasks": room_tasks})
    roomless = [task for task in in_use if task.room_id is None]
    if roomless:
        groups.append({"title": _("Elsewhere"), "room": None, "tasks": roomless})
    context = {"groups": groups, "not_in_use": [task for task in tasks if not task.is_active]}
    return render(request, "tasks/manage/task_list.html", context)


@require_http_methods(["GET", "POST"])
@adult_required
def task_new(request):
    """First the catalogue to start from; then the editor, filled in from the choice."""
    picture = request.GET.get("picture") or request.POST.get("picture", "")
    if request.method == "GET" and not picture:
        return render(
            request,
            "tasks/manage/catalogue.html",
            {"samples": _samples("tasks"), "kind": "tasks", "own_url": "?picture=" + OWN},
        )

    initial = {}
    entry = catalogue.TASKS_BY_KEY.get(picture)
    if entry is not None:
        initial = {"picture": entry.key, "effort": entry.effort}
        if entry.room:
            # The room it usually belongs to, if this home has a room with that picture.
            room = Room.objects.filter(picture=entry.room, is_active=True).first()
            initial["room"] = room.pk if room else None
    return _task_editor(request, Task(), initial=initial)


@require_http_methods(["GET", "POST"])
@adult_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    return _task_editor(request, task)


def _task_editor(request, task: Task, *, initial=None):
    created = task.pk is None
    form = TaskEditForm(request.POST or None, instance=task, initial=initial)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            task = form.save(commit=False)
            cards.plan_after_edit(task, set(form.changed_data), created=created, day=cards.today())
            task.save()
            form.save_m2m()
        messages.success(request, _("Saved: %(name)s") % {"name": task.name})
        return redirect("manage-tasks")

    day = cards.today()
    context = {
        "form": form,
        "task": task,
        "created": created,
        "waiting": not created and cards.is_waiting(task, day),
        "may_delete": not created and not task.completions.exists(),
        "pictures": _samples("tasks"),
        **_preview(form, Task, catalogue.TASKS_BY_KEY),
        "rooms": Room.objects.filter(is_active=True),
    }
    return render(request, "tasks/manage/task_form.html", context)


@require_POST
@adult_required
def task_show(request, task_id):
    """Show the card today, or one more round of it if it is already waiting."""
    task = get_object_or_404(Task, pk=task_id, is_active=True)
    cards.show_today(task, cards.today())
    task.refresh_from_db()
    if task.rounds > 1:
        message = _("%(name)s: %(rounds)s× in all") % {"name": task.name, "rounds": task.rounds}
    else:
        message = _("%(name)s is waiting on Today.") % {"name": task.name}
    messages.success(request, message)
    return redirect("manage-task", task_id=task.pk)


@require_POST
@adult_required
def task_skip(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    day = cards.today()
    if cards.is_waiting(task, day):
        cards.skip(task, day)
        messages.success(request, _("Skipped: %(name)s") % {"name": task.name})
    return redirect("manage-task", task_id=task.pk)


@require_POST
@adult_required
def task_delete(request, task_id):
    """Only a task that was never done can be deleted; one that was can be switched off."""
    task = get_object_or_404(Task, pk=task_id)
    if task.completions.exists():
        messages.error(
            request, _("This task has been done before, so it can only be switched off.")
        )
        return redirect("manage-task", task_id=task.pk)
    name = task.name
    task.delete()
    messages.success(request, _("Deleted: %(name)s") % {"name": name})
    return redirect("manage-tasks")


@require_GET
@adult_required
def task_sticker(request, task_id):
    task = get_object_or_404(Task, pk=task_id, is_active=True)
    back = reverse("manage-task", args=[task.pk])
    return render(request, "tasks/stickers.html", stickers_context(request, [task], back))


# ---- Rooms ----


@require_GET
@adult_required
def room_list(request):
    rooms = list(Room.objects.all())
    for room in rooms:
        room.task_count = room.tasks.filter(is_active=True).count()
    return render(request, "tasks/manage/room_list.html", {"rooms": rooms})


@require_http_methods(["GET", "POST"])
@adult_required
def room_new(request):
    picture = request.GET.get("picture") or request.POST.get("picture", "")
    if request.method == "GET" and not picture:
        # Rooms the home already has are not offered again.
        taken = set(Room.objects.values_list("picture", flat=True))
        samples = [room for room in _samples("rooms") if room.picture not in taken]
        return render(
            request,
            "tasks/manage/catalogue.html",
            {"samples": samples, "kind": "rooms", "own_url": "?picture=" + OWN},
        )
    initial = {"picture": picture} if picture in catalogue.ROOMS_BY_KEY else {}
    return _room_editor(request, Room(), initial=initial)


@require_http_methods(["GET", "POST"])
@adult_required
def room_edit(request, room_id):
    return _room_editor(request, get_object_or_404(Room, pk=room_id))


def _room_editor(request, room: Room, *, initial=None):
    created = room.pk is None
    form = RoomEditForm(request.POST or None, instance=room, initial=initial)
    if request.method == "POST" and form.is_valid():
        room = form.save(commit=False)
        if created:
            # A new room goes to the end of the list.
            last = Room.objects.aggregate(last=Max("position"))["last"] or 0
            room.position = last + 1
        room.save()
        messages.success(request, _("Saved: %(name)s") % {"name": room.name})
        return redirect("manage-rooms")
    context = {
        "form": form,
        "room": room,
        "created": created,
        "pictures": _samples("rooms"),
        **_preview(form, Room, catalogue.ROOMS_BY_KEY),
        "task_count": 0 if created else room.tasks.count(),
    }
    return render(request, "tasks/manage/room_form.html", context)


@require_POST
@adult_required
def room_move(request, room_id, direction):
    """Move a room one place up or down in the list. The positions are renumbered."""
    rooms = list(Room.objects.all())
    index = next((i for i, room in enumerate(rooms) if room.pk == room_id), None)
    if index is not None:
        other = index - 1 if direction == "up" else index + 1
        if 0 <= other < len(rooms):
            rooms[index], rooms[other] = rooms[other], rooms[index]
        with transaction.atomic():
            for position, room in enumerate(rooms, start=1):
                if room.position != position:
                    room.position = position
                    room.save(update_fields=["position"])
    return redirect("manage-rooms")


@require_POST
@adult_required
def room_delete(request, room_id):
    """A room can always be deleted. Its tasks stay, without a room."""
    room = get_object_or_404(Room, pk=room_id)
    name = room.name
    room.delete()
    messages.success(request, _("Deleted: %(name)s") % {"name": name})
    return redirect("manage-rooms")
