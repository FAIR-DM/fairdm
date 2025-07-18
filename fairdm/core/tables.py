import django_tables2 as tables
from django.core.exceptions import FieldDoesNotExist
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from easy_icons import icon
from research_vocabs.fields import ConceptManyToManyField


def render_concept_many_to_many(value):
    """
    Custom render function for ConceptManyToManyField to display concepts.
    """
    if not value:
        return ""

    return mark_safe(", ".join(f"<a href='{c.uri}'>{c.name}</a>" for c in value.all()))


class BaseTable(tables.Table):
    id = tables.Column(verbose_name="UUID", visible=False)
    dataset = tables.Column(linkify=True, orderable=False, verbose_name=False)

    def render_dataset(self, value):
        return icon("dataset")

    def render_location(self, record):
        return icon("location")

    def value_dataset(self, value):
        return value.uuid

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_columns["id"].visible = False
        self.update_concept_field_render_methods()

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
    name = tables.Column(linkify=True)
    latitude = tables.Column(accessor="location.x", verbose_name=_("Latitude"))
    longitude = tables.Column(accessor="location.y", verbose_name=_("Longitude"))
    location = tables.Column(accessor="location", linkify=True, verbose_name=False, orderable=False)


class MeasurementTable(BaseTable):
    sample = tables.Column(linkify=True)
    latitude = tables.Column(accessor="sample.location.x", verbose_name=_("Latitude"))
    longitude = tables.Column(accessor="sample.location.y", verbose_name=_("Longitude"))
    location = tables.Column(accessor="sample.location", linkify=True, verbose_name=False, orderable=False)

    def __init__(self, data=None, *args, **kwargs):
        # modify the queryset (data) here if required
        data = data.prefetch_related("sample")
        super().__init__(*args, data=data, **kwargs)

    def render_sample(self, value):
        sample_type = value.get_real_instance_class()
        return sample_type._meta.verbose_name
