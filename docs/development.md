# Development

How to run blabtodo on your own PC, change it, and release a new version. Written for
someone who knows Django. The reasons behind the choices are in [design.md](design.md).

## What you need

- **[uv](https://docs.astral.sh/uv/)**. It installs the right Python (3.13) and all
  packages by itself.
- **Git**, to fetch and publish the code.

Docker and Node.js are not needed. GitHub builds the container image, and the styles are
built by a standalone program that is downloaded on first use.

## First run

```
uv sync
copy .env.example .env
uv run python manage.py migrate
uv run python manage.py tailwind runserver
```

Open <http://127.0.0.1:8000>.

- `uv sync` creates the `.venv` folder with everything in it.
- `.env` holds settings for your PC only, and Git ignores it. The example turns on debug
  mode. Every setting is explained in `.env.example`.
- `tailwind runserver` is Django's `runserver` plus a watcher that rebuilds the
  stylesheet whenever a template changes. The first run downloads the Tailwind program
  (about 110 MB) into `.django_tailwind_cli/`.
- Your local database and uploads are in `data/`. Delete that folder to start fresh.

To try it from a phone on the same Wi-Fi, start the server on all addresses and open
your PC's IP address on the phone:

```
uv run python manage.py tailwind runserver 0.0.0.0:8000
```

### Windows: garbled characters or a `UnicodeDecodeError` during the build

Python on Windows reads the Tailwind program's messages in the system's old encoding.
The build still succeeds; only the messages are affected. Terminals opened inside
VS Code in this folder are already set up correctly (`.vscode/settings.json`). In other
terminals, set this once:

```
setx PYTHONUTF8 1
```

## Everyday commands

| To do this | Run |
|---|---|
| Start the app with live styles | `uv run python manage.py tailwind runserver` |
| Run the tests | `uv run pytest` |
| Check and fix code style | `uv run ruff check --fix .` then `uv run ruff format .` |
| Create a migration after changing a model | `uv run python manage.py makemigrations` |
| Compile translations after editing them | `uv run python tools/compile_translations.py` |
| Build the stylesheet once | `uv run python manage.py tailwind build` |
| Add a package | `uv add <name>` (for a tool used only in development: `uv add --dev <name>`) |

The same checks run on GitHub for every push (`.github/workflows/ci.yml`). There the
container image is also built and started, which is the only place the `Dockerfile` gets
tested.

## Where things are

| Folder | Contents |
|---|---|
| `config/` | Django settings and the top-level addresses |
| `household/` | Things that belong to the installation as a whole: the test page, the health check, the two middlewares |
| `people/` | The user model |
| `templates/` | The base layout shared by all pages. Each app keeps its own pages in its own `templates/` folder |
| `styles/app.css` | The Tailwind input file |
| `static/` | Files served as they are. `static/vendor/` holds htmx and Alpine.js at fixed versions |
| `locale/` | Translations |
| `tests/` | Tests |
| `tools/` | Small helper scripts for development |
| `ha-app/`, `repository.yaml` | What makes the repository installable in Home Assistant |

Two rules. The logic lives in plain functions that can be tested without a web request,
and the views stay thin. And when a new Django app folder is added, it must also be
added to the `COPY` lines in the `Dockerfile`.

## Translations

The texts in the code are English. Czech is in `locale/cs/LC_MESSAGES/django.po`.
English needs no file.

When you add or change a text in a template or in Python code:

1. Mark it for translation as usual (`{% translate %}`, `{% blocktranslate %}`, `gettext`).
2. Add the English text and its Czech translation to `django.po`.
3. Run `uv run python tools/compile_translations.py`.
4. Commit both `django.po` and `django.mo`.

The compiled `.mo` file is kept in the repository, so that installing the app needs no
translation tools. The tests fail when it is out of date.

Django's own `makemessages` and `compilemessages` need the GNU gettext programs, which
Windows does not have. That is why step 2 is done by hand and step 3 uses a small Python
script. If you do have gettext, `makemessages --locale cs` works as usual. GitHub runs
it on every push and fails when a text has no Czech translation.

## Releasing a version

A release is a Git tag. Everything else is automatic.

```
git tag v0.1.0
git push origin v0.1.0
```

The Release workflow then:

1. builds the image for Intel/AMD and for 64-bit ARM,
2. publishes it as `ghcr.io/<owner>/blabtodo:0.1.0` and `:latest`,
3. writes the version into `ha-app/config.yaml` on `main`.

Step 3 is what makes Home Assistant offer the update, and it happens only after the
image exists. Never change that version by hand.

Before tagging, add a short entry to `ha-app/CHANGELOG.md`. Home Assistant shows it
next to the update.

**Only once, after the very first release:** the image starts out private. On GitHub,
open your profile, then Packages, then blabtodo, then Package settings, and change the
visibility to Public. Home Assistant cannot download a private image.

## Keeping the repository public-safe

- Nothing personal goes in: no real names, faces, photos, home network addresses, or
  screenshots with real data. Examples and tests use an invented family.
- `data/` and `.env` are ignored by Git. Keep it that way.
- Every commit shows its author's email address to everyone. Use GitHub's private
  `noreply` address for commits (GitHub: Settings, Emails).
