import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from . import picture_drafts, schedule
from .catalogue import FALLBACK_EMOJI, ROOMS_BY_KEY, TASKS_BY_KEY


def pick_name(names: dict, language: str | None = None) -> str:
    """The name in the wanted language, else in the default language, else any there is."""
    language = language or get_language() or settings.LANGUAGE_CODE
    return (
        names.get(language)
        or names.get(settings.LANGUAGE_CODE)
        or next((name for name in names.values() if name), "")
    )


class NamedInLanguages(models.Model):
    """Something with a name in each language. Only the default language is required."""

    names = models.JSONField(_("name"), default=dict)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    @property
    def name(self) -> str:
        return pick_name(self.names)


class Room(NamedInLanguages):
    """A place in or around the home: the kitchen, but also the garden or the garage."""

    picture = models.CharField(_("picture"), max_length=40, blank=True)
    position = models.PositiveSmallIntegerField(
        _("position"),
        default=0,
        help_text=_("Rooms are shown in this order, lowest first. It never changes by itself."),
    )
    is_active = models.BooleanField(_("in use"), default=True)

    class Meta:
        verbose_name = _("room")
        verbose_name_plural = _("rooms")
        ordering = ["position", "id"]

    @property
    def emoji(self) -> str:
        entry = ROOMS_BY_KEY.get(self.picture)
        return entry.emoji if entry else FALLBACK_EMOJI

    @property
    def picture_draft(self) -> dict:
        return picture_drafts.picture_of("rooms", self.picture)


class Task(NamedInLanguages):
    """
    A household task: what it is, how often, and the day its next card appears.

    There is no table of cards. A card on the Today screen is a task whose
    `next_card_date` has arrived (docs/design.md, section 5).
    """

    class Repeat(models.TextChoices):
        ONCE = schedule.ONCE, _("Once")
        DAYS = schedule.DAYS, _("Every day, or every few days")
        WEEKLY = schedule.WEEKLY, _("On chosen days of the week")
        MONTHLY = schedule.MONTHLY, _("On a day of the month")
        ON_DEMAND = schedule.ON_DEMAND, _("Only when asked for, for example by its QR code")

    class Effort(models.IntegerChoices):
        SMALL = 1, _("Small")
        MEDIUM = 2, _("Medium")
        BIG = 3, _("Big")

    picture = models.CharField(_("picture"), max_length=40, blank=True)
    hint = models.CharField(
        _("hint"),
        max_length=120,
        blank=True,
        help_text=_("A short note shown when marking it done, for example where things are."),
    )
    room = models.ForeignKey(
        Room,
        verbose_name=_("room"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
    )
    effort = models.PositiveSmallIntegerField(
        _("effort"), choices=Effort.choices, default=Effort.SMALL
    )

    repeat = models.CharField(
        _("repeats"), max_length=10, choices=Repeat.choices, default=Repeat.DAYS
    )
    interval = models.PositiveSmallIntegerField(
        _("every"),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text=_(
            "1 means every day, week or month. 2 means every second one, and so on. "
            "Not used for a one-time task."
        ),
    )
    weekdays = models.JSONField(_("days of the week"), default=list, blank=True)
    day_of_month = models.PositiveSmallIntegerField(
        _("day of the month"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text=_("31 means the last day in shorter months."),
    )
    start_date = models.DateField(
        _("starts on"),
        default=timezone.localdate,
        help_text=_("For a one-time task, this is its day."),
    )
    end_date = models.DateField(_("ends on"), null=True, blank=True)

    faces = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_("meant for"),
        blank=True,
        related_name="tasks",
        help_text=_("Leave empty if anyone can do it. It is a hint: anyone may still do it."),
    )
    day_only = models.BooleanField(
        _("only makes sense on the day"),
        default=False,
        help_text=_(
            "For things like putting the bins out: the card disappears at the end of the "
            "day if nobody did it."
        ),
    )
    next_task = models.ForeignKey(
        "self",
        verbose_name=_("then show"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="comes_after",
        help_text=_(
            "When this task is done, the card of the chosen task appears on Today, for "
            'example "Empty the dishwasher" after "Load the dishwasher". Best set to '
            '"Only when asked for".'
        ),
    )
    is_active = models.BooleanField(_("in use"), default=True)
    # The secret part of the address in the task's QR code. Made when the first sticker is
    # printed, and kept, so that printed stickers keep working.
    qr_key = models.CharField(max_length=32, unique=True, null=True, blank=True, editable=False)
    next_card_date = models.DateField(_("next card appears on"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("task")
        verbose_name_plural = _("tasks")
        ordering = ["id"]

    @property
    def emoji(self) -> str:
        entry = TASKS_BY_KEY.get(self.picture)
        return entry.emoji if entry else FALLBACK_EMOJI

    @property
    def picture_draft(self) -> dict:
        return picture_drafts.picture_of("tasks", self.picture)

    def ensure_qr_key(self) -> str:
        if not self.qr_key:
            self.qr_key = secrets.token_urlsafe(12)
            self.save(update_fields=["qr_key"])
        return self.qr_key

    @property
    def rule(self) -> schedule.Rule:
        return schedule.Rule(
            repeat=self.repeat,
            start=self.start_date,
            interval=self.interval,
            weekdays=tuple(self.weekdays or ()),
            day_of_month=self.day_of_month,
            end=self.end_date,
        )

    def clean(self):
        errors = {}
        if self.repeat == self.Repeat.WEEKLY and not self.weekdays:
            errors["weekdays"] = _("Choose at least one day of the week.")
        if self.repeat == self.Repeat.MONTHLY and not self.day_of_month:
            errors["day_of_month"] = _("Choose the day of the month.")
        if self.end_date and self.start_date and self.end_date < self.start_date:
            errors["end_date"] = _("The end cannot be before the start.")
        errors.update(self._chain_errors())
        if errors:
            raise ValidationError(errors)

    def _chain_errors(self) -> dict:
        """What is wrong with this task's place in a chain, if anything."""
        errors = {}
        follower = self.next_task
        if follower is not None:
            if follower.repeat == self.Repeat.ONCE:
                # Once done, a one-time task would come back every time the chain reached it.
                errors["next_task"] = _("A one-time task cannot come next. Choose another kind.")
            elif self._chain_leads_back(follower):
                errors["next_task"] = _(
                    "This would make a circle that never ends. Choose a task that does not "
                    "lead back here."
                )
        if (
            self.repeat == self.Repeat.ONCE
            and self.pk is not None
            and Task.objects.filter(next_task=self).exists()
        ):
            errors["repeat"] = _(
                "Another task shows this one when it is done, so it cannot be a one-time task."
            )
        return errors

    def _chain_leads_back(self, follower: "Task") -> bool:
        if self.pk is None:
            # A task that does not exist yet cannot be pointed at by anything.
            return False
        seen = set()
        current = follower
        while current is not None and current.pk not in seen:
            if current.pk == self.pk:
                return True
            seen.add(current.pk)
            current = current.next_task
        return False


class Completion(models.Model):
    """The record written when a card is done: who did it, when, and for which card."""

    task = models.ForeignKey(
        Task, verbose_name=_("task"), on_delete=models.PROTECT, related_name="completions"
    )
    # The day the card had appeared. With the task it identifies the card, so that two
    # people tapping Done on the same card at the same moment produce one record.
    card_date = models.DateField(_("card of"))
    done_at = models.DateTimeField(_("done at"), default=timezone.now)
    done_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name=_("done by"), related_name="completions"
    )
    recorded_on = models.ForeignKey(
        "people.Device",
        verbose_name=_("recorded on"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    note = models.CharField(_("note"), max_length=280, blank=True)
    # Copied from the task's effort at that moment, so that changing a task later does
    # not rewrite what was earned.
    points = models.PositiveSmallIntegerField(_("points"), default=1)
    # The task whose card this completion made appear (its task's "then show"), and the
    # day that task's next card was planned for before. Undo uses both to put it back.
    brought_forward = models.ForeignKey(
        Task, null=True, blank=True, on_delete=models.SET_NULL, related_name="+", editable=False
    )
    brought_forward_from = models.DateField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = _("finished task")
        verbose_name_plural = _("finished tasks")
        ordering = ["-done_at"]
        constraints = [
            models.UniqueConstraint(fields=["task", "card_date"], name="one_completion_per_card")
        ]

    def __str__(self):
        return f"{self.task} ({self.card_date})"
