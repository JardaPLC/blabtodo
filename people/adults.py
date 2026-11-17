"""
The adult view: editing tasks and rooms in the app, after an adult's PIN.

A correct PIN unlocks editing on this browser for a while, kept in its session. Every
page of the adult view moves the end further out, so it does not lock in the middle of
work, and "Finish" locks it at once.
"""

from datetime import timedelta
from functools import wraps
from urllib.parse import urlencode

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from .devices import trusted_device_required
from .models import User

UNLOCKED_FOR = timedelta(minutes=30)
_ADULT = "adult_id"
_UNTIL = "adult_until"


def unlock(request, adult: User) -> None:
    request.session.cycle_key()
    request.session[_ADULT] = adult.pk
    request.session[_UNTIL] = (timezone.now() + UNLOCKED_FOR).timestamp()


def lock(request) -> None:
    request.session.pop(_ADULT, None)
    request.session.pop(_UNTIL, None)


def current_adult(request) -> User | None:
    """The adult who unlocked editing on this browser, while it is still unlocked."""
    adult_id = request.session.get(_ADULT)
    until = request.session.get(_UNTIL)
    if adult_id is None or until is None or until < timezone.now().timestamp():
        return None
    return User.objects.filter(pk=adult_id, role=User.Role.ADULT, is_active=True).first()


def adult_required(view):
    """
    Let a view be used only by an adult who has entered their PIN on this browser.

    The device must be allowed as well. Anyone else is sent to the PIN pad and comes
    back to where they were going.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        adult = current_adult(request)
        if adult is None:
            target = reverse("unlock") + "?" + urlencode({"next": request.get_full_path()})
            if request.headers.get("HX-Request"):
                response = HttpResponse(status=204)
                response.headers["HX-Redirect"] = target
                return response
            return redirect(target)
        request.adult = adult
        request.session[_UNTIL] = (timezone.now() + UNLOCKED_FOR).timestamp()
        return view(request, *args, **kwargs)

    return trusted_device_required(wrapper)
