"""Values that every template can use."""

from django.conf import settings


def app(request):
    return {"APP_VERSION": settings.APP_VERSION}
