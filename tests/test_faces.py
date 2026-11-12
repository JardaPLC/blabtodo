"""Uploaded photos become small square face pictures without the original's extra data."""

import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from people.faces import FACE_SIZE, MAX_UPLOAD_BYTES, prepare_face


def _upload(image: Image.Image, image_format: str = "JPEG", **save_options) -> SimpleUploadedFile:
    buffer = io.BytesIO()
    image.save(buffer, format=image_format, **save_options)
    return SimpleUploadedFile(f"photo.{image_format.lower()}", buffer.getvalue())


def test_a_large_photo_becomes_a_small_square_jpeg():
    result = prepare_face(_upload(Image.new("RGB", (1600, 1200), "navy")))

    face = Image.open(result)
    assert face.format == "JPEG"
    assert face.size == (FACE_SIZE, FACE_SIZE)
    assert result.name.endswith(".jpg")
    assert result.size < 50_000


def test_the_place_a_photo_was_taken_is_not_kept():
    exif = Image.Exif()
    exif[0x010F] = "Camera maker"  # any tag stands for "extra data", location included
    result = prepare_face(_upload(Image.new("RGB", (800, 800), "olive"), exif=exif))

    assert len(Image.open(result).getexif()) == 0


def test_a_photo_taken_sideways_is_turned_upright():
    # Left half red, right half blue, marked "rotate 90 degrees clockwise to view".
    image = Image.new("RGB", (800, 400), "red")
    image.paste("blue", (400, 0, 800, 400))
    exif = Image.Exif()
    exif[0x0112] = 6
    result = prepare_face(_upload(image, exif=exif, quality=95))

    face = Image.open(result).convert("RGB")
    top, bottom = face.getpixel((200, 20)), face.getpixel((200, 380))
    assert top[0] > 200 and top[2] < 60  # red is now at the top
    assert bottom[2] > 200 and bottom[0] < 60  # blue is now at the bottom


def test_a_see_through_picture_is_put_on_white():
    result = prepare_face(_upload(Image.new("RGBA", (600, 600), (0, 0, 0, 0)), "PNG"))

    assert Image.open(result).convert("RGB").getpixel((10, 10)) == (255, 255, 255)


def test_a_file_that_is_not_a_picture_is_refused():
    with pytest.raises(ValidationError):
        prepare_face(SimpleUploadedFile("notes.jpg", b"this is not a picture"))


def test_a_photo_over_the_size_limit_is_refused():
    upload = _upload(Image.new("RGB", (10, 10)))
    upload.size = MAX_UPLOAD_BYTES + 1

    with pytest.raises(ValidationError):
        prepare_face(upload)
