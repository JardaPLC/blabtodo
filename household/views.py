"""
Pages of the skeleton (milestone 0).

The hello page exists to prove the whole chain on real devices: styles, both languages,
page fragments fetched by htmx, in-page behaviour by Alpine.js, and the database.
The Today screen replaces it in milestone 1.
"""

import os
import time

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

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


def hello(request):
    context = {
        **_status_context(),
        "tiles": range(1, 7),
        "time_zone": settings.TIME_ZONE,
        "installation_id": settings.INSTALLATION_ID,
        "data_dir_writable": os.access(settings.DATA_DIR, os.W_OK),
    }
    return render(request, "household/hello.html", context)


def status(request):
    """The live part of the hello page, fetched again by htmx every 30 seconds."""
    return render(request, "household/_status.html", _status_context())


def health(request):
    """For the host (Home Assistant, Docker) to check that the app is alive."""
    ok = _database_ok()
    return JsonResponse(
        {"status": "ok" if ok else "error", "version": settings.APP_VERSION},
        status=200 if ok else 503,
    )
