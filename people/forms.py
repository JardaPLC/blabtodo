from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

from .faces import prepare_face
from .models import User
from .pins import PIN_MAX_LENGTH, validate_pin


class PinField(forms.CharField):
    """A PIN, typed on a number pad and never shown back."""

    def __init__(self, **kwargs):
        kwargs.setdefault(
            "widget",
            forms.PasswordInput(
                attrs={
                    "class": "field",
                    "inputmode": "numeric",
                    "autocomplete": "off",
                    "maxlength": PIN_MAX_LENGTH,
                }
            ),
        )
        super().__init__(**kwargs)
        self.validators.append(validate_pin)


class FaceImageField(forms.ImageField):
    """A photo upload that comes out as a small square face picture."""

    def clean(self, data, initial=None):
        value = super().clean(data, initial)
        if isinstance(value, UploadedFile):
            return prepare_face(value)
        return value


class PinForm(forms.Form):
    pin = PinField(label=_("PIN"))


class SetupForm(forms.Form):
    """The first-run screen: creates the first adult, who is also the owner."""

    name = forms.CharField(
        label=_("Your name"),
        max_length=40,
        help_text=_("As the family calls you, for example Dad. It is shown under your face."),
        widget=forms.TextInput(attrs={"class": "field", "autocomplete": "off"}),
    )
    pin = PinField(
        label=_("PIN"),
        help_text=_("4 to 8 digits. You enter it to allow a new phone, tablet or PC."),
    )
    pin_again = PinField(label=_("PIN again"))
    password = forms.CharField(
        label=_("Password"),
        help_text=_(
            "For the management pages, where people and tasks are set up. "
            "Make it longer and harder to guess than the PIN."
        ),
        widget=forms.PasswordInput(attrs={"class": "field", "autocomplete": "new-password"}),
    )
    password_again = forms.CharField(
        label=_("Password again"),
        widget=forms.PasswordInput(attrs={"class": "field", "autocomplete": "new-password"}),
    )

    def clean(self):
        cleaned = super().clean()
        pin, pin_again = cleaned.get("pin"), cleaned.get("pin_again")
        if pin and pin_again and pin != pin_again:
            self.add_error("pin_again", _("The two PINs are not the same."))

        password, password_again = cleaned.get("password"), cleaned.get("password_again")
        if password:
            if password_again and password != password_again:
                self.add_error("password_again", _("The two passwords are not the same."))
            try:
                validate_password(password)
            except ValidationError as error:
                self.add_error("password", error)
        return cleaned

    def save(self) -> User:
        owner = User(
            display_name=self.cleaned_data["name"],
            role=User.Role.ADULT,
            is_staff=True,
            is_superuser=True,
        )
        owner.set_password(self.cleaned_data["password"])
        owner.set_pin(self.cleaned_data["pin"])
        owner.save()
        return owner


class PersonAdminForm(forms.ModelForm):
    """Adding and changing a family member in the management pages."""

    new_pin = PinField(
        label=_("New PIN"),
        required=False,
        help_text=_(
            "4 to 8 digits. Leave empty to keep the current PIN. "
            "Adults need a PIN; children do not."
        ),
    )
    photo = FaceImageField(
        label=_("Photo"),
        required=False,
        help_text=_("Any photo of the face. It is cropped to a square and made small."),
    )

    class Meta:
        model = User
        fields = ["display_name", "role", "colour", "photo", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["display_name"].required = True
        self.fields["is_active"].label = _("Lives here")
        self.fields["is_active"].help_text = _(
            "Untick instead of deleting: the person disappears from the screens, "
            "and what they did stays in the archive."
        )

    def clean(self):
        cleaned = super().clean()
        role, lives_here = cleaned.get("role"), cleaned.get("is_active")
        person = self.instance

        if role == User.Role.ADULT and not (cleaned.get("new_pin") or person.has_pin):
            self.add_error("new_pin", _("An adult needs a PIN."))

        stays_adult = role == User.Role.ADULT and lives_here
        if person.pk and person.is_adult and person.is_active and not stays_adult:
            other_adults = User.objects.filter(role=User.Role.ADULT, is_active=True).exclude(
                pk=person.pk
            )
            if not other_adults.exists():
                raise ValidationError(
                    _("This is the only adult. The household needs at least one.")
                )
        return cleaned

    def save(self, commit=True):
        person = super().save(commit=False)
        if self.cleaned_data.get("new_pin"):
            person.set_pin(self.cleaned_data["new_pin"])
        if not person.pk:
            # Family members do not sign in with a password. Only the owner has one.
            person.set_unusable_password()
        if commit:
            person.save()
        return person
