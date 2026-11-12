"""Turning an uploaded photo into a face picture."""

import io
import uuid

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageOps, UnidentifiedImageError

FACE_SIZE = 400
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


def prepare_face(upload) -> SimpleUploadedFile:
    """
    Return a small square JPEG made from the uploaded photo.

    A phone photo is several megabytes and may carry the place it was taken. The result
    is turned upright, cropped to a square around the upper middle (where a face usually
    is), shrunk, and saved without any of the original's extra data.
    """
    if upload.size > MAX_UPLOAD_BYTES:
        raise ValidationError(_("This photo is too large. The limit is 15 MB."))
    try:
        upload.seek(0)
        image = ImageOps.exif_transpose(Image.open(upload))
        if image.mode in ("RGBA", "LA", "P"):
            # Put see-through pictures on white instead of letting them turn black.
            image = image.convert("RGBA")
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            image = background
        else:
            image = image.convert("RGB")
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as error:
        raise ValidationError(_("This file is not a picture that can be read.")) from error

    image = ImageOps.fit(
        image, (FACE_SIZE, FACE_SIZE), Image.Resampling.LANCZOS, centering=(0.5, 0.4)
    )
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85, optimize=True)
    return SimpleUploadedFile(
        f"{uuid.uuid4().hex}.jpg", buffer.getvalue(), content_type="image/jpeg"
    )
