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

# Passwords are hashed quickly in tests. PINs keep their real hasher.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
    "people.hashers.PinHasher",
]
MEDIA_ROOT = os.path.join(_test_data_dir, "media")
EXTRA_ALLOWED_HOSTS = []
TIME_ZONE = "Europe/Prague"

# The production storage needs `collectstatic` to have run; tests should not.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
