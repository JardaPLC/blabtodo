"""The device check page and its live fragment."""

import pytest
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone, translation


def test_check_page_loads_the_bundled_scripts_and_styles(trusted_client):
    html = trusted_client.get("/check/").content.decode()

    assert "Funguje to!" in html
    assert "/static/vendor/htmx.min.js" in html
    assert "/static/vendor/alpine.min.js" in html
    assert "/static/css/tailwind.css" in html


def test_check_page_shows_the_installation_fingerprint(trusted_client):
    html = trusted_client.get("/check/").content.decode()

    assert len(settings.INSTALLATION_ID) == 8
    assert settings.INSTALLATION_ID in html
    assert settings.SECRET_KEY not in html


def test_status_is_a_fragment_not_a_whole_page(trusted_client):
    response = trusted_client.get("/status/")

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
