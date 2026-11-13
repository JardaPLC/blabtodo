"""
Snapshots of the database inside the data folder (docs/design.md, section 10.5).

They protect against mistakes: a bad update, something deleted by accident. They do not
protect against the disk failing, because they sit on the same disk. That is the job of
the host's backup, which copies the whole data folder elsewhere.
"""

import logging
from datetime import date
from pathlib import Path

from django.conf import settings
from django.db import DatabaseError, connection

logger = logging.getLogger(__name__)

DAILY_KEPT = 14
BEFORE_UPDATE_KEPT = 5

# The day for which the daily snapshot was last seen to exist. Kept in memory so that
# the folder is not looked at on every request.
_checked_for: date | None = None


def backups_dir() -> Path:
    return Path(settings.DATA_DIR) / "backups"


def write_snapshot(name: str) -> Path:
    """
    Write a complete, consistent copy of the database as backups/<name>.sqlite3.

    Uses SQLite's own `VACUUM INTO`, which is safe while the app is in use.
    """
    folder = backups_dir()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{name}.sqlite3"
    unfinished = folder / f"{name}.sqlite3.part"
    unfinished.unlink(missing_ok=True)
    with connection.cursor() as cursor:
        cursor.execute("VACUUM INTO %s", [str(unfinished)])
    unfinished.replace(target)
    return target


def _keep_newest(prefix: str, count: int) -> None:
    snapshots = sorted(
        backups_dir().glob(f"{prefix}*.sqlite3"), key=lambda path: path.stat().st_mtime
    )
    for old in snapshots[:-count]:
        old.unlink(missing_ok=True)


def snapshot_if_due(day: date) -> None:
    """
    Make today's snapshot if there is none yet. Called when the Today screen is fetched,
    so it happens on the first use of each day and needs no timer.

    A failure is logged and never gets in the way of showing the page.
    """
    global _checked_for
    if _checked_for == day or not settings.DAILY_SNAPSHOT:
        return
    try:
        if not (backups_dir() / f"daily-{day.isoformat()}.sqlite3").exists():
            write_snapshot(f"daily-{day.isoformat()}")
            _keep_newest("daily-", DAILY_KEPT)
        _checked_for = day
    except (DatabaseError, OSError):
        logger.exception("The daily database snapshot could not be written.")


def snapshot_before_update(version: str) -> Path | None:
    """
    Keep a copy of the database as it was before this version first started.

    Returns the snapshot, or None if there was nothing to copy or it already exists.
    """
    database = Path(settings.DATABASE_FILE)
    if not database.exists() or database.stat().st_size == 0:
        return None
    if "django_migrations" not in connection.introspection.table_names():
        # A database file with nothing in it yet: a first start, not an update.
        return None
    safe_version = "".join(char if char.isalnum() or char in ".-" else "-" for char in version)
    name = f"before-{safe_version}"
    if (backups_dir() / f"{name}.sqlite3").exists():
        return None
    snapshot = write_snapshot(name)
    _keep_newest("before-", BEFORE_UPDATE_KEPT)
    return snapshot
