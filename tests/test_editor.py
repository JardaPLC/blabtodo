"""The adult view: editing tasks and rooms in the app after an adult's PIN."""

from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

from people.adults import UNLOCKED_FOR
from tasks import cards
from tasks.labels import repeat_summary
from tasks.models import Completion, Room, Task
from tasks.schedule import DAYS, MONTHLY, ON_DEMAND, WEEKLY
from tests.conftest import ADULT_PIN, make_room, make_task

pytestmark = pytest.mark.django_db


def html_of(response) -> str:
    assert response.status_code == 200, response.status_code
    return response.content.decode()


@pytest.fixture
def editor(trusted_client):
    """A browser on an allowed device, with the adult view unlocked by Mum's PIN."""
    response = trusted_client.post("/manage/unlock/", {"pin": ADULT_PIN, "next": "/manage/"})
    assert response.headers["Location"] == "/manage/"
    return trusted_client


def task_form(**changed) -> dict:
    """What the task editor sends for a new daily task, with some fields changed."""
    today = cards.today().isoformat()
    form = {
        "picture": "",
        "names_cs": "",
        "names_en": "",
        "hint": "",
        "room": "",
        "effort": "1",
        "repeat": DAYS,
        "interval": "1",
        "day_of_month": "",
        "start_date": today,
        "initial-start_date": today,
        "end_date": "",
        "next_task": "",
        "is_active": "on",
    }
    form.update(changed)
    return {key: value for key, value in form.items() if value is not None}


def form_of(task: Task, **changed) -> dict:
    """What the task editor sends for an existing task, with some fields changed."""
    task.refresh_from_db()
    form = task_form(
        picture=task.picture,
        names_cs=task.names.get("cs", ""),
        names_en=task.names.get("en", ""),
        hint=task.hint,
        room=task.room_id or "",
        effort=str(task.effort),
        repeat=task.repeat,
        interval=str(task.interval),
        day_of_month=task.day_of_month or "",
        start_date=task.start_date.isoformat(),
        **{"initial-start_date": task.start_date.isoformat()},
        end_date=task.end_date.isoformat() if task.end_date else "",
        next_task=task.next_task_id or "",
        weekdays=[str(day) for day in task.weekdays],
        faces=[str(person.pk) for person in task.faces.all()],
        is_active="on" if task.is_active else None,
        day_only="on" if task.day_only else None,
    )
    form.update(changed)
    return {key: value for key, value in form.items() if value is not None}


# ---- The way in ----


def test_the_adult_view_asks_for_a_pin_first(trusted_client):
    response = trusted_client.get("/manage/tasks/")

    assert response.headers["Location"] == "/manage/unlock/?next=%2Fmanage%2Ftasks%2F"


def test_a_device_that_is_not_allowed_is_asked_to_be_allowed_first(client, adult):
    response = client.get("/manage/")

    assert response.headers["Location"].startswith("/trust/")


def test_a_wrong_pin_does_not_unlock(trusted_client):
    html = html_of(trusted_client.post("/manage/unlock/", {"pin": "0000"}))

    assert "Špatný PIN" in html
    assert trusted_client.get("/manage/").status_code == 302


def test_the_right_pin_unlocks_and_goes_where_it_was_asked_to(trusted_client):
    response = trusted_client.post("/manage/unlock/", {"pin": ADULT_PIN, "next": "/manage/rooms/"})

    assert response.headers["Location"] == "/manage/rooms/"
    assert "Mum" in html_of(trusted_client.get("/manage/"))


def test_it_locks_after_half_an_hour_without_use(editor):
    later = timezone.now() + UNLOCKED_FOR + timedelta(minutes=1)
    with mock.patch("django.utils.timezone.now", return_value=later):
        response = editor.get("/manage/")

    assert response.status_code == 302


def test_using_it_keeps_it_unlocked(editor):
    almost = timezone.now() + UNLOCKED_FOR - timedelta(minutes=1)
    with mock.patch("django.utils.timezone.now", return_value=almost):
        assert editor.get("/manage/").status_code == 200
    # Another 29 minutes after that last use is still inside the half hour.
    later = almost + UNLOCKED_FOR - timedelta(minutes=1)
    with mock.patch("django.utils.timezone.now", return_value=later):
        assert editor.get("/manage/").status_code == 200


def test_finish_locks_at_once(editor):
    response = editor.post("/manage/finish/")

    assert response.headers["Location"] == "/"
    assert editor.get("/manage/").status_code == 302


def test_today_leads_to_the_adult_view(trusted_client):
    assert 'href="/manage/"' in html_of(trusted_client.get("/"))


# ---- The list of tasks ----


def test_tasks_are_listed_by_room_with_how_often_they_come(editor):
    kitchen = make_room("Kuchyně")
    make_task("Naplnit myčku", room=kitchen)
    make_task("Nakoupit", repeat=WEEKLY, weekdays=[0, 3])
    make_task("Stará věc", is_active=False)

    html = html_of(editor.get("/manage/tasks/"))

    assert html.index("Kuchyně") < html.index("Naplnit myčku") < html.index("Jinde")
    assert html.index("Jinde") < html.index("Nakoupit")
    assert "Každý den" in html
    assert "Po, Čt" in html
    assert html.index("Nepoužívané") < html.index("Stará věc")


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({"repeat": DAYS, "interval": 1}, "Každý den"),
        ({"repeat": DAYS, "interval": 2}, "Každé 2 dny"),
        ({"repeat": DAYS, "interval": 7}, "Každých 7 dní"),
        ({"repeat": WEEKLY, "weekdays": [1], "interval": 2}, "Út, každý 2. týden"),
        ({"repeat": MONTHLY, "day_of_month": 1}, "Každý měsíc, 1. dne"),
        ({"repeat": MONTHLY, "day_of_month": 31, "interval": 3}, "Každé 3 měsíce, poslední den"),
        ({"repeat": ON_DEMAND}, "Na vyžádání"),
    ],
)
def test_how_often_a_task_comes_in_a_few_words(fields, expected):
    assert repeat_summary(Task(**fields)) == expected


# ---- Adding a task ----


def test_a_new_task_starts_from_the_catalogue(editor):
    html = html_of(editor.get("/manage/tasks/new/"))

    assert "?picture=water-plants" in html
    assert "Zalít květiny" in html
    assert "?picture=own" in html


def test_a_picture_from_the_catalogue_brings_its_room_and_effort(editor):
    kitchen = make_room("Kuchyně", picture="kitchen")

    html = html_of(editor.get("/manage/tasks/new/?picture=cook"))

    assert 'value="cook"' in html
    assert f'name="room" value="{kitchen.pk}" class="peer sr-only" checked' in html
    assert 'name="effort" value="3" class="peer sr-only" checked' in html
    # The picture's name is offered as the placeholder of the name box.
    assert "Uvařit" in html


def test_saving_a_new_task_plans_its_first_card(editor):
    response = editor.post("/manage/tasks/new/", task_form(picture="water-plants"))

    assert response.headers["Location"] == "/manage/tasks/"
    task = Task.objects.get()
    assert task.names == {"cs": "Zalít květiny", "en": "Water the plants"}
    assert task.next_card_date == cards.today()
    assert "Uloženo: Zalít květiny" in html_of(editor.get("/manage/tasks/"))


def test_a_task_of_your_own_needs_a_name(editor):
    html = html_of(editor.post("/manage/tasks/new/", task_form(picture="")))

    assert "Napište název" in html
    assert not Task.objects.exists()


def test_a_weekly_task_needs_its_days(editor, adult):
    html = html_of(
        editor.post(
            "/manage/tasks/new/",
            task_form(names_cs="Vysát", repeat=WEEKLY, faces=[str(adult.pk)]),
        )
    )

    assert "Vyberte aspoň jeden den v týdnu." in html
    # What was filled in stays filled in.
    assert f'value="{adult.pk}" class="peer sr-only" checked' in html


def test_a_new_weekly_task_gets_its_days_faces_and_room(editor, adult):
    kitchen = make_room("Kuchyně")

    editor.post(
        "/manage/tasks/new/",
        task_form(
            names_cs="Vytřít",
            repeat=WEEKLY,
            weekdays=["2", "5"],
            faces=[str(adult.pk)],
            room=str(kitchen.pk),
            effort="2",
        ),
    )

    task = Task.objects.get()
    assert task.weekdays == [2, 5]
    assert list(task.faces.all()) == [adult]
    assert task.room == kitchen
    assert task.effort == 2


# ---- Changing a task ----


def test_changing_when_a_task_repeats_replans_its_card(editor):
    task = make_task("Vysát", repeat=ON_DEMAND)
    assert task.next_card_date is None

    editor.post(f"/manage/tasks/{task.pk}/", form_of(task, repeat=DAYS))

    task.refresh_from_db()
    assert task.next_card_date == cards.today()


def test_a_chain_is_set_in_the_editor_and_refused_in_a_circle(editor):
    load = make_task("Naplnit myčku")
    empty = make_task("Vyklidit myčku", repeat=ON_DEMAND)

    editor.post(f"/manage/tasks/{load.pk}/", form_of(load, next_task=str(empty.pk)))
    load.refresh_from_db()
    assert load.next_task == empty

    html = html_of(
        editor.post(f"/manage/tasks/{empty.pk}/", form_of(empty, next_task=str(load.pk)))
    )
    assert "kruh" in html


def test_switching_a_task_off_keeps_it_and_it_can_be_switched_on_again(editor):
    task = make_task("Vysát")

    editor.post(f"/manage/tasks/{task.pk}/", form_of(task, is_active=None))
    task.refresh_from_db()
    assert not task.is_active

    editor.post(f"/manage/tasks/{task.pk}/", form_of(task, is_active="on"))
    task.refresh_from_db()
    assert task.is_active
    assert task.next_card_date == cards.today()


def test_show_today_and_one_more_and_skip(editor):
    task = make_task("Vyprat", repeat=ON_DEMAND)

    editor.post(f"/manage/tasks/{task.pk}/show/")
    task.refresh_from_db()
    assert task.next_card_date == cards.today()

    editor.post(f"/manage/tasks/{task.pk}/show/")
    assert "×2" in html_of(editor.get(f"/manage/tasks/{task.pk}/"))

    editor.post(f"/manage/tasks/{task.pk}/skip/")
    task.refresh_from_db()
    assert task.next_card_date is None
    assert task.rounds == 1


def test_a_task_never_done_can_be_deleted(editor):
    task = make_task("Překlep")
    assert "Smazat úkol" in html_of(editor.get(f"/manage/tasks/{task.pk}/"))

    editor.post(f"/manage/tasks/{task.pk}/delete/")

    assert not Task.objects.exists()


def test_a_task_that_was_done_cannot_be_deleted(editor, adult):
    task = make_task("Vysát")
    cards.complete(task_id=task.pk, card_date=task.next_card_date, people=[adult])
    assert "Smazat úkol" not in html_of(editor.get(f"/manage/tasks/{task.pk}/"))

    editor.post(f"/manage/tasks/{task.pk}/delete/")

    assert Task.objects.filter(pk=task.pk).exists()
    assert Completion.objects.count() == 1


def test_a_sticker_can_be_printed_for_one_task(editor):
    task = make_task("Vyměnit filtr")

    html = html_of(editor.get(f"/manage/tasks/{task.pk}/sticker/"))

    assert "<svg" in html
    assert f'href="/manage/tasks/{task.pk}/"' in html


# ---- Rooms ----


def test_a_new_room_comes_from_the_catalogue_without_the_rooms_already_there(editor):
    make_room("Kuchyně", picture="kitchen")

    html = html_of(editor.get("/manage/rooms/new/"))

    assert "?picture=kitchen" not in html
    assert "?picture=bathroom" in html


def test_a_new_room_goes_to_the_end_of_the_list(editor):
    make_room("Kuchyně", position=5)

    editor.post(
        "/manage/rooms/new/",
        {"picture": "bathroom", "names_cs": "", "names_en": "", "is_active": "on"},
    )

    room = Room.objects.get(picture="bathroom")
    assert room.name == "Koupelna"
    assert room.position == 6


def test_rooms_are_moved_up_and_down(editor):
    first, second, third = (make_room(name, position=n) for n, name in enumerate("ABC"))

    editor.post(f"/manage/rooms/{third.pk}/move/up/")
    assert list(Room.objects.all()) == [first, third, second]

    editor.post(f"/manage/rooms/{first.pk}/move/down/")
    assert list(Room.objects.all()) == [third, first, second]

    # Past the ends nothing moves.
    editor.post(f"/manage/rooms/{third.pk}/move/up/")
    assert list(Room.objects.all()) == [third, first, second]


def test_deleting_a_room_keeps_its_tasks(editor):
    kitchen = make_room("Kuchyně")
    task = make_task("Naplnit myčku", room=kitchen)

    editor.post(f"/manage/rooms/{kitchen.pk}/delete/")

    task.refresh_from_db()
    assert task.room is None
    assert not Room.objects.exists()
