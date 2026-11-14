"""
Cards: which tasks are waiting, and what done, undo and skip do to a task's next card.

These are the rules of docs/design.md, section 5, one test per rule.
"""

from datetime import UTC, date, datetime, timedelta

import pytest

from people.devices import trust_device
from tasks import cards
from tasks.models import Completion
from tasks.schedule import MONTHLY, ON_DEMAND, ONCE, WEEKLY
from tests.conftest import make_task, noon

pytestmark = pytest.mark.django_db

# 2 November 2026 is a Monday.
MON = date(2026, 11, 2)
TUE, WED, THU, FRI, SAT, SUN = (MON + timedelta(days=n) for n in range(1, 7))
NEXT_MON, NEXT_TUE, NEXT_WED = (MON + timedelta(days=n) for n in range(7, 10))


def waiting(day):
    return list(cards.waiting_cards(day))


# ---- Which cards are waiting ----


def test_a_card_appears_on_its_day_and_not_before():
    task = make_task(start_date=WED)

    assert waiting(TUE) == []
    assert waiting(WED) == [task]


def test_a_card_waits_until_someone_does_it_and_there_is_only_ever_one():
    task = make_task(start_date=MON)

    # Nobody did it for three days: still one card, still Monday's.
    assert waiting(THU) == [task]
    assert waiting(THU)[0].next_card_date == MON
    assert not Completion.objects.exists()


def test_the_oldest_card_comes_first():
    newest = make_task("Newest", start_date=WED)
    oldest = make_task("Oldest", start_date=MON)
    middle = make_task("Middle", start_date=TUE)

    assert waiting(WED) == [oldest, middle, newest]


def test_cards_of_the_same_day_keep_the_order_the_tasks_were_made_in():
    first = make_task("First", start_date=MON)
    second = make_task("Second", start_date=MON)

    assert waiting(MON) == [first, second]


def test_a_task_that_is_switched_off_has_no_card():
    make_task(start_date=MON, is_active=False)

    assert waiting(MON) == []


def test_today_follows_the_household_clock_not_the_servers():
    # Half past eleven at night in UTC is already tomorrow in the Czech time zone.
    late_evening_utc = datetime(2026, 11, 10, 23, 30, tzinfo=UTC)

    assert cards.today(late_evening_utc) == date(2026, 11, 11)


# ---- Done ----


def test_done_records_who_when_where_and_how_much(adult, child):
    task = make_task(start_date=MON, effort=3)
    device, _token = trust_device(name="Kitchen panel", trusted_by=adult)

    completion = cards.complete(
        task_id=task.pk,
        card_date=MON,
        people=[adult, child],
        device=device,
        note="with the new can",
        now=noon(MON),
    )

    assert completion.task == task
    assert completion.card_date == MON
    assert completion.done_at == noon(MON)
    assert set(completion.done_by.all()) == {adult, child}
    assert completion.recorded_on == device
    assert completion.note == "with the new can"
    # Done together still counts once: the task fills the jar, not the people.
    assert completion.points == 3


def test_a_daily_card_done_today_comes_back_tomorrow(adult):
    task = make_task(start_date=MON)

    cards.complete(task_id=task.pk, card_date=MON, people=[adult], now=noon(MON))

    assert waiting(MON) == []
    assert waiting(TUE) == [task]
    assert waiting(TUE)[0].next_card_date == TUE


def test_doing_an_old_card_today_covers_today(adult):
    task = make_task(start_date=MON)

    # Monday's card is finally done on Thursday. There is no second card for Thursday.
    cards.complete(task_id=task.pk, card_date=MON, people=[adult], now=noon(THU))

    assert waiting(THU) == []
    assert waiting(FRI)[0].next_card_date == FRI
    assert Completion.objects.count() == 1


def test_a_weekly_card_done_late_still_meets_the_next_scheduled_day(adult):
    task = make_task("Vacuum", repeat=WEEKLY, weekdays=[2, 5], start_date=MON)
    assert task.next_card_date == WED

    cards.complete(task_id=task.pk, card_date=WED, people=[adult], now=noon(FRI))

    task.refresh_from_db()
    assert task.next_card_date == SAT


def test_one_doing_on_the_next_scheduled_day_covers_both_cards(adult):
    task = make_task("Vacuum", repeat=WEEKLY, weekdays=[2, 5], start_date=MON)

    # Wednesday's card is done on Saturday, which is itself a scheduled day.
    cards.complete(task_id=task.pk, card_date=WED, people=[adult], now=noon(SAT))

    task.refresh_from_db()
    assert task.next_card_date == NEXT_WED


def test_a_one_time_task_leaves_the_queue_for_good(adult):
    task = make_task("Take the parcel", repeat=ONCE, start_date=TUE)

    cards.complete(task_id=task.pk, card_date=TUE, people=[adult], now=noon(WED))

    task.refresh_from_db()
    assert task.next_card_date is None
    assert waiting(WED) == [] and waiting(NEXT_WED) == []


def test_a_monthly_card_done_moves_to_next_month(adult):
    task = make_task(
        "Clean the fridge", repeat=MONTHLY, day_of_month=1, start_date=date(2026, 11, 1)
    )

    cards.complete(task_id=task.pk, card_date=date(2026, 11, 1), people=[adult], now=noon(MON))

    task.refresh_from_db()
    assert task.next_card_date == date(2026, 12, 1)


def test_points_are_what_the_task_was_worth_when_it_was_done(adult):
    task = make_task(start_date=MON, effort=1)
    completion = cards.complete(task_id=task.pk, card_date=MON, people=[adult], now=noon(MON))

    task.effort = 3
    task.save()

    completion.refresh_from_db()
    assert completion.points == 1


# ---- Two people, one card ----


def test_the_same_card_cannot_be_done_twice(adult, child):
    task = make_task(start_date=MON)
    cards.complete(task_id=task.pk, card_date=MON, people=[adult], now=noon(MON))

    # A second device still shows Monday's card and sends Done a moment later.
    with pytest.raises(cards.CardGone):
        cards.complete(task_id=task.pk, card_date=MON, people=[child], now=noon(MON))

    assert Completion.objects.count() == 1


@pytest.mark.parametrize(
    ("change", "sent_date"),
    [
        ({"is_active": False}, MON),  # the task was switched off meanwhile
        ({}, TUE),  # the page showed a card that is not the waiting one
        ({"next_card_date": NEXT_MON}, NEXT_MON),  # the card is not due yet
    ],
)
def test_done_is_refused_when_the_card_is_not_the_one_waiting(adult, change, sent_date):
    task = make_task(start_date=MON)
    for field, value in change.items():
        setattr(task, field, value)
    task.save()

    with pytest.raises(cards.CardGone):
        cards.complete(task_id=task.pk, card_date=sent_date, people=[adult], now=noon(MON))


def test_done_for_a_task_that_does_not_exist_is_refused(adult):
    with pytest.raises(cards.CardGone):
        cards.complete(task_id=999, card_date=MON, people=[adult], now=noon(MON))


# ---- Only makes sense on the day ----


def test_a_day_only_card_disappears_at_the_end_of_its_day_without_a_trace():
    task = make_task("Put the bins out", repeat=WEEKLY, weekdays=[1], start_date=MON, day_only=True)
    assert waiting(TUE) == [task]

    assert waiting(WED) == []
    task.refresh_from_db()
    assert task.next_card_date == NEXT_TUE
    assert not Completion.objects.exists()


def test_a_daily_day_only_card_is_replaced_by_todays():
    task = make_task(start_date=MON, day_only=True)

    assert waiting(WED) == [task]
    assert waiting(WED)[0].next_card_date == WED


def test_a_day_only_card_can_be_done_on_its_day(adult):
    task = make_task(repeat=WEEKLY, weekdays=[1], start_date=MON, day_only=True)

    cards.complete(task_id=task.pk, card_date=TUE, people=[adult], now=noon(TUE))

    task.refresh_from_db()
    assert task.next_card_date == NEXT_TUE


# ---- Undo, skip, show today ----


def test_undo_puts_the_card_back_as_if_nothing_had_happened(adult):
    task = make_task(start_date=MON)
    completion = cards.complete(task_id=task.pk, card_date=MON, people=[adult], now=noon(WED))

    cards.undo(completion)

    assert not Completion.objects.exists()
    assert waiting(WED)[0].next_card_date == MON


def test_only_the_latest_completion_of_a_task_can_be_undone(adult):
    task = make_task(start_date=MON)
    first = cards.complete(task_id=task.pk, card_date=MON, people=[adult], now=noon(MON))
    cards.complete(task_id=task.pk, card_date=TUE, people=[adult], now=noon(TUE))

    with pytest.raises(cards.CannotUndo):
        cards.undo(first)

    assert Completion.objects.count() == 2


def test_the_undo_bar_works_briefly_and_only_on_the_device_that_recorded_it(adult):
    here, _token = trust_device(name="Kitchen panel", trusted_by=adult)
    elsewhere, _token = trust_device(name="A phone", trusted_by=adult)
    task = make_task(start_date=MON)
    completion = cards.complete(
        task_id=task.pk, card_date=MON, people=[adult], device=here, now=noon(MON)
    )
    soon, too_late = noon(MON) + timedelta(seconds=20), noon(MON) + timedelta(minutes=5)

    assert cards.may_undo_from(completion, here, now=soon)
    assert not cards.may_undo_from(completion, elsewhere, now=soon)
    assert not cards.may_undo_from(completion, here, now=too_late)
    assert not cards.may_undo_from(completion, None, now=soon)


def test_skip_moves_the_task_on_and_records_nothing():
    task = make_task(start_date=MON)

    cards.skip(task, WED)

    assert waiting(WED) == []
    assert waiting(THU)[0].next_card_date == THU
    assert not Completion.objects.exists()


def test_show_today_brings_a_card_forward():
    task = make_task(repeat=WEEKLY, weekdays=[5], start_date=MON)
    assert waiting(TUE) == []

    cards.show_today(task, TUE)

    assert waiting(TUE) == [task]


# ---- Changing a task ----


def test_changing_the_repeat_settings_leaves_a_waiting_card_alone():
    task = make_task(start_date=MON)
    task.repeat, task.weekdays = WEEKLY, [5]

    cards.replan_after_edit(task, WED)

    assert task.next_card_date == MON


def test_changing_the_repeat_settings_replans_a_task_that_is_not_waiting():
    task = make_task("Vacuum", repeat=WEEKLY, weekdays=[5], start_date=MON)
    assert task.next_card_date == SAT
    task.weekdays = [3]

    cards.replan_after_edit(task, TUE)

    assert task.next_card_date == THU


def test_a_task_switched_on_again_starts_afresh():
    task = make_task(start_date=MON, is_active=False)
    task.is_active = True

    cards.plan_from(task, NEXT_WED)

    # Not "since Monday of last week": it was off, so nothing was waiting.
    assert task.next_card_date == NEXT_WED


def test_a_task_done_today_is_not_brought_back_today_by_an_edit(adult):
    task = make_task(repeat=WEEKLY, weekdays=[0], start_date=MON)
    cards.complete(task_id=task.pk, card_date=MON, people=[adult], now=noon(MON))
    task.refresh_from_db()
    task.weekdays = [0, 3]

    cards.replan_after_edit(task, MON)

    # Monday is a scheduled day, but Monday is already done.
    assert task.next_card_date == THU


# ---- A task asked for more than once a day ----


def test_a_task_asked_for_again_the_same_day_can_be_done_again(adult):
    # Its QR code is scanned in the morning and again in the evening.
    task = make_task("Change the filter", repeat=ON_DEMAND, start_date=MON)
    cards.show_today(task, MON)
    cards.complete(task_id=task.pk, card_date=MON, people=[adult], now=noon(MON))
    cards.show_today(task, MON)

    evening = noon(MON) + timedelta(hours=6)
    cards.complete(task_id=task.pk, card_date=MON, people=[adult], now=evening)

    assert Completion.objects.filter(task=task, card_date=MON).count() == 2
    assert waiting(MON) == []


def test_undo_of_the_second_time_the_same_day_puts_that_card_back(adult):
    task = make_task("Change the filter", repeat=ON_DEMAND, start_date=MON)
    cards.show_today(task, MON)
    first = cards.complete(task_id=task.pk, card_date=MON, people=[adult], now=noon(MON))
    cards.show_today(task, MON)
    second = cards.complete(
        task_id=task.pk, card_date=MON, people=[adult], now=noon(MON) + timedelta(hours=6)
    )

    with pytest.raises(cards.CannotUndo):
        cards.undo(first)
    cards.undo(second)

    assert waiting(MON) == [task]
    assert list(Completion.objects.all()) == [first]
