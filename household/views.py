"""
Pages that belong to the installation as a whole.

- home: where Today will be. Until tasks exist it shows the family.
- check: the device check page, which proves the whole chain on a real device: styles,
  both languages, page fragments fetched by htmx, in-page behaviour by Alpine.js.
- media: uploaded files, served to allowed devices only.
- health: for the host to see that the app is alive.
"""

import os
import time

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.db import DatabaseError, connection
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils._os import safe_join
from django.views.decorators.http import require_GET

from people.devices import trusted_device_required
from people.models import User

_STARTED = time.monotonic()


def _database_ok() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return False
    return True


def _status_context() -> dict:
    return {
        "now": timezone.localtime(),
        "minutes_running": int((time.monotonic() - _STARTED) // 60),
        "database_ok": _database_ok(),
    }


@trusted_device_required
def home(request):
    context = {
        "people": User.objects.filter(is_active=True),
        # The one person who can sign in to the management pages, to remind them how.
        "owner": User.objects.filter(is_superuser=True, is_active=True).first(),
    }
    return render(request, "household/home.html", context)


@trusted_device_required
def check(request):
    context = {
        **_status_context(),
        "tiles": range(1, 7),
        "time_zone": settings.TIME_ZONE,
        "installation_id": settings.INSTALLATION_ID,
        "data_dir_writable": os.access(settings.DATA_DIR, os.W_OK),
    }
    return render(request, "household/check.html", context)


@trusted_device_required
def status(request):
    """The live part of the device check page, fetched again by htmx every 30 seconds."""
    return render(request, "household/_status.html", _status_context())


@require_GET
@trusted_device_required
def media(request, path):
    """An uploaded file. Faces and photos are private, so only allowed devices get them."""
    try:
        full_path = safe_join(settings.MEDIA_ROOT, path)
    except SuspiciousFileOperation as error:  # a path that tries to leave the media folder
        raise Http404 from error
    if not os.path.isfile(full_path):
        raise Http404
    response = FileResponse(open(full_path, "rb"))  # noqa: SIM115 - closed by the response
    response.headers["Cache-Control"] = "private, max-age=86400"
    return response


def health(request):
    """For the host (Home Assistant, Docker) to check that the app is alive."""
    ok = _database_ok()
    return JsonResponse(
        {"status": "ok" if ok else "error", "version": settings.APP_VERSION},
        status=200 if ok else 503,
    )
