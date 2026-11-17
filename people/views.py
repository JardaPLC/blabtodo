"""The first-run setup screen and the screen where an adult allows a new device."""

import math

from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .adults import lock
from .adults import unlock as unlock_adult_view
from .devices import (
    guess_device_name,
    household_is_set_up,
    remember_device,
    safe_next_url,
    trust_device,
    trusted_device_required,
)
from .forms import PinForm, SetupForm
from .pins import check_adult_pin, seconds_paused


def _device_name(request) -> str:
    return guess_device_name(request.headers.get("User-Agent", ""))


@require_http_methods(["GET", "POST"])
def setup(request):
    """Create the first adult. Open to anyone on the home network, but only until it is done."""
    if household_is_set_up():
        return redirect("today")

    form = SetupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            owner = form.save()
            _device, token = trust_device(name=_device_name(request), trusted_by=owner)
        response = redirect("today")
        remember_device(response, token)
        return response
    return render(request, "people/setup.html", {"form": form})


def _pin_pad_context(form, next_url, wrong_pin, paused) -> dict:
    return {
        "form": form,
        "next": next_url,
        "wrong_pin": wrong_pin,
        "paused": bool(paused),
        # A wait is told in whole minutes, or in seconds when it is under a minute.
        "wait_minutes": math.ceil(paused / 60) if paused >= 60 else 0,
        "wait_seconds": paused if paused < 60 else 0,
    }


@require_http_methods(["GET", "POST"])
@trusted_device_required
def unlock(request):
    """The PIN pad in front of the adult view. Same PINs, same pause after wrong tries."""
    next_url = safe_next_url(request, default="/manage/")
    wrong_pin = False
    paused = seconds_paused()
    form = PinForm(request.POST or None)
    if request.method == "POST" and not paused and form.is_valid():
        result = check_adult_pin(form.cleaned_data["pin"])
        if result.adult is not None:
            unlock_adult_view(request, result.adult)
            return redirect(next_url)
        paused = result.seconds_paused
        wrong_pin = True
    context = _pin_pad_context(form, next_url, wrong_pin, paused)
    return render(request, "people/unlock.html", context)


@require_http_methods(["POST"])
def finish(request):
    """Lock the adult view again and go back to Today."""
    lock(request)
    return redirect("today")


@require_http_methods(["GET", "POST"])
def trust(request):
    """Allow the device in hand, by an adult's PIN."""
    if not household_is_set_up():
        return redirect("setup")
    next_url = safe_next_url(request)
    if request.device is not None:
        return redirect(next_url)

    wrong_pin = False
    paused = seconds_paused()
    form = PinForm(request.POST or None)
    if request.method == "POST" and not paused and form.is_valid():
        result = check_adult_pin(form.cleaned_data["pin"])
        if result.adult is not None:
            _device, token = trust_device(name=_device_name(request), trusted_by=result.adult)
            response = redirect(next_url)
            remember_device(response, token)
            return response
        paused = result.seconds_paused
        wrong_pin = True

    context = _pin_pad_context(form, next_url, wrong_pin, paused)
    return render(request, "people/trust.html", context)
