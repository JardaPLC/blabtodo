"""The management pages (Django admin) for people and devices."""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from people.devices import trust_device
from people.models import User
from tests.conftest import make_person

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner_client(client, adult):
    adult.is_staff = adult.is_superuser = True
    adult.save()
    client.force_login(adult)
    return client


def _person_form(**changes) -> dict:
    return {"display_name": "Emma", "role": "child", "colour": "rose", "is_active": "on"} | changes


def test_the_management_pages_need_the_owners_sign_in(client, adult):
    response = client.get("/admin/people/user/")

    assert response.status_code == 302
    assert "/admin/login/" in response.headers["Location"]


def test_the_management_pages_are_in_czech_and_show_only_what_is_used(owner_client):
    index = owner_client.get("/admin/").content.decode()

    assert "Správa blabtodo" in index
    assert "Členové rodiny" in index
    assert "Zařízení" in index
    assert "/admin/auth/group/" not in index  # permission groups are not used

    form = owner_client.get("/admin/people/user/add/").content.decode()
    assert "Bydlí tady" in form
    assert "Nový PIN" in form


def test_a_child_is_added_without_pin_or_password(owner_client):
    response = owner_client.post("/admin/people/user/add/", _person_form())

    assert response.status_code == 302
    emma = User.objects.get(display_name="Emma")
    assert (emma.username, emma.role, emma.colour) == ("emma", "child", "rose")
    assert not emma.has_pin
    assert not emma.has_usable_password()
    assert not emma.is_staff


def test_an_adult_cannot_be_added_without_a_pin(owner_client):
    response = owner_client.post(
        "/admin/people/user/add/", _person_form(display_name="Dad", role="adult")
    )

    assert response.status_code == 200
    assert "Dospělý potřebuje PIN." in response.content.decode()
    assert not User.objects.filter(display_name="Dad").exists()


def test_an_adult_is_added_with_a_pin(owner_client):
    owner_client.post(
        "/admin/people/user/add/", _person_form(display_name="Dad", role="adult", new_pin="1357")
    )

    assert User.objects.get(display_name="Dad").check_pin("1357")


def test_changing_a_person_keeps_the_pin_unless_a_new_one_is_given(owner_client, adult):
    address = f"/admin/people/user/{adult.pk}/change/"

    owner_client.post(address, _person_form(display_name="Mum", role="adult"))
    adult.refresh_from_db()
    assert adult.check_pin("2468")

    owner_client.post(address, _person_form(display_name="Mum", role="adult", new_pin="9753"))
    adult.refresh_from_db()
    assert adult.check_pin("9753")


def test_an_uploaded_photo_is_stored_as_a_small_square_face(owner_client):
    buffer = io.BytesIO()
    Image.new("RGB", (1200, 900), "teal").save(buffer, format="PNG")
    photo = SimpleUploadedFile("holiday.png", buffer.getvalue(), content_type="image/png")

    owner_client.post("/admin/people/user/add/", _person_form(photo=photo))

    emma = User.objects.get(display_name="Emma")
    with emma.photo.open() as stored:
        face = Image.open(stored)
        assert (face.format, face.size) == ("JPEG", (400, 400))


@pytest.mark.parametrize("change", [{"role": "child"}, {"is_active": ""}])
def test_the_only_adult_cannot_be_made_a_child_or_moved_out(owner_client, adult, change):
    form = _person_form(display_name="Mum", role="adult") | change
    if not form["is_active"]:
        del form["is_active"]  # an unticked box is simply not sent

    response = owner_client.post(f"/admin/people/user/{adult.pk}/change/", form)

    assert response.status_code == 200
    assert "Toto je jediný dospělý." in response.content.decode()
    adult.refresh_from_db()
    assert adult.is_adult and adult.is_active


def test_one_of_two_adults_can_be_moved_out(owner_client, adult):
    dad = make_person("Dad", User.Role.ADULT, "1357")
    form = _person_form(display_name="Dad", role="adult")
    del form["is_active"]

    owner_client.post(f"/admin/people/user/{dad.pk}/change/", form)

    dad.refresh_from_db()
    assert not dad.is_active


def test_people_cannot_be_deleted(owner_client, child):
    assert owner_client.get(f"/admin/people/user/{child.pk}/delete/").status_code == 403
    assert User.objects.filter(pk=child.pk).exists()


def test_devices_are_listed_and_removed_but_not_added_by_hand(owner_client, adult):
    device, _token = trust_device(name="Kitchen panel", trusted_by=adult)

    assert "Kitchen panel" in owner_client.get("/admin/people/device/").content.decode()
    assert owner_client.get("/admin/people/device/add/").status_code == 403

    owner_client.post(f"/admin/people/device/{device.pk}/change/", {"name": "Kitchen panel"})
    device.refresh_from_db()
    assert not device.is_active
