"""
The starter catalogue: common household tasks and rooms, each with a picture and a name
in every language the app ships with.

A task or room stores only the key of its picture. What is drawn for a key is decided in
one place (`tasks/templates/tasks/_picture.html`). For now that is the emoji given here,
as a stand-in until the picture set is chosen (docs/design.md, open questions). The keys
stay the same when the pictures change.
"""

from dataclasses import dataclass

from django.conf import settings
from django.utils import translation
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _

FALLBACK_EMOJI = "📋"


@dataclass(frozen=True)
class Entry:
    key: str
    name: Promise | str
    emoji: str
    # For tasks: how much work it usually is (1 small, 2 medium, 3 big).
    effort: int = 1
    # For tasks: the key of the room it usually belongs to, if any.
    room: str | None = None

    def names(self) -> dict[str, str]:
        """The name in every language of the app, ready to store on a task or room."""
        names = {}
        for code, _language in settings.LANGUAGES:
            with translation.override(code):
                names[code] = str(self.name)
        return names


TASKS = [
    Entry("water-plants", _("Water the plants"), "🌱", 1, "living-room"),
    Entry("load-dishwasher", _("Load the dishwasher"), "🍽️", 1, "kitchen"),
    Entry("empty-dishwasher", _("Empty the dishwasher"), "🥣", 1, "kitchen"),
    Entry("wash-dishes", _("Wash the dishes"), "🧽", 2, "kitchen"),
    Entry("set-table", _("Set the table"), "🍴", 1, "kitchen"),
    Entry("wipe-table", _("Wipe the table"), "🧼", 1, "kitchen"),
    Entry("cook", _("Cook"), "🍳", 3, "kitchen"),
    Entry("clean-fridge", _("Clean the fridge"), "🧊", 2, "kitchen"),
    Entry("take-out-rubbish", _("Take out the rubbish"), "🗑️", 1),
    Entry("sort-recycling", _("Sort the recycling"), "♻️", 1),
    Entry("bins-out", _("Put the bins out"), "🚛", 1),
    Entry("vacuum", _("Vacuum"), "🧹", 2),
    Entry("mop-floor", _("Mop the floor"), "💧", 2),
    Entry("dust", _("Dust"), "🧤", 1),
    Entry("clean-windows", _("Clean the windows"), "✨", 3),
    Entry("clean-bathroom", _("Clean the bathroom"), "🛁", 3, "bathroom"),
    Entry("clean-sink", _("Clean the sink"), "🚰", 1, "bathroom"),
    Entry("clean-toilet", _("Clean the toilet"), "🚽", 2, "toilet"),
    Entry("load-washing-machine", _("Load the washing machine"), "🧺", 1, "bathroom"),
    Entry("hang-laundry", _("Hang up the laundry"), "👕", 2),
    Entry("fold-laundry", _("Fold the laundry"), "🧦", 2),
    Entry("put-away-laundry", _("Put the laundry away"), "👚", 1),
    Entry("iron", _("Iron"), "👔", 3),
    Entry("change-bed-sheets", _("Change the bed sheets"), "🛏️", 2, "bedroom"),
    Entry("make-bed", _("Make the bed"), "🛌", 1, "bedroom"),
    Entry("tidy-room", _("Tidy the room"), "🧸", 2, "childrens-room"),
    Entry("tidy-toys", _("Put the toys away"), "🧩", 1, "childrens-room"),
    Entry("tidy-shoes", _("Tidy the shoes"), "👟", 1, "hall"),
    Entry("feed-pet", _("Feed the pet"), "🐾", 1),
    Entry("walk-dog", _("Walk the dog"), "🐕", 2),
    Entry("clean-litter", _("Clean the litter box"), "🐈", 1),
    Entry("shopping", _("Go shopping"), "🛒", 3),
    Entry("post", _("Take a parcel to the post office"), "📦", 2),
    Entry("pay-bills", _("Pay the bills"), "🧾", 1),
    Entry("mow-lawn", _("Mow the lawn"), "🌿", 3, "garden"),
    Entry("water-garden", _("Water the garden"), "🚿", 2, "garden"),
    Entry("rake-leaves", _("Rake the leaves"), "🍂", 3, "garden"),
    Entry("shovel-snow", _("Shovel the snow"), "❄️", 3),
    Entry("wash-car", _("Wash the car"), "🚗", 3, "garage"),
]

ROOMS = [
    Entry("kitchen", _("Kitchen"), "🍳"),
    Entry("living-room", _("Living room"), "🛋️"),
    Entry("bedroom", _("Bedroom"), "🛏️"),
    Entry("childrens-room", _("Children's room"), "🧸"),
    Entry("bathroom", _("Bathroom"), "🛁"),
    Entry("toilet", _("Toilet"), "🚽"),
    Entry("hall", _("Hall"), "🚪"),
    Entry("study", _("Study"), "💻"),
    Entry("laundry-room", _("Laundry room"), "🧺"),
    Entry("pantry", _("Pantry"), "🥫"),
    Entry("cellar", _("Cellar"), "📦"),
    Entry("balcony", _("Balcony"), "☀️"),
    Entry("garden", _("Garden"), "🌳"),
    Entry("garage", _("Garage"), "🚗"),
]

TASKS_BY_KEY = {entry.key: entry for entry in TASKS}
ROOMS_BY_KEY = {entry.key: entry for entry in ROOMS}


def choices(entries: list[Entry]) -> list[tuple[str, str]]:
    """For a drop-down: the picture next to the name, sorted by name in the current language."""
    labelled = [(entry.key, f"{entry.emoji}  {entry.name}") for entry in entries]
    return sorted(labelled, key=lambda choice: str(choice[1]).split("  ", 1)[1].casefold())
