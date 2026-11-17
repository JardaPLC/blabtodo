"""
Which cards the Today screen shows: everyone's, one person's, or one room's.

One filter at a time. It lives in the address (`?face=2`, `?room=3`, `?room=none`), so a
small display in the kitchen can be pointed at the kitchen's address and stay there,
and the refresh, Done and Undo keep it.
"""

from dataclasses import dataclass

from django.db.models import QuerySet

from people.models import User

from .models import Room

PEOPLE = "people"
ROOMS = "rooms"
# `?room=none`: the tasks that belong to no room, such as going to the shop.
NO_ROOM = "none"


@dataclass(frozen=True)
class CardFilter:
    # Which row of buttons is shown: faces or rooms.
    by: str = PEOPLE
    face: User | None = None
    room: Room | None = None
    no_room: bool = False

    @property
    def is_active(self) -> bool:
        return self.face is not None or self.room is not None or self.no_room

    @property
    def query(self) -> str:
        """The part of the address that keeps this filter, starting with "?", or ""."""
        if self.face is not None:
            return f"?face={self.face.pk}"
        if self.room is not None:
            return f"?room={self.room.pk}"
        if self.no_room:
            return f"?room={NO_ROOM}"
        if self.by == ROOMS:
            return f"?by={ROOMS}"
        return ""

    def apply(self, tasks: QuerySet) -> QuerySet:
        if self.face is not None:
            # "Cards with my face on them": how someone who cannot read finds their own.
            return tasks.filter(faces=self.face)
        if self.room is not None:
            return tasks.filter(room=self.room)
        if self.no_room:
            return tasks.filter(room__isnull=True)
        return tasks


def from_request(request, people: list[User]) -> CardFilter:
    """The filter asked for in the address. Anything unknown means no filter."""
    face_id = request.GET.get("face", "")
    face = next((person for person in people if str(person.pk) == face_id), None)
    if face is not None:
        return CardFilter(by=PEOPLE, face=face)

    room_id = request.GET.get("room", "")
    if room_id == NO_ROOM:
        return CardFilter(by=ROOMS, no_room=True)
    if room_id.isdigit():
        room = Room.objects.filter(pk=int(room_id), is_active=True).first()
        if room is not None:
            return CardFilter(by=ROOMS, room=room)
        return CardFilter(by=ROOMS)

    by = ROOMS if request.GET.get("by") == ROOMS else PEOPLE
    return CardFilter(by=by)
