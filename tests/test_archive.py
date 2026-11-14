"""The list of finished tasks: newest first, grouped by day, older days on scrolling."""

from datetime import timedelta

import pytest

from tasks import cards
from tasks.labels import day_heading
from tasks.views import ARCHIVE_DAYS
from tests.conftest import make_room, make_task, noon

pytestmark = pytest.mark.django_db


def finish(task, day, people, note=""):
    """Record a completion of the task on a given day, whatever its card says."""
    task.next_card_date = day
    task.save()
    return cards.complete(task_id=task.pk, card_date=day, people=people, note=note, now=noon(day))


def test_finished_tasks_show_picture_name_room_time_faces_and_note(trusted_client, adult, child):
    task = make_task("Zalít květiny", picture="water-plants", room=make_room("Obývák"))
    finish(task, cards.today(), [adult, child], note="i ten fíkus")

    html = trusted_client.get("/done/").content.decode()

    assert "Zalít květiny" in html
    assert "Obývák" in html
    assert "12:00" in html
    assert "i ten fíkus" in html
    assert "🌱" in html
    assert adult.initial in html and child.initial in html


def test_newest_first_and_grouped_by_day(trusted_client, adult):
    today = cards.today()
    finish(make_task("Starší úkol"), today - timedelta(days=1), [adult])
    finish(make_task("Novější úkol"), today, [adult])

    html = trusted_client.get("/done/").content.decode()

    assert html.index("Dnes") < html.index("Novější úkol") < html.index("Včera")
    assert html.index("Včera") < html.index("Starší úkol")


def test_older_days_load_when_the_list_is_scrolled_to_its_end(trusted_client, adult):
    today = cards.today()
    task = make_task("Každý den")
    for days_ago in range(ARCHIVE_DAYS + 2):
        finish(task, today - timedelta(days=days_ago), [adult])
    oldest_shown = today - timedelta(days=ARCHIVE_DAYS - 1)

    first = trusted_client.get("/done/").content.decode()
    assert f"before={oldest_shown.isoformat()}" in first

    more = trusted_client.get(
        f"/done/?before={oldest_shown.isoformat()}", headers={"HX-Request": "true"}
    ).content.decode()
    # Just the two remaining days, without the page around them, and nothing further.
    assert "<html" not in more
    assert more.count("<section") == 2
    assert "before=" not in more


def test_an_empty_list_says_so_kindly(trusted_client):
    html = trusted_client.get("/done/").content.decode()

    assert "Zatím nic není hotové" in html


def test_a_strange_date_just_shows_the_newest(trusted_client, adult):
    finish(make_task("Úkol"), cards.today(), [adult])

    assert "Úkol" in trusted_client.get("/done/?before=yesterday").content.decode()


def test_the_list_needs_an_allowed_device(client, adult):
    assert client.get("/done/").headers["Location"].startswith("/trust/")


def test_today_links_to_the_finished_tasks(trusted_client):
    assert 'href="/done/"' in trusted_client.get("/").content.decode()


def test_day_headings():
    today = cards.today()

    assert day_heading(today, today) == "Dnes"
    assert day_heading(today - timedelta(days=1), today) == "Včera"
    a_year_ago = today.replace(year=today.year - 1)
    assert str(a_year_ago.year) in day_heading(a_year_ago, today)
