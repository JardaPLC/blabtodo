"""
How gunicorn serves the app inside the container.

    gunicorn -c gunicorn.conf.py config.wsgi:application
"""

import socket

PORT = 8000


def listen_addresses(port: int = PORT) -> list[str]:
    """
    Listen on IPv6 and on IPv4.

    Both are needed. A name such as "homeassistant.local" usually resolves to an IPv6
    address first, and Home Assistant gives its containers IPv6 addresses. A server that
    listens on IPv4 only then looks dead to most browsers: the connection is accepted by
    the host and reset.

    On Linux one IPv6 socket normally serves IPv4 clients too (they then appear in the
    log as "::ffff:192.168.x.x"). Where the system keeps the two apart, both are opened.
    Where it has no IPv6 at all, IPv4 alone is used.
    """
    try:
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as probe:
            ipv6_only = bool(probe.getsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY))
            probe.bind(("::", 0))
    except OSError:
        return [f"0.0.0.0:{port}"]
    if ipv6_only:
        return [f"0.0.0.0:{port}", f"[::]:{port}"]
    return [f"[::]:{port}"]


bind = listen_addresses()

# One process with a few threads is plenty for a household and keeps memory use low.
workers = 1
threads = 4

# Requests are written to the log, where the host (Home Assistant, Docker) shows them.
accesslog = "-"
