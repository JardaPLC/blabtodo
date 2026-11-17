"""
Rounds: a card asked for several times, such as three loads of washing from one pile.

Done takes one round off; the card goes when none is left.
"""

from datetime import date, timedelta

import pytest

from tasks import cards
from tasks.models import Completion, Task
from tasks.schedule import ON_DEMAND
from tests.conftest import make_task, noon

pytestmark = pytest.mark.django_db

MON = date(2026, 11, 2)
TUE = MON + timedelta(days=1)


def waiting(day):
    return list(cards.waiting_cards(day))


def rounds_of(task) -> int:
    task.refresh_from_db()
    return task.rounds


def done(task, day, person, *, rounds=None, minutes=0):
    task.refresh_from_db()
    return cards.complete(
        task_id=task.pk,
        card_date=task.next_card_date,
        people=[person],
        rounds=rounds,
        now=noon(day) + timedelta(minutes=minutes),
    )


def washing(rounds: int, *, repeat=ON_DEMAND) -> Task:
    task = make_task("Wash", repeat=repeat, start_date=MON)
    for _ in range(rounds):
        cards.show_today(task, MON)
    return task


# ---- Asking for more ----


def test_asking_for_a_waiting_card_again_adds_a_round_and_keeps_its_place():
    task = washing(1)

    cards.show_today(task, MON)
    cards.show_today(task, MON)

    task.refresh_from_db()
    assert task.rounds == 3
    assert task.next_card_date == MON
    assert waiting(MON) == [task]


def test_a_card_that_waits_since_last_week_keeps_its_day_when_asked_for_again():
    task = make_task("Wash", start_date=MON)

    cards.show_today(task, TUE + timedelta(days=5))

    task.refresh_from_db()
    assert task.next_card_date == MON
    assert task.rounds == 2


def test_rounds_stop_at_nine():
    task = washing(12)

    assert rounds_of(task) == cards.MAX_ROUNDS == 9


# ---- Done ----


def test_done_takes_one_round_off_and_the_card_goes_with_the_last(adult):
    task = washing(3)

    done(task, MON, adult)
    assert rounds_of(task) == 2
    assert waiting(MON) == [task]

    done(task, MON, adult, minutes=1)
    done(task, MON, adult, minutes=2)
    assert waiting(MON) == []
    # Every round is a finished task of its own, for the list and for the jar.
    assert Completion.objects.filter(task=task).count() == 3


def test_a_repeating_card_moves_on_only_after_its_last_round(adult):
    task = make_task("Wash", start_date=MON)
    cards.show_today(task, MON)

    done(task, MON, adult)
    task.refresh_from_db()
    assert task.next_card_date == MON

    done(task, MON, adult, minutes=1)
    task.refresh_from_db()
    assert task.next_card_date == TUE
    assert task.rounds == 1


def test_a_second_tap_on_the_same_round_is_refused(adult, child):
    task = washing(2)
    # Both sheets showed "2 times".
    done(task, MON, adult, rounds=2)

    with pytest.raises(cards.CardGone):
        done(task, MON, child, rounds=2)
    assert rounds_of(task) == 1


# ---- Undo, skip, day-only ----


def test_undo_gives_the_round_back(adult):
    task = washing(3)
    completion = done(task, MON, adult)

    cards.undo(completion)

    assert rounds_of(task) == 3
    assert not Completion.objects.exists()


def test_undo_of_the_last_round_brings_the_card_back_with_one_round(adult):
    task = washing(2)
    done(task, MON, adult)
    last = done(task, MON, adult, minutes=1)
    assert waiting(MON) == []

    cards.undo(last)

    assert waiting(MON) == [task]
    assert rounds_of(task) == 1


def test_skip_drops_the_card_with_all_its_rounds():
    task = make_task("Wash", start_date=MON)
    cards.show_today(task, MON)

    cards.skip(task, MON)

    task.refresh_from_db()
    assert task.next_card_date == TUE
    assert task.rounds == 1


def test_a_day_only_card_nobody_did_goes_with_all_its_rounds():
    task = make_task("Bins", start_date=MON, day_only=True)
    cards.show_today(task, MON)

    assert waiting(TUE) == [task]
    assert rounds_of(task) == 1


# ---- Chains ----


def chain():
    load = make_task("Load", repeat=ON_DEMAND, start_date=MON)
    empty = make_task("Empty", repeat=ON_DEMAND, start_date=MON)
    load.next_task = empty
    load.save()
    return load, empty


def test_each_load_asks_for_one_emptying(adult):
    load, empty = chain()
    cards.show_today(load, MON)
    cards.show_today(load, MON)

    done(load, MON, adult)
    done(load, MON, adult, minutes=1)

    assert rounds_of(empty) == 2


def test_undo_of_a_load_takes_back_only_its_own_round(adult):
    load, empty = chain()
    cards.show_today(load, MON)
    cards.show_today(load, MON)
    done(load, MON, adult)
    second = done(load, MON, adult, minutes=1)

    cards.undo(second)

    assert rounds_of(empty) == 1
    assert rounds_of(load) == 1
    assert set(waiting(MON)) == {load, empty}


# ---- Screens ----


def test_a_card_with_rounds_shows_how_many(trusted_client):
    task = washing(3)
    task.next_card_date = cards.today()
    task.save()

    html = trusted_client.get("/").content.decode()

    assert "×3" in html


def test_a_card_with_one_round_shows_no_number(trusted_client):
    task = washing(1)
    task.next_card_date = cards.today()
    task.save()

    assert "×1" not in trusted_client.get("/").content.decode()


def test_the_sheet_offers_one_more_and_sends_how_many_it_showed(trusted_client):
    task = make_task("Wash")
    cards.show_today(task, cards.today())

    html = trusted_client.get(f"/cards/{task.pk}/done/").content.decode()

    assert f"/cards/{task.pk}/one-more/" in html
    assert 'name="rounds" value="2"' in html
    assert "Zbývá ještě 2×" in html


def test_one_more_from_the_sheet_adds_a_round(trusted_client):
    task = make_task("Wash")

    response = trusted_client.post(f"/cards/{task.pk}/one-more/")

    assert rounds_of(task) == 2
    assert response.headers["HX-Trigger"] == "sheet-close"
    assert "×2" in response.content.decode()


def test_one_more_for_a_card_that_is_gone_changes_nothing(trusted_client):
    task = make_task("Wash", repeat=ON_DEMAND)

    trusted_client.post(f"/cards/{task.pk}/one-more/")

    task.refresh_from_db()
    assert task.next_card_date is None


def test_done_from_a_sheet_that_showed_an_old_number_is_met_kindly(trusted_client, adult):
    task = make_task("Wash")
    cards.show_today(task, cards.today())
    form = {"card_date": task.next_card_date.isoformat(), "who": [adult.pk], "rounds": "2"}
    trusted_client.post(f"/cards/{task.pk}/done/", form)

    response = trusted_client.post(f"/cards/{task.pk}/done/", form)

    assert "Tohle už někdo udělal" in response.content.decode()
    assert Completion.objects.count() == 1


def test_the_undo_bar_says_how_many_rounds_are_left(trusted_client, adult):
    task = make_task("Wash")
    cards.show_today(task, cards.today())
    cards.show_today(task, cards.today())
    form = {"card_date": task.next_card_date.isoformat(), "who": [adult.pk], "rounds": "3"}

    html = trusted_client.post(f"/cards/{task.pk}/done/", form).content.decode()

    assert "Zbývá ještě 2×" in html


def test_scanning_the_code_of_a_waiting_card_offers_one_more_time(trusted_client):
    task = make_task("Wash")
    address = f"/t/{task.ensure_qr_key()}/"

    page = trusted_client.get(address).content.decode()
    assert "Už čeká v Dnes" in page
    assert "Ještě jednou" in page
    trusted_client.post(address)

    assert rounds_of(task) == 2
