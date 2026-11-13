"""The management pages (Django admin) for tasks, rooms and finished tasks."""

from datetime import timedelta

import pytest

from tasks import cards
from tasks.models import Completion, Room, Task
from tests.conftest import make_room, make_task

pytestmark = pytest.mark.django_db

TODAY = cards.today


@pytest.fixture
def owner_client(client, adult):
    adult.is_staff = adult.is_superuser = True
    adult.save()
    client.force_login(adult)
    return client


def _empty_task_form() -> dict:
    """The form for adding a task, as the page shows it before anything is filled in."""
    return {
        "picture": "",
        "names_cs": "",
        "names_en": "",
        "hint": "",
        "room": "",
        "effort": "1",
        "repeat": "days",
        "interval": "1",
        "day_of_month": "",
        "start_date": TODAY().isoformat(),
        # The page sends what it showed for the start, so that "unchanged" can be told.
        "initial-start_date": TODAY().isoformat(),
        "end_date": "",
        "is_active": "on",
        "next_card_date": "",
    }


def _form_showing(task: Task) -> dict:
    """The form for changing a task, as the page shows it for the task as it is now."""
    form = _empty_task_form() | {
        "picture": task.picture,
        "names_cs": task.names.get("cs", ""),
        "names_en": task.names.get("en", ""),
        "hint": task.hint,
        "room": task.room_id or "",
        "effort": str(task.effort),
        "repeat": task.repeat,
        "interval": str(task.interval),
        "day_of_month": task.day_of_month or "",
        "start_date": task.start_date.isoformat(),
        "initial-start_date": task.start_date.isoformat(),
        "end_date": task.end_date.isoformat() if task.end_date else "",
        "next_card_date": task.next_card_date.isoformat() if task.next_card_date else "",
        "weekdays": list(task.weekdays),
        "faces": [person.pk for person in task.faces.all()],
    }
    if task.day_only:
        form["day_only"] = "on"
    if not task.is_active:
        del form["is_active"]
    return form


def _add_task(client, **filled_in):
    return client.post("/admin/tasks/task/add/", _empty_task_form() | filled_in)


def _change_task(client, task, **changed):
    """Change some fields of a task and leave the rest as the page showed them."""
    task.refresh_from_db()
    form = _form_showing(task) | changed
    # A box that is unticked is simply not sent.
    form = {field: value for field, value in form.items() if value is not False}
    response = client.post(f"/admin/tasks/task/{task.pk}/change/", form)
    task.refresh_from_db()
    return response


def test_the_management_index_lists_tasks_rooms_and_finished_tasks(owner_client):
    index = owner_client.get("/admin/").content.decode()

    assert "Úkoly" in index
    assert "Místnosti" in index
    assert "Hotové úkoly" in index


# ---- Adding a task ----


def test_choosing_a_picture_is_enough_to_add_a_task(owner_client):
    response = _add_task(owner_client, picture="water-plants")

    assert response.status_code == 302
    task = Task.objects.get()
    assert task.names == {"cs": "Zalít květiny", "en": "Water the plants"}
    assert task.picture == "water-plants"
    # A daily task that starts today has its first card today.
    assert task.next_card_date == TODAY()


def test_a_typed_name_wins_over_the_name_of_the_picture(owner_client):
    _add_task(owner_client, picture="water-plants", names_cs="Zalít fíkus")

    assert Task.objects.get().names == {"cs": "Zalít fíkus", "en": "Water the plants"}


def test_a_task_can_have_a_name_and_no_picture(owner_client):
    _add_task(owner_client, names_cs="Seřídit hodiny")

    task = Task.objects.get()
    assert task.names == {"cs": "Seřídit hodiny"}
    assert task.name == "Seřídit hodiny"
    assert task.emoji == "📋"


def test_a_task_needs_a_name_or_a_picture(owner_client):
    response = _add_task(owner_client)

    assert response.status_code == 200
    assert "Napište název, nebo vyberte obrázek" in response.content.decode()
    assert not Task.objects.exists()


def test_an_english_name_alone_is_not_enough(owner_client):
    response = _add_task(owner_client, names_en="Wind the clock")

    assert response.status_code == 200
    assert not Task.objects.exists()


def test_a_weekly_task_needs_its_days(owner_client):
    response = _add_task(owner_client, picture="vacuum", repeat="weekly")

    assert response.status_code == 200
    assert "Vyberte aspoň jeden den v týdnu." in response.content.decode()
    assert not Task.objects.exists()


def test_a_weekly_task_gets_its_first_card_on_its_next_day(owner_client):
    in_three_days = TODAY() + timedelta(days=3)

    _add_task(owner_client, picture="vacuum", repeat="weekly", weekdays=[in_three_days.weekday()])

    task = Task.objects.get()
    assert task.weekdays == [in_three_days.weekday()]
    assert task.next_card_date == in_three_days


def test_a_monthly_task_needs_its_day(owner_client):
    response = _add_task(owner_client, picture="clean-fridge", repeat="monthly")

    assert "Vyberte den v měsíci." in response.content.decode()
    assert not Task.objects.exists()


def test_the_end_cannot_be_before_the_start(owner_client):
    yesterday = (TODAY() - timedelta(days=1)).isoformat()

    response = _add_task(owner_client, picture="vacuum", end_date=yesterday)

    assert "Konec nemůže být před začátkem." in response.content.decode()


def test_a_task_can_be_given_a_room_a_hint_faces_and_an_effort(owner_client, adult, child):
    kitchen = make_room("Kuchyně")

    _add_task(
        owner_client,
        picture="load-dishwasher",
        room=kitchen.pk,
        hint="Tablety jsou pod dřezem",
        faces=[child.pk],
        effort="2",
        day_only="on",
    )

    task = Task.objects.get()
    assert (task.room, task.hint, task.effort, task.day_only) == (
        kitchen,
        "Tablety jsou pod dřezem",
        2,
        True,
    )
    assert list(task.faces.all()) == [child]


# ---- Changing a task ----


def test_saving_a_task_unchanged_changes_nothing(owner_client, adult):
    task = make_task("Vysát", start_date=TODAY() - timedelta(days=3))
    before = task.next_card_date

    response = _change_task(owner_client, task)

    assert response.status_code == 302
    assert task.next_card_date == before


def test_changing_when_a_task_repeats_leaves_its_waiting_card(owner_client):
    task = make_task("Vysát")
    in_three_days = TODAY() + timedelta(days=3)

    _change_task(owner_client, task, repeat="weekly", weekdays=[in_three_days.weekday()])

    assert task.repeat == "weekly"
    assert task.next_card_date == TODAY()


def test_changing_when_a_task_repeats_replans_one_that_is_not_waiting(owner_client, adult):
    task = make_task("Vysát")
    cards.complete(task_id=task.pk, card_date=TODAY(), people=[adult])
    in_three_days = TODAY() + timedelta(days=3)

    _change_task(owner_client, task, repeat="weekly", weekdays=[in_three_days.weekday()])

    assert task.next_card_date == in_three_days


def test_changing_only_the_name_does_not_move_the_card(owner_client, adult):
    task = make_task("Vysát")
    cards.complete(task_id=task.pk, card_date=TODAY(), people=[adult])

    _change_task(owner_client, task, names_cs="Vysát koberce")

    assert task.name == "Vysát koberce"
    assert task.next_card_date == TODAY() + timedelta(days=1)


def test_a_day_set_by_hand_is_respected(owner_client):
    task = make_task("Vysát")
    next_week = TODAY() + timedelta(days=7)

    _change_task(owner_client, task, next_card_date=next_week.isoformat())

    assert task.next_card_date == next_week


def test_clearing_the_day_lets_the_app_work_it_out(owner_client):
    task = make_task("Posekat trávník")
    _change_task(owner_client, task, next_card_date=(TODAY() + timedelta(days=40)).isoformat())

    _change_task(owner_client, task, next_card_date="")

    assert task.next_card_date == TODAY()


def test_a_task_switched_off_has_no_card_and_starts_afresh_when_switched_on(owner_client):
    task = make_task("Vysát", start_date=TODAY() - timedelta(days=30))
    assert task.next_card_date == TODAY() - timedelta(days=30)

    _change_task(owner_client, task, is_active=False)
    assert not task.is_active
    assert list(cards.waiting_cards(TODAY())) == []

    _change_task(owner_client, task, is_active="on")
    # Back in use: its card is today's, not one "since" a month ago.
    assert task.is_active
    assert task.next_card_date == TODAY()


def test_tasks_cannot_be_deleted_only_switched_off(owner_client):
    task = make_task("Vysát")

    assert owner_client.get(f"/admin/tasks/task/{task.pk}/delete/").status_code == 403
    assert Task.objects.filter(pk=task.pk).exists()


# ---- Actions on tasks ----


def _run_action(client, model: str, action: str, chosen) -> None:
    client.post(
        f"/admin/tasks/{model}/",
        {"action": action, "_selected_action": [item.pk for item in chosen]},
    )


def test_skipping_a_waiting_card_from_the_task_list(owner_client):
    task = make_task("Zalít květiny")

    _run_action(owner_client, "task", "skip_waiting_card", [task])

    task.refresh_from_db()
    assert task.next_card_date == TODAY() + timedelta(days=1)
    assert not Completion.objects.exists()


def test_showing_a_card_today_from_the_task_list(owner_client):
    task = make_task("Posekat trávník", start_date=TODAY() + timedelta(days=20))

    _run_action(owner_client, "task", "show_today", [task])

    assert list(cards.waiting_cards(TODAY())) == [task]


# ---- Finished tasks ----


def test_finished_tasks_are_listed_and_can_be_put_back(owner_client, adult):
    task = make_task("Zalít květiny")
    completion = cards.complete(task_id=task.pk, card_date=TODAY(), people=[adult], note="hotovo")

    listing = owner_client.get("/admin/tasks/completion/").content.decode()
    assert "Zalít květiny" in listing
    assert adult.display_name in listing

    _run_action(owner_client, "completion", "put_card_back", [completion])

    assert not Completion.objects.exists()
    assert list(cards.waiting_cards(TODAY())) == [task]


def test_a_finished_task_cannot_be_added_by_hand(owner_client):
    assert owner_client.get("/admin/tasks/completion/add/").status_code == 403


# ---- Rooms ----


def test_choosing_a_picture_is_enough_to_add_a_room(owner_client):
    response = owner_client.post(
        "/admin/tasks/room/add/",
        {"picture": "kitchen", "names_cs": "", "names_en": "", "position": "1", "is_active": "on"},
    )

    assert response.status_code == 302
    room = Room.objects.get()
    assert room.names == {"cs": "Kuchyně", "en": "Kitchen"}
    assert room.emoji == "🍳"


def test_a_room_can_be_removed_and_its_tasks_simply_have_none(owner_client):
    kitchen = make_room("Kuchyně")
    task = make_task("Naplnit myčku", room=kitchen)

    owner_client.post(f"/admin/tasks/room/{kitchen.pk}/delete/", {"post": "yes"})

    task.refresh_from_db()
    assert not Room.objects.exists()
    assert task.room is None
