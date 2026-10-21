"""Form fields for autocomplete functionality."""

from typing import Any, ClassVar

from dal import autocomplete, forward
from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django_tomselect.app_settings import (
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownInput,
    TomSelectConfig,
)
from django_tomselect.forms import (
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
)
from django_tomselect.middleware import get_current_request
from django_tomselect.widgets import (
    TomSelectModelMultipleWidget,
    TomSelectModelWidget,
)
from research_vocabs.models import Concept

from .views import SCOPES, DatasetAutocompleteView, ProjectAutocompleteView


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
        **kwargs: Passed to the form field.

    Attributes:
        view_class: The record view that decides what is offered.
        kind: The kind of record, as it appears in the view's address.
        default_scope: The scope used when none is given.
        multiple: Whether the field chooses several records.
        label: The field's label when none is given.
        placeholder: The text shown before anything is chosen.
        count_text: The plural word shown beside the number of records chosen.
    """

    view_class = None
    kind = ""
    default_scope = "view"
    multiple = False
    label = ""
    placeholder = ""
    count_text = ""

    def __init__(self, *args, scope=None, **kwargs):
        scope = scope or self.default_scope
        if scope not in SCOPES:
            raise ValueError(f"scope must be one of {', '.join(SCOPES)}, not {scope!r}")
        self.scope = scope
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
            **plugins,
        )

    def get_bound_field(self, form, field_name):
        """Remember the form, which holds the record being edited and the request."""
        self.form = form
        self.field_name = field_name
        self.widget.field = self
        return super().get_bound_field(form, field_name)

    @property
    def user(self):
        """The person using the field: the form's request, else the current one."""
        request = getattr(self.form, "request", None) or get_current_request()
        return getattr(request, "user", None)

    def view(self):
        """Return the record view that serves the field's scope."""
        return self.view_class.for_scope(self.scope)()

    def offered(self):
        """Return the records the field offers the person using it."""
        return self.view().offered(self.user)

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
        """Return the records the field accepts: those it offers and those already stored."""
        records = self.view().base_queryset()
        return records.filter(
            Q(pk__in=self.offered().values("pk")) | Q(pk__in=self.stored_pks())
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


def record_fields(view_class, kind, *, label, one_label, any_label, count_text):
    """Make the single and the multiple field that choose one kind of record.

    Args:
        view_class: The record view that decides what is offered.
        kind: The kind of record, as it appears in the view's address.
        label: The label of both fields.
        one_label: The placeholder of the single field.
        any_label: The placeholder of the multiple field.
        count_text: The plural word shown beside the number the multiple field has chosen.

    Returns:
        The single field class and the multiple field class.
    """
    shared = {
        "view_class": view_class,
        "kind": kind,
        "label": label,
        "count_text": count_text,
    }
    noun = kind.capitalize()
    single = type(
        f"{noun}ChoiceField",
        (RecordChoiceFieldMixin, TomSelectModelChoiceField),
        {
            **shared,
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
