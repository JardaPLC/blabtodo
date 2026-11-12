"""Which network addresses the server listens on inside the container (gunicorn.conf.py)."""

import runpy
import socket
from pathlib import Path

import pytest

CONF_FILE = Path(__file__).resolve().parent.parent / "gunicorn.conf.py"


@pytest.fixture
def listen_addresses():
    return runpy.run_path(str(CONF_FILE))["listen_addresses"]


def _fake_socket(*, ipv6_only: bool = False, unavailable: bool = False):
    class FakeSocket:
        def __init__(self, family, kind):
            assert family == socket.AF_INET6
            if unavailable:
                raise OSError("Address family not supported by protocol")

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def getsockopt(self, level, option):
            return int(ipv6_only)

        def bind(self, address):
            assert address == ("::", 0)

    return FakeSocket


def test_one_ipv6_socket_serves_both_families_where_the_system_allows(
    listen_addresses, monkeypatch
):
    monkeypatch.setattr(socket, "socket", _fake_socket(ipv6_only=False))

    assert listen_addresses() == ["[::]:8000"]


def test_both_families_are_opened_where_the_system_keeps_them_apart(listen_addresses, monkeypatch):
    monkeypatch.setattr(socket, "socket", _fake_socket(ipv6_only=True))

    assert listen_addresses() == ["0.0.0.0:8000", "[::]:8000"]


def test_ipv4_alone_is_used_where_there_is_no_ipv6(listen_addresses, monkeypatch):
    monkeypatch.setattr(socket, "socket", _fake_socket(unavailable=True))

    assert listen_addresses() == ["0.0.0.0:8000"]


def test_the_configuration_never_listens_on_ipv4_only_when_ipv6_exists(listen_addresses):
    # Run against this machine's real network stack, whatever it is.
    addresses = listen_addresses()

    assert addresses
    if socket.has_ipv6 and addresses != ["0.0.0.0:8000"]:
        assert any(address.startswith("[::]") for address in addresses)
