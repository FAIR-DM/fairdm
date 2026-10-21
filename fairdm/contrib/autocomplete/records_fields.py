"""SKETCH ONLY. Ready-made autocomplete fields for records, people and organizations.

Untested, and rebuilt test-first once the screens are approved. See
``specs/032-record-search-fields/sketch.md``.
"""

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
    TomSelectMultipleChoiceField,
)


def record_config(url, *, multiple, placeholder=None, count_text=None, **extra):
    """Build the shared look: search in the dropdown, checkboxes and a count for several."""
    plugins = {
        "plugin_dropdown_input": PluginDropdownInput(),
        "plugin_clear_button": PluginClearButton(),
    }
    if multiple:
        plugins["plugin_checkbox_options"] = PluginCheckboxOptions()
    return TomSelectConfig(
        url=url,
        value_field="id",
        label_field="name",
        placeholder=placeholder,
        minimum_query_length=2,
        preload="focus",
        hide_selected=False,
        close_after_select=not multiple,
        highlight=True,
        loading_class="ts-loading",
        attrs=(
            {
                "data-none-text": str(placeholder),
                "data-count-text": str(count_text or _("selected")),
            }
            if multiple
            else {}
        ),
        **plugins,
        **extra,
    )


def _pair(kind, url_prefix, *, any_label, one_label, count_text):
    """Make the single and the multiple field for one kind of record."""

    class Single(TomSelectModelChoiceField):
        def __init__(self, *args, scope="view", filter_by=(), **kwargs):
            kwargs.setdefault("label", kind)
            super().__init__(
                *args,
                config=record_config(
                    f"autocomplete:{url_prefix}-{scope}",
                    multiple=False,
                    placeholder=one_label,
                    filter_by=filter_by,
                ),
                **kwargs,
            )

    class Multiple(TomSelectModelMultipleChoiceField):
        def __init__(self, *args, scope="public", filter_by=(), **kwargs):
            kwargs.setdefault("label", kind)
            super().__init__(
                *args,
                config=record_config(
                    f"autocomplete:{url_prefix}-{scope}",
                    multiple=True,
                    count_text=count_text,
                    placeholder=any_label,
                    filter_by=filter_by,
                ),
                **kwargs,
            )

    return Single, Multiple


ProjectChoiceField, ProjectMultipleChoiceField = _pair(
    _("Project"),
    "project",
    any_label=_("Any project"),
    one_label=_("Choose a project"),
    count_text=_("projects"),
)
DatasetChoiceField, DatasetMultipleChoiceField = _pair(
    _("Dataset"),
    "dataset",
    any_label=_("Any dataset"),
    one_label=_("Choose a dataset"),
    count_text=_("datasets"),
)
SampleChoiceField, SampleMultipleChoiceField = _pair(
    _("Sample"),
    "sample",
    any_label=_("Any sample"),
    one_label=_("Choose a sample"),
    count_text=_("samples"),
)
MeasurementChoiceField, MeasurementMultipleChoiceField = _pair(
    _("Measurement"),
    "measurement",
    any_label=_("Any measurement"),
    one_label=_("Choose a measurement"),
    count_text=_("measurements"),
)
PersonChoiceField, PersonMultipleChoiceField = _pair(
    _("Person"),
    "person",
    any_label=_("Anyone"),
    one_label=_("Choose a person"),
    count_text=_("people"),
)
OrganizationChoiceField, OrganizationMultipleChoiceField = _pair(
    _("Organization"),
    "organization",
    any_label=_("Any organization"),
    one_label=_("Choose an organization"),
    count_text=_("organizations"),
)
PublicationChoiceField, _unused = _pair(
    _("Data publication"),
    "publication",
    any_label=_("Any publication"),
    one_label=_("Search by title, author or DOI"),
    count_text=_("publications"),
)


def record_filter(field_class, **kwargs):
    """A django-filter filter that draws one of the multiple fields above."""
    import django_filters as df

    class RecordFilter(df.ModelMultipleChoiceFilter):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self.field_class = field_class

        def get_queryset(self, request):
            return None

        @property
        def field(self):
            if not hasattr(self, "_field"):
                extra = {
                    k: v
                    for k, v in self.extra.items()
                    if k not in ("queryset", "conjoined", "null_label", "null_value")
                }
                extra.setdefault("required", False)
                self._field = field_class(label=self.label, **extra)
            return self._field

    return RecordFilter(**kwargs)


def use_record_filters(filterset, fields):
    """SKETCH: swap a filter set's related-record filters for the autocomplete ones.

    A public list's filter offers public records only, to everyone.
    """
    for name, field_class in fields.items():
        if name in filterset.filters:
            old = filterset.filters[name]
            new = record_filter(
                field_class, field_name=old.field_name, label=old.label, distinct=True
            )
            new.model = old.model
            new.parent = filterset
            filterset.filters[name] = new


class TagsField(TomSelectMultipleChoiceField):
    """Free tags as chips: offers tags in use, and accepts new ones when ``allow_new`` is on.

    A form that records tags turns ``allow_new`` on. A filter leaves it off, since a tag nobody
    has used matches nothing.
    """

    def __init__(self, *args, allow_new=False, **kwargs):
        from django_tomselect.app_settings import PluginRemoveButton

        super().__init__(
            *args,
            config=TomSelectConfig(
                url="autocomplete:tags",
                value_field="value",
                label_field="label",
                create=allow_new,
                hide_selected=True,
                minimum_query_length=2,
                preload="focus",
                placeholder=_("Add a keyword") if allow_new else _("Any keyword"),
                loading_class="ts-loading",
                plugin_remove_button=PluginRemoveButton(),
            ),
            **kwargs,
        )

    def clean(self, value):
        return list(value or [])

    def valid_value(self, value):
        return True


def tag_filter(**kwargs):
    """SKETCH: a filter by tags already in use, with no way to add one."""
    import django_filters as df

    class TagsFilterField(TagsField):
        def __init__(self, *args, **kw):
            kw.pop("choices", None)
            super().__init__(*args, allow_new=False, **kw)

    class TagFilter(df.MultipleChoiceFilter):
        field_class = TagsFilterField

        def filter(self, qs, value):
            if not value:
                return qs
            return qs.filter(**{f"{self.field_name}__in": value}).distinct()

    return TagFilter(**kwargs)
