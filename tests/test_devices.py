"""Allowed devices: allowing one by PIN, recognising it, and keeping others out."""

from datetime import timedelta

import pytest
from django.utils import timezone

from people.devices import COOKIE_NAME, find_device, guess_device_name, trust_device
from people.models import Device
from tests.conftest import ADULT_PIN

pytestmark = pytest.mark.django_db


def test_only_a_fingerprint_of_the_device_token_is_stored(adult):
    device, token = trust_device(name="Kitchen panel", trusted_by=adult)

    assert token not in device.token_hash
    assert find_device(token) == device
    assert find_device("some-other-token") is None
    assert find_device(None) is None


def test_a_removed_device_is_no_longer_recognised(adult):
    device, token = trust_device(name="Old phone", trusted_by=adult)
    device.is_active = False
    device.save()

    assert find_device(token) is None


@pytest.mark.parametrize(
    ("user_agent", "name"),
    [
        (
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) Chrome/126 Mobile Safari/537.36",
            "Telefon s Androidem",
        ),
        ("Mozilla/5.0 (Linux; Android 13; SM-X200) Chrome/126 Safari/537.36", "Tablet s Androidem"),
        ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) Safari/604.1", "iPhone"),
        ("Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) Safari/604.1", "iPad"),
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36", "Počítač s Windows"),
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15", "Mac"),
        ("Mozilla/5.0 (X11; Linux x86_64) Firefox/128.0", "Počítač s Linuxem"),
        ("", "Zařízení"),
    ],
)
def test_a_new_device_gets_a_sensible_first_name(user_agent, name):
    assert guess_device_name(user_agent) == name


def test_an_unknown_device_is_sent_to_the_pin_screen_and_remembers_where_it_was_going(
    client, adult
):
    response = client.get("/check/")

    assert response.status_code == 302
    assert response.headers["Location"] == "/trust/?next=%2Fcheck%2F"


def test_the_pin_screen_shows_no_names_or_faces(client, adult):
    html = client.get("/trust/").content.decode()

    assert "Toto zařízení ještě není povolené" in html
    assert adult.display_name not in html


def test_an_adults_pin_allows_the_device_and_returns_to_the_page(client, adult):
    response = client.post(
        "/trust/",
        {"pin": ADULT_PIN, "next": "/check/"},
        headers={"user-agent": "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X)"},
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/check/"
    device = Device.objects.get()
    assert (device.name, device.trusted_by) == ("iPad", adult)

    cookie = response.cookies[COOKIE_NAME]
    assert cookie["httponly"]
    assert cookie["samesite"] == "Lax"
    assert int(cookie["max-age"]) > 60 * 60 * 24 * 365

    assert client.get("/check/").status_code == 200


def test_a_wrong_pin_allows_nothing(client, adult):
    response = client.post("/trust/", {"pin": "0000"})

    assert response.status_code == 200
    assert "Špatný PIN." in response.content.decode()
    assert not Device.objects.exists()
    assert COOKIE_NAME not in response.cookies


def test_a_malformed_pin_is_explained_and_does_not_count_as_a_try(client, adult):
    for _try in range(8):
        response = client.post("/trust/", {"pin": "12"})

    assert "PIN má 4 až 8 číslic." in response.content.decode()
    # Still not paused: the right PIN works straight away.
    assert client.post("/trust/", {"pin": ADULT_PIN}).status_code == 302


def test_after_five_wrong_pins_entry_is_paused_even_for_the_right_one(client, adult):
    for _try in range(5):
        response = client.post("/trust/", {"pin": "0000"})

    html = response.content.decode()
    assert "Příliš mnoho špatných pokusů." in html
    assert "Zkuste to znovu za 1 minutu." in html

    response = client.post("/trust/", {"pin": ADULT_PIN})

    assert response.status_code == 200
    assert "Příliš mnoho špatných pokusů." in response.content.decode()
    assert not Device.objects.exists()


def test_after_allowing_the_device_is_never_sent_to_another_site(client, adult):
    response = client.post("/trust/", {"pin": ADULT_PIN, "next": "https://evil.example.com/"})

    assert response.headers["Location"] == "/"


def test_an_allowed_device_skips_the_pin_screen(trusted_client):
    response = trusted_client.get("/trust/?next=/check/")

    assert response.headers["Location"] == "/check/"


def test_a_removed_device_is_sent_back_to_the_pin_screen(trusted_client):
    Device.objects.update(is_active=False)

    assert trusted_client.get("/").headers["Location"] == "/trust/?next=%2F"


def test_an_open_page_on_a_removed_device_is_told_to_reload_as_a_whole(trusted_client):
    Device.objects.update(is_active=False)

    response = trusted_client.get("/status/", headers={"hx-request": "true"})

    assert response.status_code == 204
    assert response.headers["HX-Redirect"] == "/trust/"


def test_last_seen_and_the_cookie_are_renewed_about_once_an_hour(trusted_client):
    device = Device.objects.get()

    # Seen a moment ago: nothing is written and no cookie is sent again.
    response = trusted_client.get("/")
    assert COOKIE_NAME not in response.cookies
    assert Device.objects.get().last_seen_at == device.last_seen_at

    two_hours_ago = timezone.now() - timedelta(hours=2)
    Device.objects.update(last_seen_at=two_hours_ago)

    response = trusted_client.get("/")
    assert COOKIE_NAME in response.cookies
    assert Device.objects.get().last_seen_at > two_hours_ago
