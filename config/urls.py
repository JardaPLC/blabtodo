"""Top-level addresses. Each app lists its own pages in its own urls.py."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Provides the `set_language` address used by the language buttons.
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("household.urls")),
]
