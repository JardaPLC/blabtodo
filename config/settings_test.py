"""
Settings for the test suite.

Tests get their own throw-away data folder and do not depend on built styles or on a
developer's `.env` file.
"""

import atexit
import os
import shutil
import tempfile

_test_data_dir = tempfile.mkdtemp(prefix="blabtodo-test-")
atexit.register(shutil.rmtree, _test_data_dir, ignore_errors=True)
os.environ["BLABTODO_DATA_DIR"] = _test_data_dir

from .settings import *  # noqa: E402, F403

DEBUG = False
APP_VERSION = "test"
EXTRA_ALLOWED_HOSTS = []
TIME_ZONE = "Europe/Prague"

# The production storage needs `collectstatic` to have run; tests should not.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
