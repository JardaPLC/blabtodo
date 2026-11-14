"""Things many tests need: an invented family and a browser on an allowed device."""

from datetime import date, datetime, time

import pytest
from django.conf import settings
from django.utils import timezone, translation

from people.devices import COOKIE_NAME, trust_device
from people.models import User
from tasks import cards
from tasks.models import Room, Task
from tasks.schedule import DAYS

ADULT_PIN = "2468"


def make_person(name: str, role: str, pin: str | None = None) -> User:
    person = User(display_name=name, role=role)
    if pin:
        person.set_pin(pin)
    person.set_unusable_password()
    person.save()
    return person


def make_room(name: str = "Kitchen", **fields) -> Room:
    return Room.objects.create(names={"cs": name}, **fields)


def make_task(name: str = "Water the plants", *, faces=(), **fields) -> Task:
    """A task whose first card is planned the way the app plans it. Daily unless told otherwise."""
    fields.setdefault("repeat", DAYS)
    fields.setdefault("start_date", cards.today())
    task = Task(names={"cs": name}, **fields)
    cards.plan_first_card(task)
    task.save()
    task.faces.set(faces)
    return task


def noon(day: date) -> datetime:
    """Midday on a given day, in the household's time zone."""
    return timezone.make_aware(datetime.combine(day, time(12)))


@pytest.fixture(autouse=True)
def default_language():
    """Start every test in the default language, whatever the test before it switched to."""
    translation.activate(settings.LANGUAGE_CODE)
    yield
    translation.activate(settings.LANGUAGE_CODE)


@pytest.fixture
def adult(db):
    return make_person("Mum", User.Role.ADULT, ADULT_PIN)


@pytest.fixture
def child(db):
    return make_person("Emma", User.Role.CHILD)


@pytest.fixture
def trusted_client(client, adult):
    """A browser on a device that an adult has already allowed."""
    _device, token = trust_device(name="Test device", trusted_by=adult)
    client.cookies[COOKIE_NAME] = token
    return client


@pytest.fixture
def owner_client(client, adult):
    """A browser signed in to the management pages as the household's owner."""
    adult.is_staff = adult.is_superuser = True
    adult.save()
    client.force_login(adult)
    return client
