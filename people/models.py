import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .colours import COLOUR_CHOICES, COLOURS, DEFAULT_COLOUR
from .hashers import PinHasher


def face_upload_path(instance, filename):
    # A random name: the address of a photo should not reveal whose it is.
    return f"faces/{uuid.uuid4().hex}.jpg"


class User(AbstractUser):
    """
    A family member.

    Nobody types a user name in everyday use: people are picked by face, and a device is
    allowed once by an adult's PIN (docs/design.md, section 2). The user name and password
    inherited from Django matter only for the owner, who signs in to the management pages.
    """

    class Role(models.TextChoices):
        ADULT = "adult", _("Adult")
        CHILD = "child", _("Child")

    display_name = models.CharField(
        _("name"), max_length=40, blank=True, help_text=_("Shown under the face.")
    )
    role = models.CharField(_("role"), max_length=10, choices=Role.choices, default=Role.CHILD)
    colour = models.CharField(
        _("colour"),
        max_length=20,
        choices=COLOUR_CHOICES,
        blank=True,
        help_text=_("The colour of the face when there is no photo."),
    )
    photo = models.ImageField(_("photo"), upload_to=face_upload_path, blank=True)
    pin_hash = models.CharField(max_length=128, blank=True, editable=False)

    class Meta(AbstractUser.Meta):
        verbose_name = _("person")
        verbose_name_plural = _("people")
        ordering = ["id"]

    def __str__(self):
        return self.display_name or self.username

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self._free_username()
        if not self.display_name:
            self.display_name = self.username
        if not self.colour:
            self.colour = self._next_colour()

        previous_photo = None
        if self.pk:
            previous_photo = (
                type(self).objects.filter(pk=self.pk).values_list("photo", flat=True).first()
            )
        super().save(*args, **kwargs)
        if previous_photo and previous_photo != self.photo.name:
            self.photo.storage.delete(previous_photo)

    @property
    def is_adult(self) -> bool:
        return self.role == self.Role.ADULT

    @property
    def initial(self) -> str:
        return str(self)[:1].upper()

    @property
    def colour_classes(self) -> str:
        return COLOURS.get(self.colour, COLOURS[DEFAULT_COLOUR])[1]

    @property
    def has_pin(self) -> bool:
        return bool(self.pin_hash)

    def set_pin(self, pin: str) -> None:
        self.pin_hash = make_password(pin, hasher=PinHasher.algorithm)

    def check_pin(self, pin: str) -> bool:
        return self.has_pin and check_password(pin, self.pin_hash)

    def _free_username(self) -> str:
        base = slugify(self.display_name) or "person"
        candidate, number = base, 2
        while type(self).objects.filter(username=candidate).exists():
            candidate = f"{base}-{number}"
            number += 1
        return candidate

    def _next_colour(self) -> str:
        used = set(type(self).objects.values_list("colour", flat=True))
        for key in COLOURS:
            if key not in used:
                return key
        return list(COLOURS)[type(self).objects.count() % len(COLOURS)]


class Device(models.Model):
    """
    A phone, tablet, PC or wall panel that an adult has allowed to use the app.

    The device holds a random token in a cookie. Only a fingerprint of the token is
    stored here, so reading the database does not let anyone pose as a device.
    """

    name = models.CharField(_("device name"), max_length=60)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    trusted_by = models.ForeignKey(
        User,
        verbose_name=_("allowed by"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(_("allowed on"), auto_now_add=True)
    last_seen_at = models.DateTimeField(_("last seen"), null=True, blank=True)
    is_active = models.BooleanField(
        _("allowed"), default=True, help_text=_("Untick to stop this device from using the app.")
    )

    class Meta:
        verbose_name = _("device")
        verbose_name_plural = _("devices")
        ordering = ["-last_seen_at"]

    def __str__(self):
        return self.name


class PinLock(models.Model):
    """
    How many wrong PINs were entered in a row, and until when PIN entry is paused.

    There is one row for the whole household. Behind the container's network all devices
    can look alike, so the pause cannot be kept per device.
    """

    failures = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.failures} wrong PINs in a row"
