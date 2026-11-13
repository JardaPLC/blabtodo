from django.urls import path

from . import views

urlpatterns = [
    path("check/", views.check, name="check"),
    path("status/", views.status, name="status"),
    path("health/", views.health, name="health"),
    path("media/<path:path>", views.media, name="media"),
]
