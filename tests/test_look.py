"""The picture and font drafts, chosen per device on the Look page."""

from pathlib import Path

import pytest
from django.conf import settings

from tasks import catalogue, picture_drafts
from tests.conftest import make_task

pytestmark = pytest.mark.django_db

STATIC = Path(settings.BASE_DIR) / "static"


def choose(client, pictures, font):
    return client.post("/look/", {"pictures": pictures, "font": font})


def test_until_something_is_chosen_the_look_stays_as_it_was(trusted_client):
    make_task("Zalít", picture="water-plants")

    html = trusted_client.get("/").content.decode()

    assert "🌱" in html
    assert "font-andika" not in html


def test_a_choice_is_kept_on_this_device_and_shows_on_today(trusted_client):
    make_task("Zalít", picture="water-plants")

    response = choose(trusted_client, "fluent", "andika")

    assert response.status_code == 302
    html = trusted_client.get("/").content.decode()
    assert "pictures/fluent/tasks/water-plants" in html
    assert 'class="h-full font-andika"' in html


def test_material_pictures_sit_on_coloured_tiles(trusted_client):
    make_task("Zalít", picture="water-plants")
    choose(trusted_client, "material", "system")

    html = trusted_client.get("/").content.decode()

    assert "pictures/material/tasks/water-plants" in html
    assert "bg-green-100" in html


def test_a_task_without_a_known_picture_gets_the_fallback(trusted_client):
    make_task("Vlastní", picture="")
    choose(trusted_client, "fluent", "system")

    assert "pictures/fluent/fallback" in trusted_client.get("/").content.decode()


def test_nonsense_is_ignored(trusted_client):
    choose(trusted_client, "glitter", "comic-sans")
    trusted_client.cookies[picture_drafts.COOKIE_NAME] = "glitter.comic"

    html = trusted_client.get("/look/").content.decode()

    assert 'value="emoji" class="size-6 accent-green-700"\n                 checked' in html


def test_the_look_page_shows_every_picture_of_the_catalogue(trusted_client):
    html = trusted_client.get("/look/").content.decode()

    for entry in catalogue.TASKS + catalogue.ROOMS:
        assert entry.emoji in html


def test_the_look_page_needs_an_allowed_device(client, adult):
    assert client.get("/look/").headers["Location"].startswith("/trust/")


@pytest.mark.parametrize("pictures", ["fluent", "material"])
def test_every_catalogue_picture_has_a_file_in_both_sets(pictures):
    assert set(picture_drafts.TASKS) == {entry.key for entry in catalogue.TASKS}
    assert set(picture_drafts.ROOMS) == {entry.key for entry in catalogue.ROOMS}
    for kind, table in [("tasks", picture_drafts.TASKS), ("rooms", picture_drafts.ROOMS)]:
        for key in table:
            assert (STATIC / "pictures" / pictures / kind / f"{key}.svg").is_file(), key
    assert (STATIC / "pictures" / pictures / "fallback.svg").is_file()


def test_every_font_file_the_stylesheet_names_is_there():
    css = (Path(settings.BASE_DIR) / "styles" / "app.css").read_text(encoding="utf-8")
    for font in ["andika", "nunito", "atkinson"]:
        assert f"html.font-{font}" in css
    for name in (STATIC / "fonts").iterdir():
        assert f"../fonts/{name.name}" in css
