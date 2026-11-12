# blabtodo

A home task manager for one family. Household tasks sit in one shared queue that any
screen in the house can show, and marking a task done takes two taps.

- Every task is a big picture with large text, so children who cannot read yet can take part.
- Tasks repeat on a schedule, belong to rooms, and wait patiently until someone does them.
- Finished tasks fill one shared family jar. Nothing compares people with each other.
- It runs at home, on a Raspberry Pi with Home Assistant or any Docker host. Your data
  stays at home, in one folder.
- Czech and English, chosen per device.

**Status: early development.** Today you can set up your family and allow your devices.
The task screens are next. The whole plan is in [docs/design.md](docs/design.md).

## Install

| Where | Guide |
|---|---|
| Home Assistant OS (for example on a Raspberry Pi) | [docs/deploy/home-assistant.md](docs/deploy/home-assistant.md) |
| Any other Docker host (a NAS, a mini PC) | [docs/deploy/docker.md](docs/deploy/docker.md) |

blabtodo is meant for the home network only. Do not make it reachable from the internet.

## Develop

You need [uv](https://docs.astral.sh/uv/) and nothing else: no Docker, no Node.js.

```
uv sync
copy .env.example .env
uv run python manage.py migrate
uv run python manage.py tailwind runserver
```

Then open <http://127.0.0.1:8000>. Details, tests and how to release are in
[docs/development.md](docs/development.md).

## Licence

MIT, see [LICENSE](LICENSE). Work by others that blabtodo includes is listed in
[CREDITS.md](CREDITS.md).
