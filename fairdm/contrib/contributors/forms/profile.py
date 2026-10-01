"""The forms a person or an organization is edited with, and the field their lists are typed into."""

from crispy_forms.layout import Div, Fieldset, Layout
from dal import autocomplete
from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import FileExtensionValidator, URLValidator
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.widgets import ImageClearableFileInput

from fairdm.core import image_utils
from fairdm.forms import ModelForm

from ..models import Organization, Person
from ..profiles import language_names
from ..validators import ISO_639_1_CODES


class LinesField(forms.CharField):
    """A list of short entries typed one per line into a text area.

    The cleaned value is a list. Blank lines are dropped, surrounding spaces are trimmed and an
    entry typed twice is kept once, where it was first typed.

    Args:
        entry_validator: Called with each entry. A ``ValidationError`` it raises is reported
            for the first entry at fault, with the entry in the error's ``params``.
        max_entries: The most entries the field accepts.
        **kwargs: Passed to ``CharField``.

    Attributes:
        entry_validator: The per-entry validator, or None.
        max_entries: The most entries the field accepts.
    """

    default_error_messages = {
        "invalid_entry": _("“%(entry)s” is not valid."),
        "too_many": _("Enter no more than %(max)d lines."),
    }

    def __init__(self, *, entry_validator=None, max_entries=50, **kwargs):
        kwargs.setdefault("widget", forms.Textarea(attrs={"rows": 4}))
        super().__init__(**kwargs)
        self.entry_validator = entry_validator
        self.max_entries = max_entries

    def prepare_value(self, value):
        """Show a list one entry per line."""
        if value is None:
            return ""
        if isinstance(value, list | tuple):
            return "\n".join(value)
        return value

    def to_python(self, value):
        """Split the text into a list of distinct, trimmed entries.

        Args:
            value: The submitted text.

        Returns:
            The entries in the order first typed, empty when nothing was typed.
        """
        text = super().to_python(value)
        return list(
            dict.fromkeys(line.strip() for line in text.splitlines() if line.strip())
        )

    def validate(self, value):
        """Refuse an empty list when required, and the first entry the validator rejects.

        Args:
            value: The cleaned list.

        Raises:
            ValidationError: The field is required and empty, has too many entries, or an
                entry is not valid.
        """
        super().validate(value)
        if len(value) > self.max_entries:
            raise ValidationError(
                self.error_messages["too_many"],
                code="too_many",
                params={"max": self.max_entries},
            )
        if self.entry_validator is None:
            return
        for entry in value:
            try:
                self.entry_validator(entry)
            except ValidationError:
                raise ValidationError(
                    self.error_messages["invalid_entry"],
                    code="invalid_entry",
                    params={"entry": entry},
                ) from None


def language_choices():
    """List the ISO 639-1 languages by name in the active language.

    Returns:
        ``(code, name)`` pairs sorted by name. A code Django has no name for is shown as written.
    """
    named = [(code, language_names([code])[0]) for code in ISO_639_1_CODES]
    return sorted(named, key=lambda choice: choice[1].casefold())


class ProfileForm(ModelForm):
    """What the person and organization editing forms share.

    The editing page supplies the ``<form>`` tag and the buttons, so the crispy helper draws
    neither. ``sections`` groups the fields under headings, and ``get_layout`` draws them. A stored
    record can fail the model's validation on a field the form does not carry,
    such as a malformed identifier. Django refuses to attach that error to a missing field and
    raises, so it is reported on the form as a whole instead.

    Args:
        *args: Passed to ``ModelForm``.
        **kwargs: Passed to ``ModelForm``.

    Attributes:
        sections: ``(heading, rows)`` pairs, in page order. A row is a field name, or a tuple
            of field names drawn side by side on a wide screen.
    """

    sections: tuple = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_tag = False

    def get_layout(self):
        """Group the fields under the headings ``sections`` names.

        A field the form does not carry is left out, and a section left with no field is not
        drawn. A field no section names, as a portal's subclass may add, follows the last
        section.

        Returns:
            The crispy layout.
        """
        placed = set()
        layout = []
        for heading, rows in self.sections:
            drawn = []
            for row in rows:
                names = [row] if isinstance(row, str) else list(row)
                names = [name for name in names if name in self.fields]
                placed.update(names)
                if len(names) > 1:
                    drawn.append(
                        Div(*names, css_class="grid grid-cols-1 md:grid-cols-2 gap-x-6")
                    )
                else:
                    drawn.extend(names)
            if drawn:
                layout.append(Fieldset(heading, *drawn))
        layout.extend(name for name in self.fields if name not in placed)
        return Layout(*layout)

    def _update_errors(self, errors):
        """Move errors the model raised for a field this form lacks to the form's own errors.

        Args:
            errors: The ``ValidationError`` from the model's validation.
        """
        if hasattr(errors, "error_dict"):
            kept = {}
            for field, field_errors in errors.error_dict.items():
                target = field if field in self.fields else NON_FIELD_ERRORS
                kept.setdefault(target, []).extend(field_errors)
            errors = ValidationError(kept)
        super()._update_errors(errors)


class PersonProfileForm(ProfileForm):
    """The page where a person edits their own profile.

    A portal adds or drops fields by subclassing this form and naming the subclass in
    ``FAIRDM_PROFILE_FORMS``.

    Args:
        *args: Passed to ``ModelForm``.
        **kwargs: Passed to ``ModelForm``.

    Attributes:
        image: The photo. Ticking the clear box removes it.
        first_name: The given name, as citations use it.
        last_name: The family name, as citations use it.
        name: The name the person is publicly known by.
        alternative_names: Other names, one per line.
        profile: The biography.
        links: Web addresses, one per line.
        lang: The languages the person works in.
    """

    image = forms.ImageField(
        required=False,
        label=_("Photo"),
        help_text=format_lazy(
            _("JPEG, PNG or WebP, up to {size} MB."),
            size=image_utils.MAX_IMAGE_UPLOAD_BYTES // (1024 * 1024),
        ),
        validators=[
            image_utils.validate_image_file_size,
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
        ],
        widget=ImageClearableFileInput(
            thumbnail_options={"size": (150, 150), "crop": True}
        ),
    )
    alternative_names = LinesField(
        required=False,
        label=_("Alternative names"),
        help_text=_("Other names you publish under, one per line."),
    )
    links = LinesField(
        required=False,
        label=_("Links"),
        help_text=_("Web addresses of your other profiles, one per line."),
        entry_validator=URLValidator(schemes=["http", "https"]),
        error_messages={
            "invalid_entry": _(
                "“%(entry)s” is not a web address. Start it with http:// or https://."
            ),
        },
    )
    lang = forms.MultipleChoiceField(
        required=False,
        label=_("Languages"),
        help_text=_("The languages you work in."),
    )

    class Meta:
        model = Person
        fields = [
            "image",
            "first_name",
            "last_name",
            "name",
            "alternative_names",
            "profile",
            "links",
            "lang",
        ]
        labels = {
            "first_name": _("Given name"),
            "last_name": _("Family name"),
            "name": _("Display name"),
            "profile": _("Biography"),
        }
        help_texts = {
            "first_name": _("Used with your family name in citations."),
            "last_name": _("Used with your given name in citations."),
            "name": _(
                "The name you are publicly known by, as it appears on your credits."
            ),
            "profile": _("A few lines about your research. Markdown is supported."),
        }

    sections = (
        (_("Name"), [("first_name", "last_name"), "name", "alternative_names"]),
        (_("About you"), ["image", "profile", "lang"]),
        (_("Elsewhere online"), ["links"]),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "lang" in self.fields:
            self.fields["lang"].choices = language_choices()

    def clean_lang(self):
        """Keep each language once, in the order chosen."""
        return list(dict.fromkeys(self.cleaned_data["lang"]))


class OrganizationProfileForm(ProfileForm):
    """The page where an organization's owner or an administrator edits its profile.

    The website and the other links are two fields over the one stored list of links, the
    website first. A portal adds or drops fields by subclassing this form and naming the
    subclass in ``FAIRDM_PROFILE_FORMS``.

    Args:
        *args: Passed to ``ModelForm``.
        **kwargs: Passed to ``ModelForm``.

    Attributes:
        image: The logo. Ticking the clear box removes it.
        name: The organization's name.
        alternative_names: Other names, one per line.
        parent: The organization this one is part of. The organization itself and any
            organization beneath it are refused.
        website: The first stored link. Clearing it promotes the next link on reopening.
        links: The other web addresses, one per line.
    """

    image = forms.ImageField(
        required=False,
        label=_("Logo"),
        help_text=format_lazy(
            _("JPEG, PNG or WebP, up to {size} MB."),
            size=image_utils.MAX_IMAGE_UPLOAD_BYTES // (1024 * 1024),
        ),
        validators=[
            image_utils.validate_image_file_size,
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
        ],
        widget=ImageClearableFileInput(
            thumbnail_options={"size": (150, 150), "crop": True}
        ),
    )
    alternative_names = LinesField(
        required=False,
        label=_("Alternative names"),
        help_text=_("Other names the organization is known by, one per line."),
    )
    parent = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        label=_("Part of"),
        help_text=_("The organization this one belongs to, if any."),
        widget=autocomplete.ModelSelect2(url="autocomplete:organization"),
    )
    website = forms.CharField(
        required=False,
        label=_("Website"),
        help_text=_("The organization's own web address."),
        validators=[
            URLValidator(
                schemes=["http", "https"],
                message=_("Enter a web address starting with http:// or https://."),
            )
        ],
    )
    links = LinesField(
        required=False,
        label=_("Other links"),
        help_text=_(
            "Web addresses of other pages about the organization, one per line."
        ),
        entry_validator=URLValidator(schemes=["http", "https"]),
        error_messages={
            "invalid_entry": _(
                "“%(entry)s” is not a web address. Start it with http:// or https://."
            ),
        },
    )

    class Meta:
        model = Organization
        fields = [
            "image",
            "name",
            "alternative_names",
            "type",
            "parent",
            "city",
            "country",
            "profile",
            "website",
            "links",
        ]
        labels = {
            "name": _("Name"),
            "type": _("Type"),
            "city": _("City"),
            "country": _("Country"),
            "profile": _("Description"),
        }
        help_texts = {
            "name": _("The name the organization is publicly known by."),
            "profile": _(
                "A few lines about what the organization does. Markdown is supported."
            ),
        }

    sections = (
        (_("Identity"), ["image", "name", "alternative_names", ("type", "parent")]),
        (_("Location"), [("city", "country")]),
        (_("About"), ["profile"]),
        (_("Online"), ["website", "links"]),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        stored = self.instance.links or []
        if "website" in self.fields:
            self.initial["website"] = stored[0] if stored else ""
            stored = stored[1:]
        self.initial["links"] = stored

    def clean(self):
        """Store the website first among the links, and no link twice."""
        cleaned = super().clean()
        if "website" in cleaned and "links" in cleaned:
            website = [cleaned["website"]] if cleaned["website"] else []
            cleaned["links"] = list(dict.fromkeys([*website, *cleaned["links"]]))
        return cleaned
