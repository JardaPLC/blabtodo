"""The Today screen filtered by room, and the switch between faces and rooms."""

import pytest

from tasks import cards
from tasks.schedule import ON_DEMAND
from tests.conftest import make_room, make_task

pytestmark = pytest.mark.django_db


def html_of(response) -> str:
    assert response.status_code == 200
    return response.content.decode()


@pytest.fixture
def home(db):
    kitchen = make_room("Kuchyně", picture="kitchen")
    bathroom = make_room("Koupelna", picture="bathroom")
    make_task("Naplnit myčku", room=kitchen)
    make_task("Utřít stůl", room=kitchen)
    make_task("Umýt umyvadlo", room=bathroom)
    make_task("Nakoupit")  # no room
    return kitchen, bathroom


def test_the_row_shows_faces_until_rooms_are_chosen(trusted_client, home, adult):
    html = html_of(trusted_client.get("/"))
    assert f"?face={adult.pk}" in html
    assert "?room=" not in html

    html = html_of(trusted_client.get("/?by=rooms"))
    assert f"?face={adult.pk}" not in html
    kitchen, bathroom = home
    assert f"?room={kitchen.pk}" in html
    assert f"?room={bathroom.pk}" in html


def test_a_room_shows_only_its_own_cards(trusted_client, home):
    kitchen, _bathroom = home

    html = html_of(trusted_client.get(f"/?room={kitchen.pk}"))

    assert "Naplnit myčku" in html
    assert "Utřít stůl" in html
    assert "Umýt umyvadlo" not in html
    assert "Nakoupit" not in html


def test_elsewhere_shows_the_cards_that_belong_to_no_room(trusted_client, home):
    html = html_of(trusted_client.get("/?room=none"))

    assert "Nakoupit" in html
    assert "Naplnit myčku" not in html


def test_elsewhere_is_offered_only_when_some_task_has_no_room(trusted_client):
    make_task("Naplnit myčku", room=make_room("Kuchyně"))

    assert "?room=none" not in html_of(trusted_client.get("/?by=rooms"))


def test_each_room_button_says_how_many_cards_wait_there(trusted_client, home):
    kitchen, _bathroom = home
    on_demand = make_task("Vyklidit myčku", room=kitchen, repeat=ON_DEMAND)
    assert on_demand.next_card_date is None  # not waiting, not counted

    html = html_of(trusted_client.get("/?by=rooms"))

    # The kitchen's button: the address, then the count badge.
    kitchen_button = html[html.index(f"?room={kitchen.pk}") :]
    kitchen_button = kitchen_button[: kitchen_button.index("</a>")]
    assert ">2</span>" in kitchen_button


def test_choosing_a_room_drops_the_chosen_face_and_the_other_way_round(trusted_client, home, adult):
    kitchen, _bathroom = home
    # Each button leads to an address with just its own filter.
    html = html_of(trusted_client.get(f"/?face={adult.pk}"))
    assert 'href="/?by=rooms"' in html

    html = html_of(trusted_client.get(f"/?room={kitchen.pk}"))
    assert 'href="/"' in html
    assert "face=" not in html


def test_the_room_filter_is_kept_by_the_refresh_the_sheet_done_and_undo(
    trusted_client, home, adult
):
    kitchen, _bathroom = home
    task = kitchen.tasks.get(names__cs="Naplnit myčku")

    html = html_of(trusted_client.get(f"/?room={kitchen.pk}"))
    assert f'hx-get="/cards/?room={kitchen.pk}"' in html
    assert f"/cards/{task.pk}/done/?room={kitchen.pk}" in html

    sheet = html_of(trusted_client.get(f"/cards/{task.pk}/done/?room={kitchen.pk}"))
    assert f'hx-post="/cards/{task.pk}/done/?room={kitchen.pk}"' in sheet

    after = html_of(
        trusted_client.post(
            f"/cards/{task.pk}/done/?room={kitchen.pk}",
            {"card_date": task.next_card_date.isoformat(), "who": [adult.pk], "rounds": "1"},
        )
    )
    # Still only the kitchen, and Undo comes back to the kitchen too.
    assert "Utřít stůl" in after
    assert "Umýt umyvadlo" not in after
    assert f"/undo/?room={kitchen.pk}" in after


def test_the_room_name_is_left_off_cards_when_looking_at_that_room(trusted_client, home):
    kitchen, _bathroom = home

    grid = html_of(trusted_client.get(f"/cards/?room={kitchen.pk}"))

    assert "Kuchyně" not in grid


def test_an_empty_room_says_so(trusted_client, home):
    _kitchen, bathroom = home
    sink = bathroom.tasks.get()
    cards.skip(sink, cards.today())

    html = html_of(trusted_client.get(f"/?room={bathroom.pk}"))

    assert "V této místnosti teď nic nečeká." in html


@pytest.mark.parametrize("room", ["999", "abc", ""])
def test_an_unknown_room_shows_everything(trusted_client, home, room):
    html = html_of(trusted_client.get(f"/?room={room}"))

    assert "Naplnit myčku" in html
    assert "Umýt umyvadlo" in html


def test_a_room_that_is_not_in_use_is_not_offered(trusted_client, home):
    _kitchen, bathroom = home
    bathroom.is_active = False
    bathroom.save()

    assert f"?room={bathroom.pk}" not in html_of(trusted_client.get("/?by=rooms"))
