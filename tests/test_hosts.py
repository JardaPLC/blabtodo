"""Which addresses the app answers to (docs/design.md, section 13)."""

import pytest
from django.test import override_settings

from household.middleware import is_home_network_host


@pytest.mark.parametrize(
    "host",
    [
        "localhost",
        "homeassistant",
        "homeassistant.local",
        "HomeAssistant.Local",
        "homeassistant.local.",
        "nas.lan",
        "panel.home.arpa",
        "192.168.1.20",
        "10.0.0.5",
        "172.16.4.4",
        "127.0.0.1",
        "100.101.102.103",  # shared address space, used by some VPNs
        "[::1]",
        "[fe80::1]",
        "[fd12:3456:789a::1]",
    ],
)
def test_home_network_addresses_are_accepted(host):
    assert is_home_network_host(host)


@pytest.mark.parametrize(
    "host",
    [
        "",
        "example.com",
        "homeassistant.local.example.com",
        "8.8.8.8",
        "[2001:4860:4860::8888]",
        "fritz.box",  # ".box" is a public ending, so this router name must be configured
    ],
)
def test_public_addresses_are_refused(host):
    assert not is_home_network_host(host)


def test_configured_names_are_accepted():
    extra = ["tasks.example.org", ".family.example"]

    assert is_home_network_host("tasks.example.org", extra)
    assert is_home_network_host("panel.family.example", extra)
    assert is_home_network_host("family.example", extra)
    assert not is_home_network_host("other.example.org", extra)


def test_request_for_an_outside_name_is_refused(client):
    response = client.get("/health/", HTTP_HOST="evil.example.com")

    assert response.status_code == 400
    assert b"BLABTODO_ALLOWED_HOSTS" in response.content


@pytest.mark.django_db
@pytest.mark.parametrize(
    "host", ["192.168.1.20:8000", "homeassistant.local:8000", "homeassistant", "[::1]:8000"]
)
def test_request_for_a_home_network_name_is_served(client, host):
    assert client.get("/health/", HTTP_HOST=host).status_code == 200


@pytest.mark.django_db
@override_settings(EXTRA_ALLOWED_HOSTS=["tasks.example.org"])
def test_request_for_a_configured_name_is_served(client):
    assert client.get("/health/", HTTP_HOST="tasks.example.org").status_code == 200
    assert client.get("/health/", HTTP_HOST="other.example.org").status_code == 400
