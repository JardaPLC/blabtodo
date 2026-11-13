"""QR stickers: printing them, and what scanning one does."""

import re

import pytest

from tasks import cards
from tasks.models import Task
from tasks.schedule import ON_DEMAND, WEEKLY
from tests.conftest import make_task

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner_client(client, adult):
    adult.is_staff = adult.is_superuser = True
    adult.save()
    client.force_login(adult)
    return client


def scan_address(task: Task) -> str:
    return f"/t/{task.ensure_qr_key()}/"


# ---- The task that only appears when asked for ----


def test_an_on_demand_task_has_no_card_until_asked_for():
    task = make_task("Vyměnit filtr", repeat=ON_DEMAND)

    assert task.next_card_date is None
    assert list(cards.waiting_cards(cards.today())) == []


def test_an_on_demand_task_goes_away_again_once_done(adult):
    task = make_task("Vyměnit filtr", repeat=ON_DEMAND)
    cards.show_today(task, cards.today())

    cards.complete(task_id=task.pk, card_date=cards.today(), people=[adult])

    task.refresh_from_db()
    assert task.next_card_date is None


# ---- The key ----


def test_a_task_gets_its_key_once_and_keeps_it():
    task = make_task("Vyměnit filtr")
    assert task.qr_key is None

    key = task.ensure_qr_key()
    task.refresh_from_db()

    assert len(key) >= 16
    assert task.qr_key == key
    assert task.ensure_qr_key() == key


def test_every_task_gets_a_different_key():
    keys = {make_task(f"Úkol {n}").ensure_qr_key() for n in range(20)}

    assert len(keys) == 20


# ---- Scanning ----


def test_scanning_asks_before_showing_the_card(trusted_client):
    task = make_task("Vyměnit filtr", repeat=ON_DEMAND)

    html = trusted_client.get(scan_address(task)).content.decode()

    assert "Vyměnit filtr" in html
    assert "Zobrazit tento úkol v Dnes?" in html
    assert list(cards.waiting_cards(cards.today())) == []


def test_confirming_shows_the_card_on_today(trusted_client):
    task = make_task("Vyměnit filtr", repeat=ON_DEMAND)

    response = trusted_client.post(scan_address(task))

    assert response.headers["Location"] == "/"
    assert list(cards.waiting_cards(cards.today())) == [task]


def test_scanning_a_card_that_is_already_waiting_changes_nothing(trusted_client):
    task = make_task("Vysát", start_date=cards.today().replace(day=1))
    waiting_since = task.next_card_date

    html = trusted_client.get(scan_address(task)).content.decode()
    trusted_client.post(scan_address(task))

    assert "Už čeká v Dnes." in html
    task.refresh_from_db()
    assert task.next_card_date == waiting_since


def test_scanning_brings_a_repeating_task_forward(trusted_client):
    task = make_task("Posekat trávník", repeat=WEEKLY, weekdays=[(cards.today().weekday() + 3) % 7])

    trusted_client.post(scan_address(task))

    assert list(cards.waiting_cards(cards.today())) == [task]


@pytest.mark.parametrize("why", ["unknown", "switched off"])
def test_a_code_that_leads_nowhere_says_so_kindly(trusted_client, why):
    task = make_task("Vyměnit filtr", repeat=ON_DEMAND)
    address = scan_address(task)
    if why == "unknown":
        address = "/t/not-a-real-key/"
    else:
        task.is_active = False
        task.save()

    response = trusted_client.get(address)
    trusted_client.post(address)

    assert response.status_code == 404
    assert "Tento kód nikam nevede" in response.content.decode()
    task.refresh_from_db()
    assert task.next_card_date is None


def test_a_device_that_is_not_allowed_is_asked_for_a_pin_and_comes_back(client, adult):
    task = make_task("Vyměnit filtr", repeat=ON_DEMAND)
    address = scan_address(task)

    response = client.get(address)

    assert response.headers["Location"] == "/trust/?next=" + address.replace("/", "%2F")


# ---- Printing ----


def test_the_print_action_leads_to_a_page_of_stickers(owner_client):
    first = make_task("Vyměnit filtr", repeat=ON_DEMAND)
    second = make_task("Odvápnit konvici", repeat=ON_DEMAND)

    response = owner_client.post(
        "/admin/tasks/task/",
        {"action": "print_stickers", "_selected_action": [first.pk, second.pk]},
    )
    page = owner_client.get(response.headers["Location"], HTTP_HOST="192.168.1.20:8000")
    html = page.content.decode()

    assert html.count("<svg") == 2
    assert "Vyměnit filtr" in html and "Odvápnit konvici" in html
    assert "http://192.168.1.20:8000/" in html
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.qr_key and second.qr_key


def test_the_code_holds_the_scan_address_as_the_browser_reached_the_app(owner_client):
    task = make_task("Vyměnit filtr", repeat=ON_DEMAND)

    owner_client.get(
        f"/admin/tasks/task/stickers/?ids={task.pk}", HTTP_HOST="homeassistant.local:8000"
    )

    task.refresh_from_db()
    import segno

    expected = segno.make(f"http://homeassistant.local:8000/t/{task.qr_key}/", error="m")
    page = owner_client.get(
        f"/admin/tasks/task/stickers/?ids={task.pk}", HTTP_HOST="homeassistant.local:8000"
    ).content.decode()
    printed = re.search(r'd="([^"]+)"', page.split("<svg", 1)[1]).group(1)
    assert printed in expected.svg_inline(omitsize=True)


def test_printing_again_keeps_the_same_codes(owner_client):
    task = make_task("Vyměnit filtr", repeat=ON_DEMAND)
    address = f"/admin/tasks/task/stickers/?ids={task.pk}"

    def codes(page):
        return re.findall(r"<svg.*?</svg>", page.content.decode(), re.S)

    first, second = codes(owner_client.get(address)), codes(owner_client.get(address))

    assert len(first) == 1
    assert first == second


def test_stickers_are_not_printed_for_tasks_that_are_switched_off(owner_client):
    task = make_task("Vyměnit filtr", is_active=False)

    html = owner_client.get(f"/admin/tasks/task/stickers/?ids={task.pk}").content.decode()

    assert "<svg" not in html


def test_the_sticker_page_is_for_the_owner_only(client, trusted_client):
    task = make_task("Vyměnit filtr")

    response = trusted_client.get(f"/admin/tasks/task/stickers/?ids={task.pk}")

    assert "/admin/login/" in response.headers["Location"]
