from django.urls import path

from . import views

urlpatterns = [
    path("", views.today, name="today"),
    path("cards/", views.cards_fragment, name="cards"),
    # A card's number is its task's number, because a task has at most one card.
    path("cards/<int:task_id>/done/", views.done, name="card-done"),
    path("completions/<int:completion_id>/undo/", views.undo, name="completion-undo"),
]
