"""Form fields for autocomplete functionality."""

from typing import Any, ClassVar

from dal import autocomplete, forward
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db.models import Q
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django_tomselect.app_settings import (
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
)
from django_tomselect.forms import (
    TomSelectChoiceField,
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
)
from django_tomselect.middleware import get_current_request
from django_tomselect.widgets import (
    TomSelectModelMultipleWidget,
    TomSelectModelWidget,
)
from literature.models import LiteratureItem
from research_vocabs.models import Concept

from fairdm.contrib.contributors.services.registries import Ror

from .views import (
    SCOPES,
    TAG_SCOPES,
    DatasetAutocompleteView,
    MeasurementAutocompleteView,
    OrganizationAutocompleteView,
    PersonAutocompleteView,
    ProjectAutocompleteView,
    SampleAutocompleteView,
    TagAutocompleteView,
)


class ConceptMixin:
    """Configure a model choice field to autocomplete the concepts of one vocabulary.

    Args:
        vocabulary: A vocabulary builder class or the dotted path to one.
        minimum_input_length: Characters typed before the autocomplete queries.
        **kwargs: Passed to the model choice field. ``queryset``, ``widget`` and
            ``label`` are filled in from the vocabulary when not given.

    Attributes:
        widget: The autocomplete widget class used when the caller passes none.
    """

    widget: ClassVar[type[Any]]

    def __init__(self, vocabulary, minimum_input_length=2, **kwargs):
        if isinstance(vocabulary, str):
            vocabulary = import_string(vocabulary)

        vocab_name = vocabulary._meta.name

        if "queryset" not in kwargs:
            kwargs["queryset"] = Concept.objects.filter(vocabulary__name=vocab_name)

        if "widget" not in kwargs:
            kwargs["widget"] = self.widget(
                url=reverse("autocomplete:concept"),
                forward=(forward.Const(vocab_name, "vocabulary"),),
                attrs={
                    "data-placeholder": f"Select {vocabulary.__name__}...",
                    "data-minimum-input-length": minimum_input_length,
                },
            )

        if "label" not in kwargs:
            kwargs["label"] = vocabulary.__name__

        super().__init__(**kwargs)


class ConceptSelect(ConceptMixin, forms.ModelChoiceField):
    """Select a single Concept with autocomplete.

    The field configures autocomplete for one vocabulary, given as a
    VocabularyBuilder class or a string path.

    Args:
        vocabulary: Either a VocabularyBuilder class or a string path to one
                   (e.g., "my_app.vocabularies.ScienceKeywords")
        minimum_input_length: Minimum characters before autocomplete triggers (default: 2)
        **kwargs: Standard ModelChoiceField arguments

    Attributes:
        widget: The autocomplete widget class used when the caller passes none.

    Example:
        from fairdm.contrib.autocomplete.fields import ConceptSelect
        from my_app.vocabularies import ScienceKeywords

        # Using a class
        field = ConceptSelect(vocabulary=ScienceKeywords)

        # Using a string with custom minimum input
        field = ConceptSelect(
            vocabulary="my_app.vocabularies.ScienceKeywords",
            minimum_input_length=3
        )
    """

    widget = autocomplete.ModelSelect2


class ConceptMultiSelect(ConceptMixin, forms.ModelMultipleChoiceField):
    """Select multiple Concepts with autocomplete.

    The field configures autocomplete for one vocabulary, given as a
    VocabularyBuilder class or a string path.

    Args:
        vocabulary: Either a VocabularyBuilder class or a string path to one
                   (e.g., "my_app.vocabularies.ScienceKeywords")
        minimum_input_length: Minimum characters before autocomplete triggers (default: 2)
        **kwargs: Standard ModelMultipleChoiceField arguments

    Attributes:
        widget: The autocomplete widget class used when the caller passes none.

    Example:
        from fairdm.contrib.autocomplete.fields import ConceptMultiSelect
        from my_app.vocabularies import ScienceKeywords

        # Using a class
        field = ConceptMultiSelect(vocabulary=ScienceKeywords)

        # Using a string with custom minimum input
        field = ConceptMultiSelect(
            vocabulary="my_app.vocabularies.ScienceKeywords",
            minimum_input_length=3
        )
    """

    widget = autocomplete.ModelSelect2Multiple


class RecordSelectMixin:
    """Draw the records a field has chosen the way the field sees them.

    A person cannot be shown the name of a record they may not see, so the field decides how
    each chosen record is labelled.
    """

    field = None

    def _get_selected_options(self, value, autocomplete_view):
        """Label the chosen records through the field, or as the library does with no field."""
        if self.field is None:
            return super()._get_selected_options(value, autocomplete_view)
        return self.field.selected_options(value)

    def get_context(self, name, value, attrs=None):
        """Tell the page which field's value the search should put first."""
        context = super().get_context(name, value, attrs)
        context["widget"]["prefer"] = getattr(self.field, "prefer", None)
        return context


class RecordSelectWidget(RecordSelectMixin, TomSelectModelWidget):
    """Choose one record."""


class RecordSelectMultipleWidget(RecordSelectMixin, TomSelectModelMultipleWidget):
    """Choose several records."""


class RecordFieldMixin:
    """What a field that chooses records of one kind shares, single or multiple.

    The field offers, and accepts, the records its view offers the person at its scope. It never
    asks django-tomselect to validate, which rebuilds the view from the current page's search
    and filter parameters.

    Args:
        scope: How much the person may be offered: ``"public"``, ``"view"`` or ``"edit"``.
            Defaults to the field's ``default_scope``.
        depends_on: The name of another field on the same form whose value the records must
            match, such as ``"dataset"`` for a sample. It must be a filter the view allows.
        prefer: The name of another field on the same form whose value the records should
            match to be listed first, in a group of their own. Unlike ``depends_on`` it never
            narrows what the field offers or accepts. It must be a filter the view allows.
        **kwargs: Passed to the form field.

    Attributes:
        view_class: The record view that decides what is offered.
        kind: The kind of record, as it appears in the view's address.
        scopes: The scopes the kind offers. A person or an organization is offered at one.
        default_scope: The scope used when none is given.
        multiple: Whether the field chooses several records.
        label: The field's label when none is given.
        placeholder: The text shown before anything is chosen.
        count_text: The plural word shown beside the number of records chosen.
        given_request: A request set on the field, for a field whose form carries none, such as
            a filter's.
    """

    view_class = None
    given_request = None
    kind = ""
    scopes = SCOPES
    default_scope = "view"
    multiple = False
    label = ""
    placeholder = ""
    count_text = ""

    def __init__(self, *args, scope=None, depends_on=None, prefer=None, **kwargs):
        scope = scope or self.default_scope
        if scope not in self.scopes:
            raise ValueError(
                f"scope must be one of {', '.join(self.scopes)}, not {scope!r}"
            )
        allowed = self.view_class.allowed_filter_fields
        if depends_on and depends_on not in allowed:
            raise ValueError(
                f"depends_on must be one of {', '.join(allowed) or 'none'}, not {depends_on!r}"
            )
        if prefer and prefer not in allowed:
            raise ValueError(
                f"prefer must be one of {', '.join(allowed) or 'none'}, not {prefer!r}"
            )
        self.scope = scope
        self.depends_on = depends_on
        self.prefer = prefer
        self.form = None
        self.field_name = ""
        kwargs.setdefault("label", self.label)
        super().__init__(*args, config=self.build_config(), **kwargs)

    def build_config(self):
        """Return the look and the address shared by the fields of every kind.

        Returns:
            The django-tomselect configuration of the field's widget.
        """
        plugins = {
            "plugin_dropdown_input": PluginDropdownInput(),
            "plugin_clear_button": PluginClearButton(),
        }
        attrs = {}
        if self.multiple:
            plugins["plugin_checkbox_options"] = PluginCheckboxOptions()
            attrs = {
                "data-none-text": str(self.placeholder),
                "data-count-text": str(self.count_text),
            }
        return TomSelectConfig(
            url=f"autocomplete:{self.kind}-{self.scope}",
            value_field="id",
            label_field="name",
            placeholder=self.placeholder,
            minimum_query_length=2,
            preload="focus",
            load_throttle=300,
            hide_selected=False,
            close_after_select=not self.multiple,
            highlight=True,
            loading_class="ts-loading",
            attrs=attrs,
            filter_by=(self.depends_on, self.depends_on) if self.depends_on else (),
            **plugins,
        )

    def get_bound_field(self, form, field_name):
        """Remember the form, which holds the record being edited and the request."""
        self.form = form
        self.field_name = field_name
        self.widget.field = self
        return super().get_bound_field(form, field_name)

    @property
    def request(self):
        """The request the field is used in: the form's, else the one it was given, else the current one."""
        return (
            getattr(self.form, "request", None)
            or self.given_request
            or get_current_request()
        )

    @property
    def user(self):
        """The person using the field, or none when it is used outside a request."""
        return getattr(self.request, "user", None)

    def view(self):
        """Return the record view that serves the field's scope."""
        return self.view_class.for_scope(self.scope)()

    def narrowing(self):
        """Return the lookup that the other field's submitted value puts on the records.

        Read from the bound form's data and never from the page's request.

        Returns:
            A dict for the view's ``offered()``, or ``None`` when the field depends on nothing
            or the other field has no value.
        """
        if not self.depends_on or self.form is None or not self.form.is_bound:
            return None
        value = self.form.data.get(self.form.add_prefix(self.depends_on))
        return None if value in (None, "") else {self.depends_on: value}

    def offered(self, narrowed=False):
        """Return the records the field offers the person using it.

        Args:
            narrowed: Whether to keep only the records that match the field it depends on.
                A value that cannot name a record offers nothing.

        Returns:
            A queryset of the offered records.
        """
        view = self.view()
        try:
            depends_on = self.narrowing() if narrowed else None
            return view.offered(self.user, depends_on=depends_on)
        except (TypeError, ValueError):
            return view.base_queryset().none()

    def stored_pks(self):
        """Return the primary keys the record being edited already holds in this field.

        Returns:
            A list, empty when the form edits no saved record.
        """
        instance = getattr(self.form, "instance", None)
        if instance is None or instance.pk is None:
            return []
        try:
            model_field = instance._meta.get_field(self.field_name)
        except FieldDoesNotExist:
            return []
        if model_field.many_to_many:
            return list(getattr(instance, self.field_name).values_list("pk", flat=True))
        stored = getattr(instance, model_field.attname)
        return [] if stored is None else [stored]

    def allowed(self):
        """Return the records the field accepts: those it offers and those already stored.

        A field used outside any request, in a script or a test, serves no person. It accepts
        what the form assigned to its ``queryset`` and nothing by default.
        """
        if self.request is None:
            return self.queryset
        records = self.view().base_queryset()
        return records.filter(
            Q(pk__in=self.offered(narrowed=True).values("pk"))
            | Q(pk__in=self.stored_pks())
        )

    def selected_options(self, value):
        """Describe the chosen records for the widget.

        A record the person may not see is labelled as private and never named. A value that is
        neither offered nor stored is not shown at all.

        Args:
            value: The chosen primary key, or the list of them.

        Returns:
            A list of ``{"value", "label"}`` dicts.
        """
        values = value if isinstance(value, (list, tuple)) else [value]
        values = [v for v in values if v not in (None, "")]
        if not values:
            return []
        try:
            chosen = list(self.allowed().filter(pk__in=values))
        except (TypeError, ValueError):
            return []
        offered = set(
            self.offered()
            .filter(pk__in=[o.pk for o in chosen])
            .values_list("pk", flat=True)
        )
        return [
            {
                "value": str(record.pk),
                "label": record.name
                if record.pk in offered
                else str(_("Private record")),
            }
            for record in chosen
        ]


class RecordChoiceFieldMixin(RecordFieldMixin):
    """Choose one record."""

    def clean(self, value):
        """Accept the record when the field offers it, or already holds it."""
        self.queryset = self.allowed()
        return forms.ModelChoiceField.clean(self, self._clean_value(value))


class RecordMultipleChoiceFieldMixin(RecordFieldMixin):
    """Choose several records."""

    multiple = True

    def clean(self, value):
        """Accept the records when the field offers each, or already holds it."""
        self.queryset = self.allowed()
        return forms.ModelMultipleChoiceField.clean(self, value)


def record_fields(
    view_class, kind, *, label, one_label, any_label, count_text, scopes=SCOPES
):
    """Make the single and the multiple field that choose one kind of record.

    Args:
        view_class: The record view that decides what is offered.
        kind: The kind of record, as it appears in the view's address.
        label: The label of both fields.
        one_label: The placeholder of the single field.
        any_label: The placeholder of the multiple field.
        count_text: The plural word shown beside the number the multiple field has chosen.
        scopes: The scopes the kind offers. The single field defaults to ``view`` where the
            kind offers it, and the multiple field to ``public``.

    Returns:
        The single field class and the multiple field class.
    """
    shared = {
        "view_class": view_class,
        "kind": kind,
        "label": label,
        "count_text": count_text,
        "scopes": scopes,
    }
    noun = kind.capitalize()
    single = type(
        f"{noun}ChoiceField",
        (RecordChoiceFieldMixin, TomSelectModelChoiceField),
        {
            **shared,
            "default_scope": "view" if "view" in scopes else scopes[0],
            "placeholder": one_label,
            "widget_class": RecordSelectWidget,
            "__doc__": f"Choose one {kind}.",
        },
    )
    multiple = type(
        f"{noun}MultipleChoiceField",
        (RecordMultipleChoiceFieldMixin, TomSelectModelMultipleChoiceField),
        {
            **shared,
            "placeholder": any_label,
            "default_scope": "public",
            "widget_class": RecordSelectMultipleWidget,
            "__doc__": f"Choose several {kind} records.",
        },
    )
    return single, multiple


ProjectChoiceField, ProjectMultipleChoiceField = record_fields(
    ProjectAutocompleteView,
    "project",
    label=_("Project"),
    one_label=_("Choose a project"),
    any_label=_("Any project"),
    count_text=_("projects"),
)
DatasetChoiceField, DatasetMultipleChoiceField = record_fields(
    DatasetAutocompleteView,
    "dataset",
    label=_("Dataset"),
    one_label=_("Choose a dataset"),
    any_label=_("Any dataset"),
    count_text=_("datasets"),
)
SampleChoiceField, SampleMultipleChoiceField = record_fields(
    SampleAutocompleteView,
    "sample",
    label=_("Sample"),
    one_label=_("Choose a sample"),
    any_label=_("Any sample"),
    count_text=_("samples"),
)
MeasurementChoiceField, MeasurementMultipleChoiceField = record_fields(
    MeasurementAutocompleteView,
    "measurement",
    label=_("Measurement"),
    one_label=_("Choose a measurement"),
    any_label=_("Any measurement"),
    count_text=_("measurements"),
)
PersonChoiceField, PersonMultipleChoiceField = record_fields(
    PersonAutocompleteView,
    "person",
    label=_("Person"),
    one_label=_("Choose a person"),
    any_label=_("Any person"),
    count_text=_("people"),
    scopes=("public",),
)
OrganizationChoiceField, OrganizationMultipleChoiceField = record_fields(
    OrganizationAutocompleteView,
    "organization",
    label=_("Organization"),
    one_label=_("Choose an organization"),
    any_label=_("Any organization"),
    count_text=_("organizations"),
    scopes=("public",),
)


class PublicationChoiceField(TomSelectModelChoiceField):
    """Choose one publication by searching its title, authors or DOI.

    Publications carry no visibility, so the field accepts any publication that exists. It never
    asks django-tomselect to validate, which rebuilds the view from the current page's search
    parameters.

    Args:
        **kwargs: Passed to the form field. ``label`` defaults to "Publication".
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("label", _("Publication"))
        config = TomSelectConfig(
            url="autocomplete:publication",
            value_field="id",
            label_field="title",
            placeholder=_("Choose a publication"),
            minimum_query_length=2,
            preload="focus",
            load_throttle=300,
            hide_selected=False,
            close_after_select=True,
            highlight=True,
            loading_class="ts-loading",
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(),
        )
        super().__init__(config=config, **kwargs)

    def clean(self, value):
        """Accept the publication when it exists."""
        self.queryset = LiteratureItem.objects.all()
        return forms.ModelChoiceField.clean(self, self._clean_value(value))


class TagsWidget(TomSelectModelMultipleWidget):
    """Choose tags, which are words and not records, so the chosen ones need no lookup."""

    def selected_tags(self, value):
        """Return the chosen tags as the options the control starts with.

        Args:
            value: The tags chosen, as a list or a single tag.

        Returns:
            A list of ``{"value", "label"}`` dicts.
        """
        tags = [value] if isinstance(value, str) else list(value or [])
        return [{"value": tag, "label": tag} for tag in tags]

    def _get_selected_options(self, value, autocomplete_view):
        """Show each chosen tag as itself."""
        return self.selected_tags(value)

    def get_context(self, name, value, attrs=None):
        """Show the chosen tags even where the page has no request to look them up in."""
        context = super().get_context(name, value, attrs)
        context["widget"]["selected_options"] = self.selected_tags(value)
        return context


class TagsField(forms.Field):
    """Choose tags, drawn as chips with a remove button, cleaned to a list of stripped words.

    With ``allow_new`` off the field accepts only tags in use on the records its scope offers
    the person. With it on, any tag that is not empty.

    Args:
        scope: How much the person may be offered: ``"public"`` or ``"view"``. Defaults to
            ``"view"``.
        allow_new: Whether a person may type a tag nobody has used.
        **kwargs: Passed to the form field.

    Attributes:
        given_request: A request set on the field, for a field whose form carries none, such as
            a filter's.
    """

    default_error_messages = {
        "invalid_choice": _(
            "Select a valid choice. %(value)s is not one of the available choices."
        ),
    }
    given_request = None

    def __init__(self, *, scope="view", allow_new=False, **kwargs):
        if scope not in TAG_SCOPES:
            raise ValueError(
                f"scope must be one of {', '.join(TAG_SCOPES)}, not {scope!r}"
            )
        self.scope = scope
        self.allow_new = allow_new
        kwargs.setdefault("label", _("Tags"))
        kwargs["widget"] = TagsWidget(
            config=TomSelectConfig(
                url=f"autocomplete:tag-{scope}",
                value_field="name",
                label_field="name",
                placeholder=_("Add a tag") if allow_new else _("Any tag"),
                minimum_query_length=2,
                preload="focus",
                load_throttle=300,
                hide_selected=True,
                close_after_select=False,
                highlight=True,
                loading_class="ts-loading",
                create=allow_new,
                plugin_remove_button=PluginRemoveButton(),
            )
        )
        super().__init__(**kwargs)

    @property
    def user(self):
        """The person using the field, or an anonymous user when it is used outside a request."""
        request = self.given_request or get_current_request()
        return getattr(request, "user", None) or AnonymousUser()

    def to_python(self, value):
        """Strip each tag, and drop the empty ones and the repeats.

        Args:
            value: The submitted tags, as a list or a single tag.

        Returns:
            A list of tags in the order given.
        """
        tags = [value] if isinstance(value, str) else value or []
        return list(dict.fromkeys(tag.strip() for tag in tags if tag and tag.strip()))

    def validate(self, value):
        """Refuse a tag nobody has used, unless the field lets a new one be added."""
        super().validate(value)
        if self.allow_new or not value:
            return
        offered = TagAutocompleteView.for_scope(self.scope)().offered(self.user)
        in_use = set(offered.filter(name__in=value).values_list("name", flat=True))
        for tag in value:
            if tag not in in_use:
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": tag},
                )

    def has_changed(self, initial, data):
        """Say whether the chosen tags differ from the initial ones, whatever their order."""
        return sorted(self.to_python(initial)) != sorted(self.to_python(data))


class RorChoiceField(TomSelectChoiceField):
    """Choose an organization from the Research Organization Registry by searching its name.

    The value is the ROR ID. The field accepts any value in the form of a ROR ID or its address
    and never asks the registry, so a form saves while ROR does not answer.

    Args:
        **kwargs: Passed to the form field. ``label`` defaults to "ROR ID".
    """

    default_error_messages = {
        "invalid_choice": _("Enter a ROR ID, such as https://ror.org/04z8jg394."),
    }

    def __init__(self, **kwargs):
        kwargs.setdefault("label", _("ROR ID"))
        config = TomSelectConfig(
            url="autocomplete:ror",
            value_field="value",
            label_field="label",
            placeholder=_("Search for an organization..."),
            minimum_query_length=3,
            preload=False,
            load_throttle=300,
            close_after_select=True,
            highlight=True,
            loading_class="ts-loading",
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(),
        )
        super().__init__(config=config, **kwargs)

    def clean(self, value):
        """Accept a ROR ID or its address, or nothing when the field is not required."""
        value = (value or "").strip()
        if not value:
            if self.required:
                raise ValidationError(self.error_messages["required"], code="required")
            return ""
        if Ror().identifier_in(value) is None:
            raise ValidationError(
                self.error_messages["invalid_choice"], code="invalid_choice"
            )
        return value
