"""
Snapshots of the database inside the data folder.

SQLite cannot take a snapshot inside a transaction, and ordinary tests run inside one,
so these tests ask for real transactions.
"""

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest
from django.core.management import call_command

from household import backups
from tests.conftest import make_task

pytestmark = pytest.mark.django_db(transaction=True)

DAY = date(2026, 11, 2)


@pytest.fixture(autouse=True)
def clean_backups(settings, tmp_path, monkeypatch):
    """Each test gets an empty data folder and a snapshot memory that knows nothing."""
    settings.DATA_DIR = tmp_path
    settings.DATABASE_FILE = tmp_path / "db.sqlite3"
    settings.DAILY_SNAPSHOT = True
    monkeypatch.setattr(backups, "_checked_for", None)
    return tmp_path


def _names_of_snapshots(folder: Path) -> list[str]:
    return sorted(path.name for path in (folder / "backups").glob("*.sqlite3"))


def test_a_snapshot_is_a_complete_database_of_its_own(clean_backups):
    make_task("Zalít květiny")

    snapshot = backups.write_snapshot("manual")

    with sqlite3.connect(snapshot) as copy:
        names = [row[0] for row in copy.execute("SELECT names FROM tasks_task")]
    assert [json.loads(stored) for stored in names] == [{"cs": "Zalít květiny"}]
    assert not list((clean_backups / "backups").glob("*.part"))


def test_the_daily_snapshot_is_made_once_a_day(clean_backups):
    backups.snapshot_if_due(DAY)
    first = (clean_backups / "backups" / "daily-2026-11-02.sqlite3").stat().st_mtime_ns

    backups.snapshot_if_due(DAY)

    assert _names_of_snapshots(clean_backups) == ["daily-2026-11-02.sqlite3"]
    assert (clean_backups / "backups" / "daily-2026-11-02.sqlite3").stat().st_mtime_ns == first


def test_after_a_restart_the_days_snapshot_is_not_made_again(clean_backups, monkeypatch):
    backups.snapshot_if_due(DAY)
    first = (clean_backups / "backups" / "daily-2026-11-02.sqlite3").stat().st_mtime_ns
    monkeypatch.setattr(backups, "_checked_for", None)  # what a restart does

    backups.snapshot_if_due(DAY)

    assert (clean_backups / "backups" / "daily-2026-11-02.sqlite3").stat().st_mtime_ns == first


def test_only_the_newest_daily_snapshots_are_kept(clean_backups):
    for n in range(backups.DAILY_KEPT + 3):
        backups.snapshot_if_due(DAY + timedelta(days=n))

    kept = _names_of_snapshots(clean_backups)
    assert len(kept) == backups.DAILY_KEPT
    assert kept[0] == f"daily-{DAY + timedelta(days=3)}.sqlite3"


def test_daily_snapshots_can_be_switched_off(clean_backups, settings):
    settings.DAILY_SNAPSHOT = False

    backups.snapshot_if_due(DAY)

    assert not (clean_backups / "backups").exists()


def test_a_snapshot_that_cannot_be_written_does_not_break_the_page(clean_backups, monkeypatch):
    def fail(name):
        raise OSError("disk full")

    monkeypatch.setattr(backups, "write_snapshot", fail)

    backups.snapshot_if_due(DAY)  # must not raise


def test_before_an_update_the_database_is_copied_once_per_version(clean_backups, settings):
    settings.DATABASE_FILE.write_bytes(b"stands for an existing database")

    assert backups.snapshot_before_update("0.3.0") is not None
    assert backups.snapshot_before_update("0.3.0") is None
    assert backups.snapshot_before_update("0.4.0") is not None

    assert _names_of_snapshots(clean_backups) == ["before-0.3.0.sqlite3", "before-0.4.0.sqlite3"]


def test_a_fresh_installation_has_nothing_to_copy(clean_backups):
    assert backups.snapshot_before_update("0.3.0") is None
    assert not (clean_backups / "backups").exists()


def test_a_database_without_any_tables_yet_is_not_copied(clean_backups, settings, monkeypatch):
    settings.DATABASE_FILE.write_bytes(b"a file that was created but never set up")
    monkeypatch.setattr(backups.connection.introspection, "table_names", lambda: [])

    assert backups.snapshot_before_update("0.3.0") is None
    assert not (clean_backups / "backups").exists()


def test_a_version_name_cannot_escape_the_backups_folder(clean_backups, settings):
    settings.DATABASE_FILE.write_bytes(b"stands for an existing database")

    snapshot = backups.snapshot_before_update("../../evil")

    assert snapshot.parent == clean_backups / "backups"


def test_the_command_the_container_runs_before_updating(clean_backups, settings, capsys):
    settings.DATABASE_FILE.write_bytes(b"stands for an existing database")
    settings.APP_VERSION = "0.3.0"

    call_command("snapshot_before_update")

    assert _names_of_snapshots(clean_backups) == ["before-0.3.0.sqlite3"]
    assert "before-0.3.0" in capsys.readouterr().out
