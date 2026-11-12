"""The hello page: languages, the live fragment and Czech plural forms."""

import pytest
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone, translation


@pytest.mark.django_db
def test_hello_page_is_czech_by_default(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["Content-Language"] == "cs"
    html = response.content.decode()
    assert '<html lang="cs"' in html
    assert "Funguje to!" in html
    assert "It works!" not in html


@pytest.mark.django_db
def test_browser_language_preference_is_ignored(client):
    response = client.get("/", headers={"accept-language": "en-US,en;q=0.9"})

    assert "Funguje to!" in response.content.decode()


@pytest.mark.django_db
def test_device_that_chose_english_gets_english(client):
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"

    response = client.get("/")

    assert response.headers["Content-Language"] == "en"
    html = response.content.decode()
    assert '<html lang="en"' in html
    assert "It works!" in html
    assert "Funguje to!" not in html


@pytest.mark.django_db
def test_unknown_language_cookie_falls_back_to_czech(client):
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = "xx"

    assert "Funguje to!" in client.get("/").content.decode()


@pytest.mark.django_db
def test_language_buttons_remember_the_choice_on_the_device(client):
    response = client.post("/i18n/setlang/", {"language": "en", "next": "/"})

    assert response.status_code == 302
    assert response.cookies[settings.LANGUAGE_COOKIE_NAME].value == "en"
    assert "It works!" in client.get("/").content.decode()


@pytest.mark.django_db
def test_hello_page_loads_the_bundled_scripts_and_styles(client):
    html = client.get("/").content.decode()

    assert "/static/vendor/htmx.min.js" in html
    assert "/static/vendor/alpine.min.js" in html
    assert "/static/css/tailwind.css" in html


@pytest.mark.django_db
def test_hello_page_shows_the_installation_fingerprint(client):
    # The fingerprint is how a restored backup is recognised (docs/deploy/home-assistant.md).
    assert len(settings.INSTALLATION_ID) == 8
    assert settings.INSTALLATION_ID in client.get("/").content.decode()
    assert settings.SECRET_KEY not in client.get("/").content.decode()


@pytest.mark.django_db
def test_status_is_a_fragment_not_a_whole_page(client):
    response = client.get("/status/")

    assert response.status_code == 200
    html = response.content.decode()
    assert "Čas serveru" in html
    assert "<html" not in html


def _status_html(minutes: int, language: str) -> str:
    context = {"minutes_running": minutes, "database_ok": True, "now": timezone.localtime()}
    with translation.override(language):
        return render_to_string("household/_status.html", context)


@pytest.mark.parametrize(
    ("minutes", "expected"),
    [
        (0, "0 minut"),
        (1, "1 minutu"),
        (2, "2 minuty"),
        (4, "4 minuty"),
        (5, "5 minut"),
        (22, "22 minut"),
    ],
)
def test_czech_plural_forms(minutes, expected):
    assert f">{expected}</dd>" in _status_html(minutes, "cs")


@pytest.mark.parametrize(("minutes", "expected"), [(1, "1 minute"), (2, "2 minutes")])
def test_english_plural_forms(minutes, expected):
    assert f">{expected}</dd>" in _status_html(minutes, "en")
