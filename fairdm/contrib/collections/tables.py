import django_tables2 as tables
from django.core.exceptions import FieldDoesNotExist
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from easy_icons import icon
from research_vocabs.fields import ConceptManyToManyField

from fairdm.utils.choices import Visibility


def render_concept_many_to_many(value):
    """
    Custom render function for ConceptManyToManyField to display concepts.
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
    """Base table class for all FairDM tables."""

    id = tables.Column(verbose_name="UUID", visible=False)
    dataset = tables.Column(orderable=False, verbose_name="")

    def render_dataset(self, value):
        """Link the dataset icon only where its own page would not refuse the visitor.

        Publication and visibility are independent (D1, FR-003), so a published-but-
        private dataset is the ordinary state, not an edge case - its records still
        belong in the listing, but this column carries no link to a page it cannot
        read (D3, extended at design review).
        """
        if value.visibility != Visibility.PRIVATE:
            return format_html(
                '<a href="{}">{}</a>', value.get_absolute_url(), icon("dataset")
            )
        return icon("dataset")

    def render_location(self, value):
        """Link the location icon to the location's own page.

        django-tables2 never calls this at all when the accessor resolves to
        `None` (`Column.empty_values`) - it substitutes the column's `default`
        instead - so this only runs where a location genuinely exists.
        """
        return format_html(
            '<a href="{}">{}</a>', value.get_absolute_url(), icon("location")
        )

    def value_dataset(self, value):
        return value.uuid

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_columns["id"].visible = False

        self.better_row_classes()

        self.update_concept_field_render_methods()

    def better_row_classes(self):
        model = getattr(self._meta, "model", None)

        # Iterate over bound columns (safer) and update/ensure the nested 'td' dict exists.
        # Use setdefault so we mutate the actual attrs mapping instead of a temporary dict.
        for bound_col in self.columns:
            # Get the underlying Column definition if present
            col = getattr(bound_col, "column", bound_col)

            # Determine accessor/name to use for field lookup; if accessor contains
            # dotted lookups (e.g. 'sample.location.x') use the first part for model field.
            fname = getattr(col, "accessor", None) or getattr(col, "name", "")
            field_name_for_lookup = fname.split(".")[0] if fname else ""

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

            # Also update the header cell classes (`th`) in the same way so
            # both header and data cells receive the same type-based classes.
            th = col.attrs.setdefault("th", {})
            current_th = th.get("class", "")
            th["class"] = f"{classes} {current_th if current_th else ''}".strip()

    def update_concept_field_render_methods(self):
        """
        Update the render methods for ConceptManyToManyField in the table.
        This is called in the constructor to ensure all fields are set up correctly.
        """
        for c in self.columns.columns.values():
            try:
                field = self._meta.model._meta.get_field(c.accessor)
            except FieldDoesNotExist:
                continue
            if isinstance(field, ConceptManyToManyField):
                c.render = render_concept_many_to_many


class SampleTable(BaseTable):
    """Table class for Sample models."""

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
        # The dataset and location icons lead every sample listing, ahead of
        # whatever fields the registered type declares.
        sequence = ("dataset", "location", "...")
        # `Sample.Meta.ordering` (`["added"]`) is a single non-unique field, so
        # paging can repeat or skip rows without a tie-break (D5, FR-033). `id`
        # is always a column here - declared on `BaseTable` - so it survives
        # `order_by`'s column-membership check even for a type whose own
        # fields never name `added`.
        order_by = ("added", "id")


class MeasurementTable(BaseTable):
    """Table class for Measurement models."""

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
        # `Measurement.Meta.ordering` (`["-modified"]`) is a single non-unique
        # field; see `SampleTable.Meta.order_by` (D5, FR-033).
        order_by = ("-modified", "id")

    def render_sample(self, value):
        if value.dataset.published:
            return format_html('<a href="{}">{}</a>', value.get_absolute_url(), value)
        return _("Unpublished")
