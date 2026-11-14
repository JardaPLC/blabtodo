"""
Django settings for blabtodo.

Everything that differs between installations comes from environment variables, and
every one of them is optional. During development they can be put in a `.env` file next
to manage.py (see `.env.example`).

Design background: docs/design.md.
"""

import hashlib
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file(path: Path) -> None:
    """Read KEY=VALUE lines from a file. Real environment variables keep priority."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


def _secret_key(data_dir: Path) -> str:
    """Use the configured key, or create one on first start and keep it in the data folder."""
    configured = os.environ.get("BLABTODO_SECRET_KEY")
    if configured:
        return configured
    key_file = data_dir / "secret_key"
    if key_file.is_file():
        key = key_file.read_text(encoding="utf-8").strip()
        if key:
            return key
    key = secrets.token_urlsafe(50)
    key_file.write_text(key, encoding="utf-8")
    return key


_load_env_file(BASE_DIR / ".env")

# One folder holds everything that must survive an update: the database, uploaded photos
# and backups. In the container it is /data.
DATA_DIR = Path(os.environ.get("BLABTODO_DATA_DIR") or BASE_DIR / "data").resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = _secret_key(DATA_DIR)
DEBUG = _env_flag("BLABTODO_DEBUG")

# A short fingerprint of this installation's data folder. It changes when the folder is
# replaced, which makes a restored backup recognisable. It reveals nothing about the key.
INSTALLATION_ID = hashlib.sha256(SECRET_KEY.encode()).hexdigest()[:8]

# A snapshot of the database is written into the data folder on the first use of each day.
DAILY_SNAPSHOT = True

# Shown on screen and in the health check. The container image sets it to the release number.
APP_VERSION = os.environ.get("BLABTODO_VERSION", "dev")

# Which host names the app answers to is decided by household.middleware.LanHostMiddleware.
# It accepts home-network addresses without any configuration and refuses everything else,
# so Django's own check is left open. Other names go in BLABTODO_ALLOWED_HOSTS.
ALLOWED_HOSTS = ["*"]
EXTRA_ALLOWED_HOSTS = _env_list("BLABTODO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = _env_list("BLABTODO_TRUSTED_ORIGINS")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_tailwind_cli",
    "people",
    "household",
    "tasks",
]

MIDDLEWARE = [
    "household.middleware.LanHostMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "household.middleware.DeviceLanguageMiddleware",
    "people.middleware.DeviceMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # The picture and font drafts this device chose to try.
                "tasks.picture_drafts.look",
                "household.context_processors.app",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database: one SQLite file in the data folder.
# WAL mode lets the screens read while something is being saved; IMMEDIATE transactions
# make two simultaneous writers wait for each other instead of failing.
DATABASE_FILE = DATA_DIR / "db.sqlite3"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATABASE_FILE,
        "OPTIONS": {
            "timeout": 20,
            "transaction_mode": "IMMEDIATE",
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
        },
    }
}

# The project has its own user model from the first migration, because Django makes it
# hard to switch later.
AUTH_USER_MODEL = "people.User"

# The first entry stores passwords (only the owner has one). The second stores PINs; why
# they are stored differently is explained in people/hashers.py.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "people.hashers.PinHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Languages. Czech is the default. English is the language the texts are written in, so
# only Czech needs a translation file. Which language a device shows is decided by
# household.middleware.DeviceLanguageMiddleware.
LANGUAGE_CODE = "cs"
LANGUAGES = [
    ("cs", "Čeština"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
USE_I18N = True

USE_TZ = True
TIME_ZONE = os.environ.get("BLABTODO_TIME_ZONE") or os.environ.get("TZ") or "Europe/Prague"


# Static files (styles, scripts, pictures). WhiteNoise serves them straight from the
# app, so no separate web server is needed.
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)  # WhiteNoise warns at every start when the folder is missing
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

# Uploaded files (photos, faces, own task pictures) live in the data folder.
MEDIA_URL = "media/"
MEDIA_ROOT = DATA_DIR / "media"

# Tailwind CSS is built by its standalone program; no Node.js is involved.
# The input file must stay outside STATICFILES_DIRS.
TAILWIND_CLI_VERSION = "4.3.5"
TAILWIND_CLI_SRC_CSS = "styles/app.css"
TAILWIND_CLI_DIST_CSS = "css/tailwind.css"

# The app sends no email. If something tries, it only prints to the log.
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

# Checks from `manage.py check --deploy` that do not apply, each for a stated reason.
SILENCED_SYSTEM_CHECKS = [
    # No email is sent, on purpose (see MAILERS above).
    "mail.E001",
    # Version 1 runs on plain HTTP inside the home network (docs/design.md, section 10.4).
    # Remove these four when HTTPS arrives in milestone 5.
    "security.W004",  # HSTS
    "security.W008",  # redirect to HTTPS
    "security.W012",  # secure-only session cookie
    "security.W016",  # secure-only CSRF cookie
]
