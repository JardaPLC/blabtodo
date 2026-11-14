"""
Drafts to choose from: two picture sets and three fonts, tried on the real screens.

Each device chooses what it shows on the "Look" page; the choice is kept in a cookie on
that device only. Once the family has chosen, the winners become the only look and this
file goes away (docs/design.md, open questions 1 and 2).

The files are fetched once by `tools/fetch_drafts.py` and stored in `static/`.
"""

from django.utils.translation import gettext_lazy as _

COOKIE_NAME = "blabtodo_look"

PICTURE_SETS = {
    "emoji": _("Emoji (as until now)"),
    "fluent": _("Fluent Emoji: colourful"),
    "material": _("Material Symbols: on coloured tiles"),
}
FONTS = {
    "system": _("The device's own (as until now)"),
    "andika": "Andika",
    "nunito": "Nunito",
    "atkinson": "Atkinson Hyperlegible Next",
}
DEFAULT = ("emoji", "system")

# Picture key: (Fluent Emoji folder, Material Symbols name, tile colour).
# The Fluent folder names are those of github.com/microsoft/fluentui-emoji.
TASKS = {
    "water-plants": ("Seedling", "potted_plant", "green"),
    "load-dishwasher": ("Fork and knife with plate", "dishwasher_gen", "amber"),
    "empty-dishwasher": ("Bowl with spoon", "dishwasher", "amber"),
    "wash-dishes": ("Sponge", "wash", "amber"),
    "set-table": ("Fork and knife", "restaurant", "amber"),
    "wipe-table": ("Soap", "countertops", "amber"),
    "cook": ("Cooking", "skillet", "amber"),
    "clean-fridge": ("Ice", "kitchen", "amber"),
    "take-out-rubbish": ("Wastebasket", "delete", "stone"),
    "sort-recycling": ("Recycling symbol", "recycling", "lime"),
    "bins-out": ("Articulated lorry", "local_shipping", "lime"),
    "vacuum": ("Broom", "vacuum", "sky"),
    "mop-floor": ("Droplet", "mop", "sky"),
    "dust": ("Gloves", "cleaning_services", "sky"),
    "clean-windows": ("Sparkles", "window", "sky"),
    "clean-bathroom": ("Bathtub", "bathtub", "cyan"),
    "clean-sink": ("Potable water", "faucet", "cyan"),
    "clean-toilet": ("Toilet", "wc", "cyan"),
    "load-washing-machine": ("Basket", "local_laundry_service", "violet"),
    "hang-laundry": ("T-shirt", "laundry", "violet"),
    "fold-laundry": ("Socks", "apparel", "violet"),
    "put-away-laundry": ("Womans clothes", "checkroom", "violet"),
    "iron": ("Necktie", "iron", "violet"),
    "change-bed-sheets": ("Bed", "king_bed", "indigo"),
    "make-bed": ("Person in bed", "bed", "indigo"),
    "tidy-room": ("Teddy bear", "bedroom_child", "pink"),
    "tidy-toys": ("Puzzle piece", "toys_and_games", "pink"),
    "tidy-shoes": ("Running shoe", "footprint", "orange"),
    "feed-pet": ("Paw prints", "pet_supplies", "orange"),
    "walk-dog": ("Dog", "pets", "orange"),
    "clean-litter": ("Cat", "cleaning_bucket", "orange"),
    "shopping": ("Shopping cart", "shopping_cart", "rose"),
    "post": ("Package", "package_2", "rose"),
    "pay-bills": ("Receipt", "receipt_long", "rose"),
    "mow-lawn": ("Herb", "grass", "green"),
    "water-garden": ("Shower", "sprinkler", "green"),
    "rake-leaves": ("Fallen leaf", "eco", "green"),
    "shovel-snow": ("Snowflake", "snowflake", "slate"),
    "wash-car": ("Automobile", "local_car_wash", "slate"),
}
ROOMS = {
    "kitchen": ("Cooking", "kitchen", "amber"),
    "living-room": ("Couch and lamp", "weekend", "sky"),
    "bedroom": ("Bed", "bedroom_parent", "indigo"),
    "childrens-room": ("Teddy bear", "bedroom_child", "pink"),
    "bathroom": ("Bathtub", "bathtub", "cyan"),
    "toilet": ("Toilet", "wc", "cyan"),
    "hall": ("Door", "door_front", "orange"),
    "study": ("Laptop", "desk", "slate"),
    "laundry-room": ("Basket", "local_laundry_service", "violet"),
    "pantry": ("Canned food", "grocery", "amber"),
    "cellar": ("Package", "stairs", "stone"),
    "balcony": ("Sun", "balcony", "yellow"),
    "garden": ("Deciduous tree", "outdoor_garden", "green"),
    "garage": ("Automobile", "garage", "slate"),
}
# For a picture key that is not in the catalogue.
FALLBACK = ("Clipboard", "checklist", "stone")

# Written out in full, so that Tailwind finds the class names and builds them.
TILES = {
    "amber": "bg-amber-100 text-amber-700",
    "cyan": "bg-cyan-100 text-cyan-700",
    "green": "bg-green-100 text-green-700",
    "indigo": "bg-indigo-100 text-indigo-700",
    "lime": "bg-lime-100 text-lime-700",
    "orange": "bg-orange-100 text-orange-700",
    "pink": "bg-pink-100 text-pink-700",
    "rose": "bg-rose-100 text-rose-700",
    "sky": "bg-sky-100 text-sky-700",
    "slate": "bg-slate-200 text-slate-700",
    "stone": "bg-stone-200 text-stone-700",
    "violet": "bg-violet-100 text-violet-700",
    "yellow": "bg-yellow-100 text-yellow-700",
}


def chosen_look(request) -> tuple[str, str]:
    """The picture set and font this device chose, or the defaults."""
    value = request.COOKIES.get(COOKIE_NAME, "")
    pictures, _dot, font = value.partition(".")
    if pictures not in PICTURE_SETS:
        pictures = DEFAULT[0]
    if font not in FONTS:
        font = DEFAULT[1]
    return pictures, font


def look(request) -> dict:
    """Context processor: the chosen look, for `_picture.html` and `base.html`."""
    pictures, font = chosen_look(request)
    return {"look": {"pictures": pictures, "font": font}}


def picture_of(kind: str, key: str) -> dict:
    """The file name and tile colour of a picture. `kind` is "tasks" or "rooms"."""
    table = TASKS if kind == "tasks" else ROOMS
    if key in table:
        _fluent, _material, tile = table[key]
        return {"file": f"{kind}/{key}.svg", "tile": TILES[tile]}
    return {"file": "fallback.svg", "tile": TILES[FALLBACK[2]]}
