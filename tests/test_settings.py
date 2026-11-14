"""The parts of the settings that have logic of their own."""

import os
from unittest import mock

from config import settings as project_settings


def test_env_file_fills_in_only_what_the_environment_lacks(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# a comment\n"
        "BLABTODO_TEST_A=from-file\n"
        "BLABTODO_TEST_B = 'quoted value'\n"
        "\n"
        "a line that is not a setting\n",
        encoding="utf-8",
    )

    with mock.patch.dict(os.environ, {"BLABTODO_TEST_A": "from-environment"}):
        os.environ.pop("BLABTODO_TEST_B", None)
        project_settings._load_env_file(env_file)

        assert os.environ["BLABTODO_TEST_A"] == "from-environment"
        assert os.environ["BLABTODO_TEST_B"] == "quoted value"


def test_missing_env_file_is_fine(tmp_path):
    project_settings._load_env_file(tmp_path / "does-not-exist")


def test_secret_key_is_created_once_and_kept(tmp_path, monkeypatch):
    monkeypatch.delenv("BLABTODO_SECRET_KEY", raising=False)

    first = project_settings._secret_key(tmp_path)

    assert len(first) >= 50
    assert (tmp_path / "secret_key").read_text(encoding="utf-8") == first
    assert project_settings._secret_key(tmp_path) == first


def test_configured_secret_key_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("BLABTODO_SECRET_KEY", "configured-key")

    assert project_settings._secret_key(tmp_path) == "configured-key"
    assert not (tmp_path / "secret_key").exists()


def test_everything_that_must_survive_lives_in_the_data_folder():
    # A backup is a copy of this one folder, so nothing may be kept outside it.
    data_dir = project_settings.DATA_DIR

    assert project_settings.DATABASE_FILE.parent == data_dir
    assert project_settings.MEDIA_ROOT.parent == data_dir


def test_errors_are_written_to_the_log_where_the_host_shows_them():
    import logging

    from django.conf import settings

    assert settings.LOGGING["root"]["handlers"] == ["console"]
    # Django's own messages, a failing page among them, reach that handler.
    assert logging.getLogger("django.request").propagate
