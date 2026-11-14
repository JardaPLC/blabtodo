"""
Cards: which tasks are waiting, and what happens when one is done, undone or skipped.

A card is not stored. It is a task whose `next_card_date` has arrived. Everything that
moves that date lives in this file (docs/design.md, section 5).
"""

from datetime import date, timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import Completion, Task
from .schedule import first_on_or_after, next_after

# Anyone may undo for this long on the device that recorded the completion. The Undo bar
# is shown for about ten seconds; the rest is slack for slow fingers and slow networks.
UNDO_WINDOW = timedelta(seconds=45)


class CardGone(Exception):
    """The card is no longer waiting: someone else did it, or the task changed."""


class CannotUndo(Exception):
    """The completion cannot be undone any more."""


def today(now=None) -> date:
    """Today's date in the household's time zone."""
    return timezone.localdate(now)


def waiting_cards(day: date):
    """The tasks whose card is waiting on this day, oldest card first."""
    _move_day_only_tasks_on(day)
    waiting = Q(day_only=False, next_card_date__lte=day) | Q(day_only=True, next_card_date=day)
    return (
        Task.objects.filter(waiting, is_active=True)
        .select_related("room")
        .prefetch_related("faces")
        .order_by("next_card_date", "id")
    )


def _move_day_only_tasks_on(day: date) -> None:
    """A day-only card that nobody did disappears: its task moves on to its next day."""
    missed = Task.objects.filter(is_active=True, day_only=True, next_card_date__lt=day)
    for task in missed:
        task.next_card_date = first_on_or_after(task.rule, day)
        task.save(update_fields=["next_card_date"])


def is_waiting(task: Task, day: date) -> bool:
    if not task.is_active or task.next_card_date is None:
        return False
    if task.day_only:
        return task.next_card_date == day
    return task.next_card_date <= day


def plan_first_card(task: Task) -> None:
    """Set the day of a new task's first card. Does not save."""
    task.next_card_date = first_on_or_after(task.rule, task.start_date)


def plan_from(task: Task, day: date) -> None:
    """
    Set the day of the next card as if the task began on this day. Does not save.

    For a task that is switched on again: it starts afresh instead of showing a card
    "since" the day it was switched off.
    """
    task.next_card_date = first_on_or_after(task.rule, day)


def replan_after_edit(task: Task, day: date) -> None:
    """
    Set the day of the next card after the task's repeat settings changed. Does not save.

    A card that is already waiting stays. Otherwise the next card is the first scheduled
    day from today on, or from tomorrow if the task was already done today.
    """
    if is_waiting(task, day):
        return
    done_today = task.pk is not None and task.completions.filter(done_at__date=day).exists()
    task.next_card_date = first_on_or_after(
        task.rule, day + timedelta(days=1) if done_today else day
    )


def complete(*, task_id: int, card_date: date, people, device=None, note: str = "", now=None):
    """
    Record that a card was done, and move its task on.

    Doing a card today covers today: the next card appears on the next scheduled day
    after today, even if this card had been waiting since last week.
    """
    now = now or timezone.now()
    day = today(now)
    with transaction.atomic():
        task = Task.objects.filter(pk=task_id).first()
        if task is None or not is_waiting(task, day) or task.next_card_date != card_date:
            raise CardGone
        completion = Completion.objects.create(
            task=task,
            card_date=card_date,
            done_at=now,
            recorded_on=device,
            note=note,
            points=task.effort,
        )
        completion.done_by.set(people)
        task.next_card_date = next_after(task.rule, day)
        task.save(update_fields=["next_card_date"])
        _bring_next_task_forward(task, completion, day)
    return completion


def _bring_next_task_forward(task: Task, completion: Completion, day: date) -> None:
    """
    A chain: the task's "then show" task gets its card today, unless it already has one.

    The completion remembers what it changed, so that Undo can change it back.
    """
    follower = Task.objects.filter(pk=task.next_task_id, is_active=True).first()
    if follower is None or follower.pk == task.pk or is_waiting(follower, day):
        return
    completion.brought_forward = follower
    completion.brought_forward_from = follower.next_card_date
    completion.save(update_fields=["brought_forward", "brought_forward_from"])
    show_today(follower, day)


def undo(completion: Completion) -> None:
    """Remove a completion and put its card back, as if it had not been done."""
    with transaction.atomic():
        task = completion.task
        if task.completions.filter(card_date__gt=completion.card_date).exists():
            raise CannotUndo
        task.next_card_date = completion.card_date
        task.save(update_fields=["next_card_date"])
        _take_next_card_back(completion)
        completion.delete()


def _take_next_card_back(completion: Completion) -> None:
    """
    Undo of a chain: the card it made appear goes away again, if nobody has done it yet.

    If someone already did it, that stays done.
    """
    follower = completion.brought_forward
    if follower is None:
        return
    shown_on = today(completion.done_at)
    still_waiting = follower.next_card_date == shown_on
    done_since = follower.completions.filter(card_date=shown_on).exists()
    if still_waiting and not done_since:
        follower.next_card_date = completion.brought_forward_from
        follower.save(update_fields=["next_card_date"])


def may_undo_from(completion: Completion, device, now=None) -> bool:
    """Whether the Undo bar on this device may still undo this completion."""
    now = now or timezone.now()
    same_device = device is not None and completion.recorded_on_id == device.pk
    return same_device and now - completion.done_at <= UNDO_WINDOW


def skip(task: Task, day: date) -> None:
    """Drop the waiting card ("not needed this time"). Nothing is recorded."""
    task.next_card_date = next_after(task.rule, day)
    task.save(update_fields=["next_card_date"])


def show_today(task: Task, day: date) -> None:
    """Make the task's card appear now, ahead of its schedule."""
    task.next_card_date = day
    task.save(update_fields=["next_card_date"])
