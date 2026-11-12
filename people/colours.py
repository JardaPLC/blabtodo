"""The colours of a person's face circle, used when they have no photo."""

from django.utils.translation import gettext_lazy as _

# key: (name shown when choosing, Tailwind classes).
# The classes are written out in full so that Tailwind finds them in this file.
COLOURS = {
    "rose": (_("Pink"), "bg-rose-500 text-white"),
    "orange": (_("Orange"), "bg-orange-500 text-white"),
    "amber": (_("Yellow"), "bg-amber-400 text-stone-900"),
    "green": (_("Green"), "bg-green-600 text-white"),
    "teal": (_("Teal"), "bg-teal-600 text-white"),
    "sky": (_("Light blue"), "bg-sky-500 text-white"),
    "indigo": (_("Blue"), "bg-indigo-600 text-white"),
    "purple": (_("Purple"), "bg-purple-600 text-white"),
}

COLOUR_CHOICES = [(key, name) for key, (name, _classes) in COLOURS.items()]
DEFAULT_COLOUR = "green"
