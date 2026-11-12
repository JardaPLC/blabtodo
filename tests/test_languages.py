"""Which language a device sees. Tested on the first-run screen, which needs no setup."""

import pytest
from django.conf import settings

pytestmark = pytest.mark.django_db


def test_a_device_sees_czech_by_default(client):
    response = client.get("/setup/")

    assert response.status_code == 200
    assert response.headers["Content-Language"] == "cs"
    html = response.content.decode()
    assert '<html lang="cs"' in html
    assert "Vítejte" in html
    assert "Welcome" not in html


def test_browser_language_preference_is_ignored(client):
    response = client.get("/setup/", headers={"accept-language": "en-US,en;q=0.9"})

    assert "Vítejte" in response.content.decode()


def test_device_that_chose_english_gets_english(client):
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"

    response = client.get("/setup/")

    assert response.headers["Content-Language"] == "en"
    html = response.content.decode()
    assert '<html lang="en"' in html
    assert "Welcome" in html
    assert "Vítejte" not in html


def test_unknown_language_cookie_falls_back_to_czech(client):
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = "xx"

    assert "Vítejte" in client.get("/setup/").content.decode()


def test_language_buttons_remember_the_choice_on_the_device(client):
    response = client.post("/i18n/setlang/", {"language": "en", "next": "/setup/"})

    assert response.status_code == 302
    assert response.cookies[settings.LANGUAGE_COOKIE_NAME].value == "en"
    assert "Welcome" in client.get("/setup/").content.decode()
