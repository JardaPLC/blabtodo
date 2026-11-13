"""
The screens in a real browser: the parts that only work if htmx and Alpine.js do.

The other tests ask the server for pages and read the HTML. These tap through the pages
the way a person does, in a headless Chromium.

    uv run playwright install chromium     (once)
    uv run pytest -m browser

To also save screenshots in phone, tablet and PC sizes, name a folder for them:

    set BLABTODO_SCREENSHOTS=screenshots
    uv run pytest -m browser
"""

import os
import re
from datetime import timedelta
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from people.devices import COOKIE_NAME, trust_device
from people.models import User
from tasks import cards
from tasks.models import Completion
from tests.conftest import ADULT_PIN, make_person, make_room, make_task

# Playwright runs an event loop of its own, which makes Django believe the database is
# being used from asynchronous code. It is not; this turns the false alarm off.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

pytestmark = [pytest.mark.browser, pytest.mark.django_db(transaction=True)]

# The phone height is what is left of a small phone's screen once the browser's own bars
# are taken off. If something fits here, it fits on any phone.
SCREENS = {"phone": (360, 640), "tablet": (820, 1180), "pc": (1440, 900)}


@pytest.fixture
def family(transactional_db):
    return make_person("Mum", User.Role.ADULT, ADULT_PIN), make_person("Emma", User.Role.CHILD)


@pytest.fixture
def problems(page: Page):
    """Fail the test if the page reported a script error along the way."""
    found = []
    page.on("pageerror", lambda error: found.append(f"script error: {error}"))
    page.on(
        "console",
        lambda message: (
            found.append(f"console: {message.text}") if message.type == "error" else None
        ),
    )
    yield found
    assert found == []


@pytest.fixture
def allowed_page(page: Page, live_server, family, problems):
    """A browser on a device that an adult has already allowed."""
    _device, token = trust_device(name="Test browser", trusted_by=family[0])
    page.context.add_cookies([{"name": COOKIE_NAME, "value": token, "url": live_server.url}])
    return page


def test_marking_a_card_done_and_undoing_it(allowed_page, live_server):
    make_task("Zalít květiny", picture="water-plants")
    page = allowed_page
    page.goto(live_server.url)

    card = page.get_by_role("button", name=re.compile("Zalít květiny"))
    sheet = page.locator("#sheet")
    expect(card).to_be_visible()
    expect(sheet).not_to_be_visible()

    card.click()
    expect(sheet).to_be_visible()
    expect(sheet.get_by_text("Kdo to udělal?")).to_be_visible()
    done = sheet.get_by_role("button", name="Hotovo", exact=True)
    expect(done).to_be_disabled()

    sheet.get_by_text("Mum", exact=True).click()
    expect(done).to_be_enabled()
    done.click()

    expect(sheet).not_to_be_visible()
    expect(page.locator("#cards")).to_contain_text("Hotovo!")
    expect(page.locator("#cards")).not_to_contain_text("Zalít květiny")
    bar = page.locator("#undo-bar")
    expect(bar).to_contain_text("Hotovo: Zalít květiny")
    assert Completion.objects.count() == 1

    bar.get_by_role("button", name="Vrátit zpět").click()
    expect(page.locator("#cards")).to_contain_text("Zalít květiny")
    expect(bar).not_to_contain_text("Hotovo:")
    assert Completion.objects.count() == 0


def test_two_people_can_have_done_it_together(allowed_page, live_server, family):
    make_task("Uvařit", picture="cook")
    page = allowed_page
    page.goto(live_server.url)

    page.get_by_role("button", name=re.compile("Uvařit")).click()
    sheet = page.locator("#sheet")
    sheet.get_by_text("Mum", exact=True).click()
    sheet.get_by_text("Emma", exact=True).click()
    sheet.get_by_role("button", name="Hotovo", exact=True).click()

    expect(sheet).not_to_be_visible()
    assert set(Completion.objects.get().done_by.all()) == set(family)


def test_unticking_the_only_face_disables_done_again(allowed_page, live_server):
    make_task("Uvařit", picture="cook")
    page = allowed_page
    page.goto(live_server.url)

    page.get_by_role("button", name=re.compile("Uvařit")).click()
    sheet = page.locator("#sheet")
    done = sheet.get_by_role("button", name="Hotovo", exact=True)
    face = sheet.get_by_text("Mum", exact=True)

    face.click()
    expect(done).to_be_enabled()
    face.click()
    expect(done).to_be_disabled()


def test_a_card_meant_for_one_person_takes_two_taps(allowed_page, live_server, family):
    _mum, emma = family
    make_task("Uklidit hračky", picture="tidy-toys", faces=[emma])
    page = allowed_page
    page.goto(live_server.url)

    page.get_by_role("button", name=re.compile("Uklidit hračky")).click()
    # Emma's face is ticked already, so Done can be tapped straight away.
    page.locator("#sheet").get_by_role("button", name="Hotovo", exact=True).click()

    expect(page.locator("#sheet")).not_to_be_visible()
    assert list(Completion.objects.get().done_by.all()) == [emma]


def test_not_yet_closes_the_sheet_and_changes_nothing(allowed_page, live_server):
    make_task("Zalít květiny", picture="water-plants")
    page = allowed_page
    page.goto(live_server.url)

    page.get_by_role("button", name=re.compile("Zalít květiny")).click()
    page.locator("#sheet").get_by_role("button", name="Ještě ne").click()

    expect(page.locator("#sheet")).not_to_be_visible()
    expect(page.locator("#cards")).to_contain_text("Zalít květiny")
    assert not Completion.objects.exists()

    # The same card can be opened again afterwards.
    page.get_by_role("button", name=re.compile("Zalít květiny")).click()
    expect(page.locator("#sheet")).to_be_visible()


def test_a_note_can_be_added(allowed_page, live_server):
    make_task("Zalít květiny", picture="water-plants")
    page = allowed_page
    page.goto(live_server.url)

    page.get_by_role("button", name=re.compile("Zalít květiny")).click()
    sheet = page.locator("#sheet")
    note = sheet.get_by_label("Poznámka")
    expect(note).not_to_be_visible()

    sheet.get_by_role("button", name="Přidat poznámku").click()
    expect(note).to_be_focused()
    note.fill("fíkus potřeboval víc")
    sheet.get_by_text("Mum", exact=True).click()
    sheet.get_by_role("button", name="Hotovo", exact=True).click()

    expect(sheet).not_to_be_visible()
    assert Completion.objects.get().note == "fíkus potřeboval víc"


def test_tapping_a_face_shows_only_that_persons_cards(allowed_page, live_server, family):
    _mum, emma = family
    make_task("Uklidit hračky", faces=[emma])
    make_task("Vynést odpadky")
    page = allowed_page
    page.goto(live_server.url)

    page.get_by_role("link", name="Emma").click()

    expect(page.locator("#cards")).to_contain_text("Uklidit hračky")
    expect(page.locator("#cards")).not_to_contain_text("Vynést odpadky")

    page.get_by_role("link", name="Všichni").click()
    expect(page.locator("#cards")).to_contain_text("Vynést odpadky")


def test_the_cards_follow_what_another_device_does(allowed_page, live_server, family):
    task = make_task("Zalít květiny")
    page = allowed_page
    page.goto(live_server.url)
    expect(page.locator("#cards")).to_contain_text("Zalít květiny")

    # Someone marks it done on another device. The page fetches its cards again by
    # itself every 30 seconds; here that fetch is asked for at once.
    cards.complete(task_id=task.pk, card_date=cards.today(), people=[family[0]])
    page.evaluate(
        "htmx.ajax('GET', document.querySelector('#cards').getAttribute('hx-get'), '#cards')"
    )

    expect(page.locator("#cards")).to_contain_text("Hotovo!")


def test_allowing_a_device_with_the_pin_pad(page: Page, live_server, family, problems):
    page.goto(live_server.url)
    expect(page).to_have_url(re.compile(r"/trust/"))

    allow = page.get_by_role("button", name="Povolit toto zařízení")
    pin = page.locator('input[name="pin"]')
    expect(allow).to_be_disabled()

    for digit in "123":
        page.get_by_role("button", name=digit, exact=True).click()
    expect(pin).to_have_value("123")
    page.get_by_role("button", name="Smazat poslední číslici").click()
    expect(pin).to_have_value("12")
    page.get_by_role("button", name="Smazat", exact=True).click()
    expect(pin).to_have_value("")

    for digit in ADULT_PIN:
        page.get_by_role("button", name=digit, exact=True).click()
    expect(pin).to_have_value(ADULT_PIN)
    expect(allow).to_be_enabled()
    allow.click()

    expect(page.get_by_role("heading", name="Dnes")).to_be_visible()


def test_a_wrong_pin_typed_on_a_keyboard_is_refused(page: Page, live_server, family, problems):
    page.goto(live_server.url)

    page.locator('input[name="pin"]').fill("0000")
    page.get_by_role("button", name="Povolit toto zařízení").click()

    expect(page.get_by_text("Špatný PIN.")).to_be_visible()
    expect(page).to_have_url(re.compile(r"/trust/"))


def test_the_first_run_screen_leads_to_today(page: Page, live_server, transactional_db, problems):
    page.goto(live_server.url)
    expect(page.get_by_role("heading", name="Vítejte")).to_be_visible()

    page.get_by_label("Vaše jméno").fill("Táta")
    page.get_by_label("PIN", exact=True).fill("2468")
    page.get_by_label("PIN znovu").fill("2468")
    page.get_by_label("Heslo", exact=True).fill("correct horse battery")
    page.get_by_label("Heslo znovu").fill("correct horse battery")
    page.get_by_role("button", name="Vytvořit a začít").click()

    expect(page.get_by_role("heading", name="Dnes")).to_be_visible()
    expect(page.get_by_role("link", name="Táta")).to_be_visible()


def test_the_language_buttons_switch_this_device(
    page: Page, live_server, transactional_db, problems
):
    page.goto(live_server.url)

    page.get_by_role("button", name="English").click()
    expect(page.get_by_role("heading", name="Welcome")).to_be_visible()

    page.get_by_role("button", name="Čeština").click()
    expect(page.get_by_role("heading", name="Vítejte")).to_be_visible()


def test_the_device_check_page_parts_work(allowed_page, live_server):
    page = allowed_page
    page.goto(live_server.url + "/check/")

    details = page.locator("#details")
    expect(details).not_to_be_visible()
    page.get_by_role("button", name="Zobrazit technické podrobnosti").click()
    expect(details).to_be_visible()

    with page.expect_response(re.compile(r"/status/$")) as refreshed:
        page.get_by_role("button", name="Obnovit teď").click()
    assert refreshed.value.ok


# ---- Screenshots ----


def _a_household():
    """An invented family with enough going on to fill the screens."""
    mum = make_person("Máma", User.Role.ADULT, ADULT_PIN)
    dad = make_person("Táta", User.Role.ADULT, "1357")
    ema = make_person("Ema", User.Role.CHILD)
    tom = make_person("Tomáš", User.Role.CHILD)
    kitchen = make_room("Kuchyně", picture="kitchen")
    living = make_room("Obývací pokoj", picture="living-room")
    kids = make_room("Dětský pokoj", picture="childrens-room")
    day = cards.today()
    make_task(
        "Zalít květiny", picture="water-plants", room=living, start_date=day - timedelta(days=3)
    )
    make_task(
        "Naplnit myčku", picture="load-dishwasher", room=kitchen, start_date=day - timedelta(days=1)
    )
    make_task("Uklidit hračky", picture="tidy-toys", room=kids, faces=[ema, tom])
    make_task("Vysát", picture="vacuum", hint="Sáčky jsou ve skříni v předsíni")
    make_task("Vynést odpadky", picture="take-out-rubbish")
    make_task("Nakrmit zvíře", picture="feed-pet", faces=[ema])
    make_task("Pověsit prádlo", picture="hang-laundry", faces=[dad])
    make_task("Odnést balík na poštu", picture="post", start_date=day - timedelta(days=9))
    return mum


def _shoot(page: Page, folder: Path, name: str) -> None:
    for screen, (width, height) in SCREENS.items():
        page.set_viewport_size({"width": width, "height": height})
        page.wait_for_timeout(150)
        page.screenshot(path=str(folder / f"{name}-{screen}.png"))


@pytest.mark.skipif(not os.environ.get("BLABTODO_SCREENSHOTS"), reason="no folder named for them")
def test_screenshots(page: Page, live_server, transactional_db):
    folder = Path(os.environ["BLABTODO_SCREENSHOTS"])
    folder.mkdir(parents=True, exist_ok=True)

    page.goto(live_server.url)
    _shoot(page, folder, "1-first-run")

    mum = _a_household()
    page.goto(live_server.url)
    _shoot(page, folder, "2-pin-pad")

    _device, token = trust_device(name="Test browser", trusted_by=mum)
    page.context.add_cookies([{"name": COOKIE_NAME, "value": token, "url": live_server.url}])
    page.goto(live_server.url)
    _shoot(page, folder, "3-today")

    for screen, (width, height) in SCREENS.items():
        page.set_viewport_size({"width": width, "height": height})
        page.goto(live_server.url)
        page.get_by_role("button", name=re.compile("Vysát")).click()
        expect(page.locator("#sheet")).to_be_visible()
        page.locator("#sheet").get_by_text("Máma", exact=True).click()
        page.wait_for_timeout(150)
        page.screenshot(path=str(folder / f"4-done-sheet-{screen}.png"))
        page.locator("#sheet").get_by_role("button", name="Hotovo", exact=True).click()
        expect(page.locator("#undo-bar")).to_contain_text("Hotovo: Vysát")
        page.screenshot(path=str(folder / f"5-after-done-{screen}.png"))
        page.locator("#undo-bar").get_by_role("button", name="Vrátit zpět").click()
        expect(page.locator("#cards")).to_contain_text("Vysát")

    page.goto(live_server.url + "/check/")
    _shoot(page, folder, "6-device-check")
