"""The Today screen, the sheet for marking a card done, and the Undo bar."""

import re
from datetime import timedelta

import pytest

from people.devices import COOKIE_NAME, trust_device
from tasks import cards
from tasks.labels import waiting_since
from tasks.models import Completion
from tasks.schedule import WEEKLY
from tests.conftest import make_room, make_task

pytestmark = pytest.mark.django_db


def html_of(response) -> str:
    return response.content.decode()


def ticked_faces(html: str) -> int:
    """How many faces on the sheet are ticked already."""
    return len(re.findall(r'class="peer sr-only"\s+checked', html))


# ---- Today ----


def test_today_shows_the_waiting_cards_with_picture_name_and_room(trusted_client):
    make_task("Zalít květiny", picture="water-plants", room=make_room("Obývací pokoj"))
    make_task("Až zítra", start_date=cards.today() + timedelta(days=1))

    html = html_of(trusted_client.get("/"))

    assert "Zalít květiny" in html
    assert "Obývací pokoj" in html
    assert "🌱" in html
    assert "Až zítra" not in html


def test_an_older_card_says_since_when_in_neutral_words(trusted_client):
    make_task("Vysát", start_date=cards.today() - timedelta(days=1))

    html = html_of(trusted_client.get("/"))

    assert "od včerejška" in html
    assert "overdue" not in html.lower()


@pytest.mark.parametrize(
    ("days_ago", "expected"),
    [(0, ""), (1, "od včerejška"), (10, "od 2. listopadu")],
)
def test_the_since_label(days_ago, expected):
    from datetime import date

    day = date(2026, 11, 12)

    assert waiting_since(day - timedelta(days=days_ago), day) == expected


def test_the_since_label_names_the_weekday_within_a_week():
    from datetime import date

    thursday = date(2026, 11, 12)

    assert waiting_since(thursday - timedelta(days=3), thursday) == "od pondělí"
    assert waiting_since(thursday - timedelta(days=6), thursday) == "od pátku"


def test_a_card_shows_the_faces_it_is_meant_for(trusted_client, child):
    make_task("Uklidit hračky", faces=[child])

    html = html_of(trusted_client.get("/"))

    assert child.colour_classes in html


def test_tapping_a_face_shows_only_the_cards_with_that_face(trusted_client, adult, child):
    make_task("Uklidit hračky", faces=[child])
    make_task("Vyžehlit", faces=[adult])
    make_task("Vynést odpadky")  # anyone's

    html = html_of(trusted_client.get(f"/?face={child.pk}"))

    assert "Uklidit hračky" in html
    assert "Vyžehlit" not in html
    assert "Vynést odpadky" not in html
    # The 30-second refresh keeps the same choice.
    assert f'hx-get="/cards/?face={child.pk}"' in html


def test_an_empty_queue_is_a_celebration_not_a_blank_page(trusted_client):
    assert "Hotovo!" in html_of(trusted_client.get("/"))


def test_the_card_grid_alone_is_what_the_refresh_fetches(trusted_client):
    make_task("Zalít květiny")

    html = html_of(trusted_client.get("/cards/"))

    assert "Zalít květiny" in html
    assert "<html" not in html


def test_today_needs_an_allowed_device(client, adult):
    assert client.get("/").headers["Location"].startswith("/trust/")
    assert client.get("/cards/").headers["Location"].startswith("/trust/")


# ---- The sheet ----


def test_tapping_a_card_asks_who_did_it(trusted_client, adult, child):
    task = make_task("Zalít květiny", hint="Konev je na balkoně")

    html = html_of(trusted_client.get(f"/cards/{task.pk}/done/"))

    assert "Kdo to udělal?" in html
    assert "Konev je na balkoně" in html
    assert adult.display_name in html and child.display_name in html
    assert f'name="card_date" value="{cards.today().isoformat()}"' in html
    assert ticked_faces(html) == 0


def test_a_card_meant_for_one_person_has_that_face_ticked_already(trusted_client, child):
    task = make_task("Uklidit hračky", faces=[child])

    html = html_of(trusted_client.get(f"/cards/{task.pk}/done/"))

    assert ticked_faces(html) == 1
    assert "picked: 1" in html


def test_after_tapping_a_face_on_today_that_face_is_ticked_on_the_sheet(trusted_client, adult):
    task = make_task("Vynést odpadky")

    html = html_of(trusted_client.get(f"/cards/{task.pk}/done/?face={adult.pk}"))

    assert ticked_faces(html) == 1


def test_done_records_it_closes_the_sheet_and_offers_undo(trusted_client, adult, child):
    task = make_task("Zalít květiny")

    response = trusted_client.post(
        f"/cards/{task.pk}/done/",
        {"card_date": cards.today().isoformat(), "who": [adult.pk, child.pk], "note": "  hotovo  "},
    )

    completion = Completion.objects.get()
    assert set(completion.done_by.all()) == {adult, child}
    assert completion.note == "hotovo"
    assert completion.recorded_on is not None

    assert response.headers["HX-Trigger"] == "sheet-close"
    assert response.headers["HX-Retarget"] == "#cards"
    html = html_of(response)
    assert "Hotovo: Zalít květiny" in html
    assert f"/completions/{completion.pk}/undo/" in html
    assert "Hotovo!" in html  # the queue is empty now


def test_done_without_anyone_shows_the_sheet_again(trusted_client, adult):
    task = make_task("Zalít květiny")

    response = trusted_client.post(
        f"/cards/{task.pk}/done/", {"card_date": cards.today().isoformat()}
    )

    assert not Completion.objects.exists()
    assert response.headers["HX-Retarget"] == "#sheet"
    assert "Ťukněte aspoň na jednu tvář." in html_of(response)


def test_someone_who_moved_out_cannot_be_recorded_as_having_done_it(trusted_client, child):
    task = make_task("Zalít květiny")
    child.is_active = False
    child.save()

    trusted_client.post(
        f"/cards/{task.pk}/done/", {"card_date": cards.today().isoformat(), "who": [child.pk]}
    )

    assert not Completion.objects.exists()


def test_done_on_a_card_someone_else_just_finished_is_met_kindly(trusted_client, adult, child):
    task = make_task("Zalít květiny")
    cards.complete(task_id=task.pk, card_date=cards.today(), people=[adult])

    response = trusted_client.post(
        f"/cards/{task.pk}/done/", {"card_date": cards.today().isoformat(), "who": [child.pk]}
    )

    assert Completion.objects.count() == 1
    assert "Tohle už někdo udělal." in html_of(response)
    assert response.headers["HX-Trigger"] == "sheet-close"


def test_opening_the_sheet_for_a_card_that_is_gone_refreshes_the_cards_instead(
    trusted_client, adult
):
    task = make_task(repeat=WEEKLY, weekdays=[0])
    cards.skip(task, cards.today() + timedelta(days=7))

    response = trusted_client.get(f"/cards/{task.pk}/done/")

    assert response.headers["HX-Retarget"] == "#cards"
    assert "Tohle už někdo udělal." in html_of(response)


def test_a_card_date_that_makes_no_sense_changes_nothing(trusted_client, adult):
    task = make_task("Zalít květiny")

    trusted_client.post(f"/cards/{task.pk}/done/", {"card_date": "soon", "who": [adult.pk]})

    assert not Completion.objects.exists()


# ---- Undo ----


def test_undo_puts_the_card_back(trusted_client, adult):
    task = make_task("Zalít květiny")
    trusted_client.post(
        f"/cards/{task.pk}/done/", {"card_date": cards.today().isoformat(), "who": [adult.pk]}
    )
    completion = Completion.objects.get()

    response = trusted_client.post(f"/completions/{completion.pk}/undo/")

    assert not Completion.objects.exists()
    html = html_of(response)
    assert "Zalít květiny" in html
    assert "/undo/" not in html  # the bar is cleared


def test_undo_from_another_device_does_nothing(client, trusted_client, adult):
    task = make_task("Zalít květiny")
    trusted_client.post(
        f"/cards/{task.pk}/done/", {"card_date": cards.today().isoformat(), "who": [adult.pk]}
    )
    completion = Completion.objects.get()

    _device, other_token = trust_device(name="Another phone", trusted_by=adult)
    client.cookies[COOKIE_NAME] = other_token
    client.post(f"/completions/{completion.pk}/undo/")

    assert Completion.objects.filter(pk=completion.pk).exists()


def test_undo_of_something_that_is_not_there_is_harmless(trusted_client):
    assert trusted_client.post("/completions/999/undo/").status_code == 200
