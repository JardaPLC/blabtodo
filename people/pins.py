"""PINs: their format, checking them, and the pause after repeated wrong tries."""

import math
from dataclasses import dataclass
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import PinLock, User

PIN_MIN_LENGTH = 4
PIN_MAX_LENGTH = 8

# Four wrong tries cost nothing. The fifth starts a pause, and every further wrong try
# doubles it. A correct PIN clears the count.
FREE_TRIES = 4
FIRST_PAUSE = timedelta(minutes=1)
LONGEST_PAUSE = timedelta(hours=1)


def validate_pin(pin: str) -> None:
    well_formed = pin.isascii() and pin.isdigit()
    if not (well_formed and PIN_MIN_LENGTH <= len(pin) <= PIN_MAX_LENGTH):
        raise ValidationError(
            _("A PIN is %(shortest)d to %(longest)d digits."),
            code="pin_format",
            params={"shortest": PIN_MIN_LENGTH, "longest": PIN_MAX_LENGTH},
        )


def pause_after(failures: int) -> timedelta:
    """How long PIN entry stays paused once this many wrong PINs came in a row."""
    if failures <= FREE_TRIES:
        return timedelta(0)
    return min(FIRST_PAUSE * 2 ** (failures - FREE_TRIES - 1), LONGEST_PAUSE)


def seconds_paused(now=None) -> int:
    """Seconds until a PIN may be tried again; 0 when it may be tried now."""
    now = now or timezone.now()
    lock = PinLock.objects.filter(pk=1).first()
    if lock is None or lock.locked_until is None or lock.locked_until <= now:
        return 0
    return math.ceil((lock.locked_until - now).total_seconds())


@dataclass(frozen=True)
class PinCheck:
    adult: User | None
    # More than 0 means PIN entry is paused. When it was already paused before this try,
    # the PIN was not looked at.
    seconds_paused: int


def check_adult_pin(pin: str, now=None) -> PinCheck:
    """Find the adult this PIN belongs to, counting the try towards the pause."""
    now = now or timezone.now()
    with transaction.atomic():
        lock, _created = PinLock.objects.get_or_create(pk=1)
        if lock.locked_until and lock.locked_until > now:
            return PinCheck(None, math.ceil((lock.locked_until - now).total_seconds()))

        adult = _adult_with_pin(pin)
        if adult is not None:
            if lock.failures or lock.locked_until:
                lock.failures, lock.locked_until = 0, None
                lock.save()
            return PinCheck(adult, 0)

        lock.failures += 1
        pause = pause_after(lock.failures)
        lock.locked_until = now + pause if pause else None
        lock.save()
        return PinCheck(None, int(pause.total_seconds()))


def _adult_with_pin(pin: str) -> User | None:
    adults = User.objects.filter(role=User.Role.ADULT, is_active=True).exclude(pin_hash="")
    for adult in adults:
        if adult.check_pin(pin):
            return adult
    return None
