"""Request middleware: which addresses the app answers to, and which language a device sees."""

import ipaddress

from django.conf import settings
from django.http import HttpResponseBadRequest
from django.http.request import split_domain_port
from django.utils import translation

# Name endings that can only be looked up inside a home network, never on the public internet.
LOCAL_SUFFIXES = (
    ".local",
    ".lan",
    ".home",
    ".internal",
    ".home.arpa",
    ".localdomain",
    ".localhost",
)


def is_home_network_host(host: str, extra_allowed: list[str] | None = None) -> bool:
    """
    Decide whether a request for this host name may be served.

    Accepted without any configuration:
    - numeric addresses that are not public internet addresses (192.168.x.x, 10.x.x.x, ...),
    - single-word names such as "homeassistant" or "localhost",
    - names with a local-only ending such as "homeassistant.local".

    Any other name must be listed in BLABTODO_ALLOWED_HOSTS. Refusing unknown public names
    is what stops an outside website from reaching the app through the visitor's browser
    (a "DNS rebinding" attack).
    """
    host = host.lower().rstrip(".")
    if not host:
        return False

    for allowed in extra_allowed or []:
        allowed = allowed.lower()
        if allowed == "*" or host == allowed:
            return True
        if allowed.startswith(".") and (host.endswith(allowed) or host == allowed[1:]):
            return True

    try:
        address = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        pass
    else:
        return not address.is_global

    if "." not in host:
        return True
    return host.endswith(LOCAL_SUFFIXES)


class LanHostMiddleware:
    """Refuse requests that were not addressed to a home-network name or address."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host, _port = split_domain_port(request.get_host())
        if not is_home_network_host(host, settings.EXTRA_ALLOWED_HOSTS):
            return HttpResponseBadRequest(
                "blabtodo answers only to home-network addresses. "
                "To use this name, add it to BLABTODO_ALLOWED_HOSTS.",
                content_type="text/plain; charset=utf-8",
            )
        return self.get_response(request)


class DeviceLanguageMiddleware:
    """
    Show the language chosen on this device, and the household default otherwise.

    The choice is stored in a cookie by Django's `set_language` view. The browser's own
    language preference is deliberately ignored: a device shows the default language
    until someone changes it on that device (docs/design.md, section 4).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if language not in {code for code, _name in settings.LANGUAGES}:
            language = settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = language
        response = self.get_response(request)
        response.headers.setdefault("Content-Language", language)
        return response
