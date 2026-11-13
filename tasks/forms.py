from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from . import catalogue
from .models import Room, Task

WEEKDAY_CHOICES = [
    (0, _("Monday")),
    (1, _("Tuesday")),
    (2, _("Wednesday")),
    (3, _("Thursday")),
    (4, _("Friday")),
    (5, _("Saturday")),
    (6, _("Sunday")),
]


class NamesWidget(forms.MultiWidget):
    """One text box per language of the app."""

    def __init__(self, attrs=None):
        boxes = {
            code: forms.TextInput(attrs={"placeholder": language, "size": 30})
            for code, language in settings.LANGUAGES
        }
        super().__init__(boxes, attrs)

    def decompress(self, value):
        names = value if isinstance(value, dict) else {}
        return [names.get(code, "") for code, _language in settings.LANGUAGES]


class NamesField(forms.MultiValueField):
    """A name in each language, stored as {"cs": "...", "en": "..."}. Empty ones are left out."""

    widget = NamesWidget

    def __init__(self, **kwargs):
        boxes = [forms.CharField(required=False, max_length=60) for _code in settings.LANGUAGES]
        kwargs.setdefault("required", False)
        super().__init__(fields=boxes, require_all_fields=False, **kwargs)

    def compress(self, values):
        names = {}
        for (code, _language), value in zip(settings.LANGUAGES, values or [], strict=False):
            if value and value.strip():
                names[code] = value.strip()
        return names


def _names_or_those_of_the_picture(form, entries_by_key) -> dict:
    """
    The names typed in, or the ones that belong to the chosen picture.

    A name in the default language is required one way or the other.
    """
    names = dict(form.cleaned_data.get("names") or {})
    entry = entries_by_key.get(form.cleaned_data.get("picture") or "")
    if entry is not None:
        names = entry.names() | names
    if not names.get(settings.LANGUAGE_CODE):
        form.add_error("names", _("Type a name, or choose a picture that has one."))
    return names


class RoomAdminForm(forms.ModelForm):
    names = NamesField(
        label=_("Name"), help_text=_("Leave empty to use the name that belongs to the picture.")
    )
    picture = forms.ChoiceField(label=_("Picture"), required=False)

    class Meta:
        model = Room
        fields = ["names", "picture", "position", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["picture"].choices = [("", "---------"), *catalogue.choices(catalogue.ROOMS)]

    def clean(self):
        cleaned = super().clean()
        cleaned["names"] = _names_or_those_of_the_picture(self, catalogue.ROOMS_BY_KEY)
        return cleaned


class TaskAdminForm(forms.ModelForm):
    names = NamesField(
        label=_("Name"), help_text=_("Leave empty to use the name that belongs to the picture.")
    )
    picture = forms.ChoiceField(label=_("Picture"), required=False)
    weekdays = forms.TypedMultipleChoiceField(
        label=_("Days of the week"),
        choices=WEEKDAY_CHOICES,
        coerce=int,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=_('Only for "On chosen days of the week".'),
    )
    faces = forms.ModelMultipleChoiceField(
        label=_("Meant for"),
        queryset=get_user_model().objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=_("Leave empty if anyone can do it. It is a hint: anyone may still do it."),
    )

    class Meta:
        model = Task
        fields = [
            "names",
            "picture",
            "hint",
            "room",
            "effort",
            "repeat",
            "interval",
            "weekdays",
            "day_of_month",
            "start_date",
            "end_date",
            "faces",
            "day_only",
            "is_active",
            "next_card_date",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["picture"].choices = [("", "---------"), *catalogue.choices(catalogue.TASKS)]
        self.fields["faces"].queryset = get_user_model().objects.filter(is_active=True)
        self.fields["room"].queryset = Room.objects.filter(is_active=True)
        self.fields["next_card_date"].help_text = _(
            "Leave empty to let the app work it out. Set a day to make the card appear then."
        )

    def clean(self):
        cleaned = super().clean()
        cleaned["names"] = _names_or_those_of_the_picture(self, catalogue.TASKS_BY_KEY)
        return cleaned
