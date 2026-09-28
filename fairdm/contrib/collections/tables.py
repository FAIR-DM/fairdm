"""Table classes and column helpers for sample and measurement listings."""

import django_tables2 as tables
from django.core.exceptions import FieldDoesNotExist
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from easy_icons import icon
from research_vocabs.fields import ConceptManyToManyField

from fairdm.utils.choices import Visibility


def render_concept_many_to_many(value):
    """Render a concept many-to-many value as comma-separated links.

    Args:
        value: The related manager for the concept field.

    Returns:
        HTML with one link per concept, or an empty string when there are none.
    """
    if not value:
        return ""

    return mark_safe(", ".join(f"<a href='{c.uri}'>{c.name}</a>" for c in value.all()))


field_map = {
    "CharField": "char",
    "TextField": "char",
    "IntegerField": "num",
    "BigIntegerField": "num",
    "PositiveIntegerField": "num",
    "PositiveSmallIntegerField": "num",
    "SmallIntegerField": "num",
    "BooleanField": "bool",
    "DateField": "date",
    "DateTimeField": "datetime",
    "TimeField": "time",
    "DecimalField": "num",
    "FloatField": "num",
    "ForeignKey": "rel",
    "ManyToManyField": "rel",
}


class BaseTable(tables.Table):
    """Base table for all listings, adding type-based column classes and header tooltips.

    Args:
        *args: Passed to ``django_tables2.Table``.
        **kwargs: Passed to ``django_tables2.Table``.

    Attributes:
        id: The hidden UUID column.
        dataset: The dataset icon column.
    """

    id = tables.Column(verbose_name="UUID", visible=False)
    dataset = tables.Column(orderable=False, verbose_name="")

    def render_dataset(self, value):
        """Link the dataset icon unless the dataset is private.

        A published dataset can still be private, and its records stay in the listing
        without a link to a page the visitor cannot read.
        """
        if value.visibility != Visibility.PRIVATE:
            return format_html(
                '<a href="{}">{}</a>', value.get_absolute_url(), icon("dataset")
            )
        return icon("dataset")

    def render_location(self, value):
        """Link the location icon to the location's own page."""
        return format_html(
            '<a href="{}">{}</a>', value.get_absolute_url(), icon("location")
        )

    def value_dataset(self, value):
        """Export the dataset's UUID."""
        return value.uuid

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_columns["id"].visible = False

        self.configure_column_attrs()

        self.update_concept_field_render_methods()

    def configure_column_attrs(self):
        """Set each column's type and name CSS classes and its header tooltip from the model field."""
        model = getattr(self._meta, "model", None)

        for bound_col in self.columns:
            col = getattr(bound_col, "column", bound_col)

            # A dotted accessor such as 'sample.location.x' looks up its first part.
            fname = getattr(col, "accessor", None) or getattr(col, "name", "")
            field_name_for_lookup = fname.split(".")[0] if fname else ""

            db_field = None
            field_type = "CharField"
            if model and field_name_for_lookup:
                try:
                    db_field = model._meta.get_field(field_name_for_lookup)
                    field_type = db_field.get_internal_type()
                except Exception:
                    field_type = "CharField"

            field_type_class = field_map.get(field_type, "char")
            field_name_class = f"col-{fname.replace('_', '-')}" if fname else ""
            classes = f"{field_type_class} {field_name_class}".strip()

            td = col.attrs.setdefault("td", {})
            current = td.get("class", "")
            td["class"] = f"{classes} {current if current else ''}".strip()

            th = col.attrs.setdefault("th", {})
            current_th = th.get("class", "")
            th["class"] = f"{classes} {current_th if current_th else ''}".strip()

            help_text = getattr(db_field, "help_text", "") if db_field else ""
            if help_text:
                th["title"] = str(help_text)

    def update_concept_field_render_methods(self):
        """Render concept many-to-many columns as links."""
        for c in self.columns.columns.values():
            try:
                field = self._meta.model._meta.get_field(c.accessor)
            except FieldDoesNotExist:
                continue
            if isinstance(field, ConceptManyToManyField):
                c.render = render_concept_many_to_many


class SampleTable(BaseTable):
    """Listing table for samples."""

    name = tables.Column(linkify=True)
    latitude = tables.Column(accessor="location.x", verbose_name=_("Latitude"))
    longitude = tables.Column(accessor="location.y", verbose_name=_("Longitude"))
    location = tables.Column(
        accessor="location", verbose_name="", orderable=False, default=""
    )

    class Meta:
        attrs = {
            "class": "table table-striped table-hover overflow-auto align-middle mb-0"
        }
        sequence = ("dataset", "location", "...")
        # `added` is not unique, so paging needs `id` as a tie-break. `id` is always a column.
        order_by = ("added", "id")


class MeasurementTable(BaseTable):
    """Listing table for measurements."""

    name = tables.Column(linkify=True, verbose_name=_("Name"))
    sample = tables.Column()
    latitude = tables.Column(accessor="sample.location.x", verbose_name=_("Latitude"))
    longitude = tables.Column(accessor="sample.location.y", verbose_name=_("Longitude"))
    location = tables.Column(
        accessor="sample.location", verbose_name="", orderable=False, default=""
    )

    class Meta:
        attrs = {
            "class": "table table-striped table-hover overflow-auto align-middle mb-0"
        }
        # `modified` is not unique, so paging needs `id` as a tie-break.
        order_by = ("-modified", "id")

    def render_sample(self, value):
        """Link the sample only when its dataset is published."""
        if value.dataset.published:
            return format_html('<a href="{}">{}</a>', value.get_absolute_url(), value)
        return _("Unpublished")
