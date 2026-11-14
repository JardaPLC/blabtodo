"""
Chains: a task's "then show" task gets its card when the task is done.

For example "Load the dishwasher", then "Empty the dishwasher".
"""

from datetime import date, timedelta

import pytest

from tasks import cards
from tasks.models import Completion
from tasks.schedule import DAYS, ON_DEMAND, ONCE, WEEKLY
from tests.conftest import make_task, noon
from tests.test_task_management import _change_task

pytestmark = pytest.mark.django_db

MON = date(2026, 11, 2)
TUE, WED = MON + timedelta(days=1), MON + timedelta(days=2)


def waiting(day):
    return list(cards.waiting_cards(day))


def chain(*names):
    """Tasks linked one after another. The first is daily, the rest only when asked for."""
    tasks = [make_task(names[0], start_date=MON)]
    tasks += [make_task(name, repeat=ON_DEMAND, start_date=MON) for name in names[1:]]
    for task, follower in zip(tasks, tasks[1:], strict=False):
        task.next_task = follower
        task.save()
    return tasks


def done(task, day, person, *, now=None):
    task.refresh_from_db()
    return cards.complete(
        task_id=task.pk, card_date=task.next_card_date, people=[person], now=now or noon(day)
    )


# ---- Doing a task shows the next one ----


def test_doing_a_task_shows_the_next_one_today(adult):
    load, empty = chain("Load the dishwasher", "Empty the dishwasher")

    assert waiting(MON) == [load]
    done(load, MON, adult)

    assert waiting(MON) == [empty]
    empty.refresh_from_db()
    assert empty.next_card_date == MON


def test_a_whole_chain_is_walked_one_step_at_a_time(adult):
    wash, hang, fold, put_away = chain("Wash", "Hang up", "Fold", "Put away")

    for step, follower in [(wash, hang), (hang, fold), (fold, put_away)]:
        done(step, MON, adult)
        # Only the next step appears, never the whole chain at once.
        assert follower in waiting(MON)
        assert step not in waiting(MON)
    done(put_away, MON, adult)

    # The last step leads nowhere, and the daily first step comes back tomorrow.
    assert waiting(MON) == []
    assert waiting(TUE) == [wash]


def test_the_next_card_goes_to_the_end_of_the_queue(adult):
    older = make_task("Waiting since Monday", start_date=MON)
    load, empty = chain("Load", "Empty")
    load.next_card_date = TUE
    load.save()

    done(load, TUE, adult)

    assert waiting(TUE) == [older, empty]


def test_a_card_that_already_waits_is_not_doubled_or_moved(adult):
    load, empty = chain("Load", "Empty")
    cards.show_today(empty, MON)
    done(load, MON, adult)

    empty.refresh_from_db()
    assert waiting(MON) == [empty]
    assert Completion.objects.get().brought_forward is None


def test_a_repeating_next_task_has_its_card_brought_forward(adult):
    load = make_task("Load", start_date=MON)
    weekly = make_task("Wipe the fronts", repeat=WEEKLY, weekdays=[4], start_date=MON)
    load.next_task = weekly
    load.save()

    done(load, MON, adult)

    assert weekly in waiting(MON)


def test_a_next_task_that_is_switched_off_does_not_appear(adult):
    load, empty = chain("Load", "Empty")
    empty.is_active = False
    empty.save()

    done(load, MON, adult)

    assert waiting(MON) == []


def test_skipping_a_card_does_not_start_the_chain():
    load, empty = chain("Load", "Empty")

    cards.skip(load, MON)

    empty.refresh_from_db()
    assert empty.next_card_date is None


def test_a_deleted_next_task_simply_ends_the_chain(adult):
    load, empty = chain("Load", "Empty")
    empty.delete()

    done(load, MON, adult)

    load.refresh_from_db()
    assert load.next_task is None


# ---- Undo ----


def test_undo_takes_the_next_card_away_again(adult):
    load, empty = chain("Load", "Empty")
    completion = done(load, MON, adult)

    cards.undo(completion)

    assert waiting(MON) == [load]
    empty.refresh_from_db()
    assert empty.next_card_date is None


def test_undo_puts_a_repeating_next_task_back_on_its_own_day(adult):
    load = make_task("Load", start_date=MON)
    weekly = make_task("Wipe the fronts", repeat=WEEKLY, weekdays=[4], start_date=MON)
    load.next_task = weekly
    load.save()
    friday = weekly.next_card_date

    cards.undo(done(load, MON, adult))

    weekly.refresh_from_db()
    assert weekly.next_card_date == friday


def test_undo_leaves_a_next_card_that_someone_already_did(adult):
    load, empty = chain("Load", "Empty")
    first = done(load, MON, adult)
    done(empty, MON, adult)

    cards.undo(first)

    assert waiting(MON) == [load]
    assert Completion.objects.filter(task=empty).exists()


# ---- Setting it up ----


@pytest.mark.parametrize("repeat", [ON_DEMAND, DAYS, WEEKLY])
def test_a_task_in_use_that_repeats_or_waits_to_be_asked_for_can_come_next(owner_client, repeat):
    load = make_task("Load")
    follower = make_task("Empty", repeat=repeat, weekdays=[0])

    _change_task(owner_client, load, next_task=follower.pk)

    assert load.next_task == follower


def test_a_one_time_task_cannot_come_next(owner_client):
    load = make_task("Load")
    once = make_task("Once", repeat=ONCE)

    response = _change_task(owner_client, load, next_task=once.pk)

    assert response.status_code == 200
    assert load.next_task is None


def test_a_task_cannot_come_after_itself(owner_client):
    load = make_task("Load")

    response = _change_task(owner_client, load, next_task=load.pk)

    assert response.status_code == 200
    assert load.next_task is None


def test_a_chain_cannot_go_round_in_a_circle(owner_client):
    load, empty = chain("Load", "Empty")

    response = _change_task(owner_client, empty, next_task=load.pk)

    assert response.status_code == 200
    assert "kruh" in response.content.decode()
    assert empty.next_task is None


def test_a_task_that_comes_next_cannot_become_a_one_time_task(owner_client):
    _load, empty = chain("Load", "Empty")

    response = _change_task(owner_client, empty, repeat=ONCE)

    assert response.status_code == 200
    empty.refresh_from_db()
    assert empty.repeat == ON_DEMAND


def test_the_editor_says_what_a_task_comes_after(owner_client):
    load, empty = chain("Load the dishwasher", "Empty the dishwasher")

    page = owner_client.get(f"/admin/tasks/task/{empty.pk}/change/").content.decode()

    assert "Load the dishwasher" in page


def test_the_undo_bar_says_what_comes_next(trusted_client, adult):
    load, _empty = chain("Load the dishwasher", "Empty the dishwasher")
    load.next_card_date = cards.today()
    load.save()

    response = trusted_client.post(
        f"/cards/{load.pk}/done/",
        {"card_date": load.next_card_date.isoformat(), "who": [adult.pk]},
    )

    html = response.content.decode()
    assert "Empty the dishwasher" in html


# ---- Twice a day ----


def test_a_chain_can_run_twice_in_one_day(adult):
    load, empty = chain("Load", "Empty")
    morning, evening = noon(MON), noon(MON) + timedelta(hours=8)
    load.repeat = ON_DEMAND
    load.save()
    cards.show_today(load, MON)

    done(load, MON, adult, now=morning)
    done(empty, MON, adult, now=morning + timedelta(hours=2))
    cards.show_today(load, MON)
    done(load, MON, adult, now=evening)

    assert waiting(MON) == [empty]
    done(empty, MON, adult, now=evening + timedelta(hours=2))
    assert Completion.objects.filter(task=empty).count() == 2


def test_undo_in_the_evening_takes_back_the_evenings_next_card(adult):
    load, empty = chain("Load", "Empty")
    load.repeat = ON_DEMAND
    load.save()
    cards.show_today(load, MON)
    done(load, MON, adult, now=noon(MON))
    done(empty, MON, adult, now=noon(MON) + timedelta(hours=2))
    cards.show_today(load, MON)
    evening = done(load, MON, adult, now=noon(MON) + timedelta(hours=8))

    # Empty was done this morning, but this evening's Empty card was not done yet.
    cards.undo(evening)

    assert waiting(MON) == [load]
