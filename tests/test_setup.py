"""The first-run screen, which creates the first adult."""

import pytest

from people.devices import COOKIE_NAME
from people.models import Device, User

pytestmark = pytest.mark.django_db

GOOD_ANSWERS = {
    "name": "Táta",
    "pin": "2468",
    "pin_again": "2468",
    "password": "correct horse battery",
    "password_again": "correct horse battery",
}


def test_a_fresh_installation_leads_everything_to_the_setup_screen(client):
    for address in ["/", "/check/", "/trust/"]:
        response = client.get(address)
        assert response.status_code == 302
        assert response.headers["Location"] == "/setup/"


def test_setup_creates_the_owner_and_allows_the_device_in_hand(client):
    response = client.post("/setup/", GOOD_ANSWERS, headers={"user-agent": "Mozilla (Windows NT)"})

    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    owner = User.objects.get()
    assert owner.display_name == "Táta"
    assert owner.username == "tata"
    assert owner.is_adult and owner.is_superuser and owner.is_staff
    assert owner.check_pin("2468")
    assert owner.check_password("correct horse battery")

    device = Device.objects.get()
    assert device.trusted_by == owner
    assert device.name == "Počítač s Windows"
    assert COOKIE_NAME in response.cookies

    # The same browser is now let in.
    home = client.get("/")
    assert home.status_code == 200
    assert "Táta" in home.content.decode()


def test_setup_closes_once_the_first_adult_exists(client, adult):
    assert client.get("/setup/").headers["Location"] == "/"

    response = client.post("/setup/", GOOD_ANSWERS)

    assert response.headers["Location"] == "/"
    assert User.objects.count() == 1


@pytest.mark.parametrize(
    ("changed", "message"),
    [
        ({"pin_again": "1357"}, "Zadané PINy se neshodují."),
        ({"pin": "12", "pin_again": "12"}, "PIN má 4 až 8 číslic."),
        ({"pin": "abcd", "pin_again": "abcd"}, "PIN má 4 až 8 číslic."),
        ({"password_again": "something else entirely"}, "Zadaná hesla se neshodují."),
    ],
)
def test_setup_explains_what_is_wrong(client, changed, message):
    response = client.post("/setup/", GOOD_ANSWERS | changed)

    assert response.status_code == 200
    assert message in response.content.decode()
    assert not User.objects.exists()


def test_setup_refuses_a_password_that_is_easy_to_guess(client):
    response = client.post(
        "/setup/", GOOD_ANSWERS | {"password": "12345678", "password_again": "12345678"}
    )

    assert response.status_code == 200
    assert not User.objects.exists()
