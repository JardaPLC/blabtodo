"""The Today screen, the sheet for marking a card done, Undo, and the finished tasks."""

import contextlib
from datetime import date

from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from household.backups import snapshot_if_due
from people.devices import trusted_device_required
from people.models import User

from . import cards, catalogue, picture_drafts
from .labels import day_heading, waiting_since
from .models import Completion, Room, Task


def _people():
    return list(User.objects.filter(is_active=True))


def _selected_face(request, people) -> User | None:
    """The person whose cards are being looked at, from `?face=<id>`. None means everyone's."""
    wanted = request.GET.get("face", "")
    return next((person for person in people if str(person.pk) == wanted), None)


def _cards_context(day: date, face: User | None) -> dict:
    waiting = cards.waiting_cards(day)
    if face is not None:
        # "Cards with my face on them": how someone who cannot read finds their own tasks.
        waiting = waiting.filter(faces=face)
    waiting = list(waiting)
    for task in waiting:
        task.waiting_since = waiting_since(task.next_card_date, day)
    return {"cards": waiting, "face": face}


@require_GET
@trusted_device_required
def today(request):
    day = cards.today()
    snapshot_if_due(day)
    people = _people()
    context = {
        "people": people,
        # The one person who can sign in to the management pages, to remind them how.
        "owner": User.objects.filter(is_superuser=True, is_active=True).first(),
        **_cards_context(day, _selected_face(request, people)),
    }
    return render(request, "tasks/today.html", context)


@require_GET
@trusted_device_required
def cards_fragment(request):
    """The card grid alone. The Today screen fetches it again every 30 seconds."""
    day = cards.today()
    snapshot_if_due(day)
    return render(
        request, "tasks/_cards.html", _cards_context(day, _selected_face(request, _people()))
    )


@require_http_methods(["GET", "POST"])
@trusted_device_required
def done(request, task_id):
    """GET: the sheet that asks who did it. POST: record it and return the refreshed cards."""
    day = cards.today()
    people = _people()
    face = _selected_face(request, people)
    task = get_object_or_404(
        Task.objects.select_related("room").prefetch_related("faces"), pk=task_id
    )

    if request.method == "GET":
        if not cards.is_waiting(task, day):
            return _after(request, day, face, gone=True)
        return _sheet(request, task, people, face, preselected=_preselected(task, face))

    try:
        card_date = date.fromisoformat(request.POST.get("card_date", ""))
    except ValueError:
        return _after(request, day, face, gone=True)

    chosen = set(request.POST.getlist("who"))
    who = [person for person in people if str(person.pk) in chosen]
    if not who:
        response = _sheet(request, task, people, face, preselected=set(), error=True)
        # The form asked for the cards to be replaced. Show the sheet again instead.
        response.headers["HX-Retarget"] = "#sheet"
        response.headers["HX-Reswap"] = "innerHTML"
        return response

    try:
        completion = cards.complete(
            task_id=task.pk,
            card_date=card_date,
            people=who,
            device=request.device,
            note=request.POST.get("note", "").strip()[:280],
        )
    except cards.CardGone:
        return _after(request, day, face, gone=True)
    return _after(request, day, face, completion=completion)


@require_POST
@trusted_device_required
def undo(request, completion_id):
    """The Undo bar: allowed for a short while on the device that recorded the completion."""
    day = cards.today()
    face = _selected_face(request, _people())
    completion = Completion.objects.filter(pk=completion_id).first()
    if completion is not None and cards.may_undo_from(completion, request.device):
        with contextlib.suppress(cards.CannotUndo):
            cards.undo(completion)
    return _after(request, day, face)


def _preselected(task: Task, face: User | None) -> set[int]:
    """Whose face is already ticked on the sheet, to save a tap where the answer is likely."""
    if face is not None:
        return {face.pk}
    faces = list(task.faces.all())
    return {faces[0].pk} if len(faces) == 1 else set()


def _sheet(request, task, people, face, *, preselected, error=False):
    context = {
        "task": task,
        "people": people,
        "face": face,
        "preselected": preselected,
        "error": error,
    }
    return render(request, "tasks/_sheet.html", context)


def _after(request, day, face, *, completion=None, gone=False):
    """The refreshed cards, the Undo bar or a notice, and the signal to close the sheet."""
    context = {**_cards_context(day, face), "completion": completion, "gone": gone}
    response = render(request, "tasks/_after_done.html", context)
    response.headers["HX-Retarget"] = "#cards"
    response.headers["HX-Reswap"] = "innerHTML"
    response.headers["HX-Trigger"] = "sheet-close"
    return response


@require_http_methods(["GET", "POST"])
@trusted_device_required
def from_qr(request, key):
    """
    Where a task's QR code leads. Asks before showing the card, so that a scan by accident
    changes nothing.
    """
    task = Task.objects.filter(qr_key=key, is_active=True).first()
    if task is None:
        return render(request, "tasks/qr.html", {"task": None}, status=404)
    day = cards.today()
    already_waiting = cards.is_waiting(task, day)
    if request.method == "POST":
        if not already_waiting:
            cards.show_today(task, day)
        return redirect("today")
    return render(request, "tasks/qr.html", {"task": task, "already_waiting": already_waiting})


# How many days with finished tasks one look at the archive shows. Older days load as the
# list is scrolled to its end.
ARCHIVE_DAYS = 7


@require_GET
@trusted_device_required
def archive(request):
    """Finished tasks, newest first, grouped by day. Everyone may look, children too."""
    day = cards.today()
    try:
        before = date.fromisoformat(request.GET.get("before", ""))
    except ValueError:
        before = None

    finished = Completion.objects.annotate(
        day=TruncDate("done_at", tzinfo=timezone.get_current_timezone())
    )
    if before is not None:
        finished = finished.filter(day__lt=before)
    days = list(
        finished.order_by("-day").values_list("day", flat=True).distinct()[: ARCHIVE_DAYS + 1]
    )
    more = len(days) > ARCHIVE_DAYS
    days = days[:ARCHIVE_DAYS]

    entries = (
        finished.filter(day__in=days)
        .select_related("task", "task__room")
        .prefetch_related("done_by")
        .order_by("-done_at")
    )
    groups = [{"day": shown, "heading": day_heading(shown, day), "entries": []} for shown in days]
    by_day = {group["day"]: group for group in groups}
    for entry in entries:
        by_day[entry.day]["entries"].append(entry)

    context = {"groups": groups, "next_before": days[-1] if more else None}
    if request.headers.get("HX-Request"):
        return render(request, "tasks/_archive_days.html", context)
    return render(request, "tasks/archive.html", context)


@require_http_methods(["GET", "POST"])
@trusted_device_required
def look(request):
    """
    The picture and font drafts. Whatever is chosen here applies to this device only, so
    that everyone can try them on their own screen before the family decides.
    """
    if request.method == "POST":
        pictures = request.POST.get("pictures", "")
        font = request.POST.get("font", "")
        response = redirect("look")
        if pictures in picture_drafts.PICTURE_SETS and font in picture_drafts.FONTS:
            response.set_cookie(
                picture_drafts.COOKIE_NAME,
                f"{pictures}.{font}",
                max_age=400 * 24 * 60 * 60,
                samesite="Lax",
            )
        return response

    # Every picture of the catalogue, as if each were a task or a room.
    tasks = [Task(picture=entry.key, names={"cs": str(entry.name)}) for entry in catalogue.TASKS]
    rooms = [Room(picture=entry.key, names={"cs": str(entry.name)}) for entry in catalogue.ROOMS]
    context = {
        "picture_sets": picture_drafts.PICTURE_SETS,
        "fonts": picture_drafts.FONTS,
        "sample_tasks": tasks,
        "sample_rooms": rooms,
    }
    return render(request, "tasks/look.html", context)
