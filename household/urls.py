from django.urls import path

from . import views

urlpatterns = [
    path("", views.hello, name="hello"),
    path("status/", views.status, name="status"),
    path("health/", views.health, name="health"),
]
