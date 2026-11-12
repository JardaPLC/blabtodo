"""Family members: names, colours, PINs and photos."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from people.colours import COLOURS
from people.models import User
from tests.conftest import make_person

pytestmark = pytest.mark.django_db


def test_project_uses_its_own_user_model(django_user_model):
    assert django_user_model is User


def test_user_name_is_made_from_the_display_name():
    assert make_person("Táta", User.Role.ADULT, "1234").username == "tata"


def test_two_people_with_the_same_name_get_different_user_names():
    first = make_person("Emma", User.Role.CHILD)
    second = make_person("Emma", User.Role.CHILD)

    assert (first.username, second.username) == ("emma", "emma-2")


def test_a_name_without_latin_letters_still_gets_a_user_name():
    assert make_person("夏", User.Role.CHILD).username == "person"


def test_each_new_person_gets_a_colour_nobody_has_yet():
    colours = [make_person(f"Person {n}", User.Role.CHILD).colour for n in range(len(COLOURS))]

    assert sorted(colours) == sorted(COLOURS)


def test_a_person_beyond_the_palette_still_gets_a_colour():
    for n in range(len(COLOURS)):
        make_person(f"Person {n}", User.Role.CHILD)

    assert make_person("One more", User.Role.CHILD).colour in COLOURS


def test_pin_is_checked_and_never_stored_as_written(adult):
    assert adult.check_pin("2468")
    assert not adult.check_pin("2469")
    assert "2468" not in adult.pin_hash
    assert adult.pin_hash.startswith("pin_pbkdf2_sha256$")


def test_a_person_without_a_pin_matches_no_pin(child):
    assert not child.has_pin
    assert not child.check_pin("")
    assert not child.check_pin("0000")


def test_replacing_a_photo_removes_the_old_file(child):
    child.photo = SimpleUploadedFile("one.jpg", b"first", content_type="image/jpeg")
    child.save()
    old_path = child.photo.path

    child.photo = SimpleUploadedFile("two.jpg", b"second", content_type="image/jpeg")
    child.save()

    assert child.photo.path != old_path
    assert not child.photo.storage.exists(old_path)
    assert child.photo.storage.exists(child.photo.path)


def test_photo_file_names_do_not_reveal_whose_they_are(child):
    child.photo = SimpleUploadedFile("emma-holiday.jpg", b"x", content_type="image/jpeg")
    child.save()

    assert child.photo.name.startswith("faces/")
    assert "emma" not in child.photo.name
