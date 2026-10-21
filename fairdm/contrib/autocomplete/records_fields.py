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

RECORD_OPTION = (
    '`<div class="flex items-center justify-between gap-3">'
    '<div class="min-w-0"><div class="truncate">${data.name}</div>'
    '<div class="text-xs text-base-content/60 truncate">${data.detail}</div></div>'
    '<span class="${data.badge_class}">${data.badge}</span></div>`'
)

CONTRIBUTOR_OPTION = (
    '`<div class="flex items-center gap-3">'
    '<img src="${data.image}" alt="" class="${data.image_class}">'
    '<span class="${data.initials_class}" aria-hidden="true">${data.initials}</span>'
    '<div class="min-w-0 flex-1"><div class="truncate">${data.name}</div>'
    '<div class="text-xs text-base-content/60 truncate">${data.detail}</div></div>'
    '<span class="${data.badge_class}">${data.badge}</span></div>`'
)


def record_config(url, *, multiple, option=RECORD_OPTION, placeholder=None, **extra):
    """Build the shared look: search in the dropdown, checkboxes for several."""
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
        minimum_query_length=0,
        preload="focus",
        hide_selected=False,
        close_after_select=not multiple,
        highlight=True,
        loading_class="ts-loading",
        attrs={"render": {"option": option}},
        **plugins,
        **extra,
    )


def _pair(kind, url_prefix, *, option=RECORD_OPTION, any_label, one_label):
    """Make the single and the multiple field for one kind of record."""

    class Single(TomSelectModelChoiceField):
        def __init__(self, *args, scope="view", filter_by=(), **kwargs):
            kwargs.setdefault("label", kind)
            super().__init__(
                *args,
                config=record_config(
                    f"autocomplete:{url_prefix}-{scope}",
                    multiple=False,
                    option=option,
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
                    option=option,
                    placeholder=any_label,
                    filter_by=filter_by,
                ),
                **kwargs,
            )

    return Single, Multiple


ProjectChoiceField, ProjectMultipleChoiceField = _pair(
    _("Project"), "project", any_label=_("Any project"), one_label=_("Choose a project")
)
DatasetChoiceField, DatasetMultipleChoiceField = _pair(
    _("Dataset"), "dataset", any_label=_("Any dataset"), one_label=_("Choose a dataset")
)
SampleChoiceField, SampleMultipleChoiceField = _pair(
    _("Sample"), "sample", any_label=_("Any sample"), one_label=_("Choose a sample")
)
MeasurementChoiceField, MeasurementMultipleChoiceField = _pair(
    _("Measurement"),
    "measurement",
    any_label=_("Any measurement"),
    one_label=_("Choose a measurement"),
)
PersonChoiceField, PersonMultipleChoiceField = _pair(
    _("Person"),
    "person",
    option=CONTRIBUTOR_OPTION,
    any_label=_("Anyone"),
    one_label=_("Choose a person"),
)
OrganizationChoiceField, OrganizationMultipleChoiceField = _pair(
    _("Organization"),
    "organization",
    option=CONTRIBUTOR_OPTION,
    any_label=_("Any organization"),
    one_label=_("Choose an organization"),
)
PublicationChoiceField, _unused = _pair(
    _("Data publication"),
    "publication",
    any_label=_("Any publication"),
    one_label=_("Search by title, author or DOI"),
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
    """Free tags as chips: offers tags in use and accepts new ones."""

    def __init__(self, *args, **kwargs):
        from django_tomselect.app_settings import PluginRemoveButton

        super().__init__(
            *args,
            config=TomSelectConfig(
                url="autocomplete:tags",
                value_field="value",
                label_field="label",
                create=True,
                hide_selected=True,
                minimum_query_length=1,
                preload=False,
                placeholder=_("Add a keyword"),
                loading_class="ts-loading",
                plugin_remove_button=PluginRemoveButton(),
            ),
            **kwargs,
        )

    def clean(self, value):
        return list(value or [])

    def valid_value(self, value):
        return True
