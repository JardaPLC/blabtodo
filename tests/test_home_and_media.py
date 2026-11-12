"""The page that will become Today, and the protection of uploaded files."""

from pathlib import Path

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from people.models import User
from tests.conftest import make_person

pytestmark = pytest.mark.django_db


def test_home_shows_the_family_by_face(trusted_client, adult, child):
    html = trusted_client.get("/").content.decode()

    assert "Dnes" in html
    for person in (adult, child):
        assert person.display_name in html
        assert person.colour_classes in html


def test_someone_who_moved_out_is_not_shown(trusted_client):
    moved_out = make_person("Uncle", User.Role.CHILD)
    moved_out.is_active = False
    moved_out.save()

    assert "Uncle" not in trusted_client.get("/").content.decode()


def test_home_reminds_the_owner_of_the_user_name_for_the_management_pages(trusted_client, adult):
    adult.is_superuser = True
    adult.save()

    assert f">{adult.username}</strong>" in trusted_client.get("/").content.decode()


def test_a_face_photo_is_shown_instead_of_the_initial(trusted_client, child):
    child.photo = SimpleUploadedFile("face.jpg", b"jpeg bytes", content_type="image/jpeg")
    child.save()

    html = trusted_client.get("/").content.decode()

    assert f'src="/media/{child.photo.name}"' in html


def test_uploaded_files_are_served_to_allowed_devices_only(client, trusted_client, child):
    child.photo = SimpleUploadedFile("face.jpg", b"jpeg bytes", content_type="image/jpeg")
    child.save()
    address = f"/media/{child.photo.name}"

    allowed = trusted_client.get(address)
    assert allowed.status_code == 200
    assert b"".join(allowed.streaming_content) == b"jpeg bytes"
    assert "private" in allowed.headers["Cache-Control"]

    client.cookies.clear()
    refused = client.get(address)
    assert refused.status_code == 302
    assert refused.headers["Location"].startswith("/trust/")


def test_a_missing_file_is_simply_not_found(trusted_client):
    assert trusted_client.get("/media/faces/nothing.jpg").status_code == 404


def test_the_media_address_cannot_reach_files_outside_the_media_folder(trusted_client):
    # The secret key sits one folder above the media folder.
    assert (Path(settings.DATA_DIR) / "secret_key").is_file()

    assert trusted_client.get("/media/%2e%2e/secret_key").status_code == 404
