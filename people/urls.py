from django.urls import path

from . import views

urlpatterns = [
    path("setup/", views.setup, name="setup"),
    path("trust/", views.trust, name="trust"),
    path("manage/unlock/", views.unlock, name="unlock"),
    path("manage/finish/", views.finish, name="finish"),
]
