"""Allowed devices: allowing one, recognising it again, and keeping others out."""

import hashlib
import secrets
from datetime import timedelta
from functools import wraps
from urllib.parse import urlencode

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _

from .models import Device, User

COOKIE_NAME = "blabtodo_device"
# Browsers keep a cookie for at most about 400 days. It is renewed while the device is in use.
COOKIE_AGE = int(timedelta(days=400).total_seconds())
# "Last seen" is written at most this often, not on every request.
SEEN_INTERVAL = timedelta(hours=1)


def _fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def household_is_set_up() -> bool:
    """True once the first adult exists. Until then every page leads to the setup screen."""
    return User.objects.filter(role=User.Role.ADULT, is_active=True).exists()


def trust_device(*, name: str, trusted_by: User | None) -> tuple[Device, str]:
    """Record a new allowed device. Returns it with the token to hand to the browser."""
    token = secrets.token_urlsafe(32)
    device = Device.objects.create(
        name=name,
        token_hash=_fingerprint(token),
        trusted_by=trusted_by,
        last_seen_at=timezone.now(),
    )
    return device, token


def find_device(token: str | None) -> Device | None:
    if not token:
        return None
    return Device.objects.filter(token_hash=_fingerprint(token), is_active=True).first()


def remember_device(response, token: str) -> None:
    response.set_cookie(COOKIE_NAME, token, max_age=COOKIE_AGE, httponly=True, samesite="Lax")


def guess_device_name(user_agent: str) -> str:
    """A first name for a newly allowed device. Adults can change it in the management pages."""
    agent = user_agent.lower()
    if "iphone" in agent:
        return "iPhone"
    if "ipad" in agent:
        return "iPad"
    if "android" in agent:
        return _("Android phone") if "mobile" in agent else _("Android tablet")
    if "windows" in agent:
        return _("Windows PC")
    if "macintosh" in agent:
        return "Mac"
    if "linux" in agent:
        return _("Linux PC")
    return _("Device")


def safe_next_url(request, default: str = "/") -> str:
    """Where to go after allowing a device: only ever back to a page of this app."""
    candidate = request.POST.get("next") or request.GET.get("next") or default
    if url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}):
        return candidate
    return default


def trusted_device_required(view):
    """
    Let a view be used only from an allowed device.

    Before the first adult exists, everything leads to the setup screen. After that, an
    unknown device is sent to the PIN screen and comes back to where it was going.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if getattr(request, "device", None) is not None:
            return view(request, *args, **kwargs)

        if not household_is_set_up():
            target = reverse("setup")
        else:
            target = reverse("trust") + "?" + urlencode({"next": request.get_full_path()})

        if request.headers.get("HX-Request"):
            # A fragment was asked for by a page that is already open, for example a wall
            # panel whose device has just been removed. Tell htmx to load the whole page.
            response = HttpResponse(status=204)
            response.headers["HX-Redirect"] = reverse("trust")
            return response
        return redirect(target)

    return wrapper
