from django.urls import path

from . import manage, views

urlpatterns = [
    path("", views.today, name="today"),
    path("cards/", views.cards_fragment, name="cards"),
    # A card's number is its task's number, because a task has at most one card.
    path("cards/<int:task_id>/done/", views.done, name="card-done"),
    path("cards/<int:task_id>/one-more/", views.one_more, name="card-one-more"),
    path("completions/<int:completion_id>/undo/", views.undo, name="completion-undo"),
    path("done/", views.archive, name="archive"),
    # Trying the picture and font drafts on this device, until the family has chosen.
    path("look/", views.look, name="look"),
    # Where a printed QR code leads. The key is random, so the address cannot be guessed.
    path("t/<str:key>/", views.from_qr, name="task-qr"),
    # The adult view: editing tasks and rooms in the app.
    path("manage/", manage.home, name="manage"),
    path("manage/tasks/", manage.task_list, name="manage-tasks"),
    path("manage/tasks/new/", manage.task_new, name="manage-task-new"),
    path("manage/tasks/<int:task_id>/", manage.task_edit, name="manage-task"),
    path("manage/tasks/<int:task_id>/show/", manage.task_show, name="manage-task-show"),
    path("manage/tasks/<int:task_id>/skip/", manage.task_skip, name="manage-task-skip"),
    path("manage/tasks/<int:task_id>/delete/", manage.task_delete, name="manage-task-delete"),
    path("manage/tasks/<int:task_id>/sticker/", manage.task_sticker, name="manage-task-sticker"),
    path("manage/rooms/", manage.room_list, name="manage-rooms"),
    path("manage/rooms/new/", manage.room_new, name="manage-room-new"),
    path("manage/rooms/<int:room_id>/", manage.room_edit, name="manage-room"),
    path(
        "manage/rooms/<int:room_id>/move/<str:direction>/",
        manage.room_move,
        name="manage-room-move",
    ),
    path("manage/rooms/<int:room_id>/delete/", manage.room_delete, name="manage-room-delete"),
]
