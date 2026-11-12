"""Things many tests need: an invented family and a browser on an allowed device."""

import pytest

from people.devices import COOKIE_NAME, trust_device
from people.models import User

ADULT_PIN = "2468"


def make_person(name: str, role: str, pin: str | None = None) -> User:
    person = User(display_name=name, role=role)
    if pin:
        person.set_pin(pin)
    person.set_unusable_password()
    person.save()
    return person


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
