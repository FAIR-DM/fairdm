# How to add a filter to a sample type

This guide writes a filter set for a sample type, with a range filter, a date range filter, a vocabulary filter and a filter that calls a method of its own. You would do this when the filter set the registry generates for the type does not offer the filters your visitors need.

## Before you start

You need a registered sample type. This guide uses `CoreSample`, a sample type of your portal. To add one, see [How to add a sample type](add-a-sample-type.md).

```python
from fairdm.core.sample.models import Sample
from fairdm.db import models


class CoreSample(Sample):
    depth_m = models.FloatField("Depth (m)", null=True, blank=True)
    lithology = models.CharField("Lithology", max_length=100, blank=True)
    cored_on = models.DateField("Cored on", null=True, blank=True)
```

## Steps

1. Write a filter set that combines `SampleFilterMixin` with `django_filters.FilterSet`. Extend the mixin's `Meta`, so the filter set keeps the mixin's `status`, `dataset` and `polymorphic_ctype` fields.

   ```python
   import django_filters

   from fairdm.core.sample.filters import SampleFilterMixin
   from myportal.models import CoreSample


   class CoreSampleFilter(SampleFilterMixin, django_filters.FilterSet):
       class Meta(SampleFilterMixin.Meta):
           model = CoreSample
           fields = [*SampleFilterMixin.Meta.fields, "lithology"]
   ```

   A `Meta` that does not extend the mixin's keeps the mixin's `image` filter but loses its `fields` list. See [Form and filter mixins](../reference/form-and-filter-mixins.md).

2. Add a range filter with two number filters over one field.

   ```python
   class CoreSampleFilter(SampleFilterMixin, django_filters.FilterSet):
       depth_min = django_filters.NumberFilter(
           field_name="depth_m", lookup_expr="gte", label="Depth from (m)"
       )
       depth_max = django_filters.NumberFilter(
           field_name="depth_m", lookup_expr="lte", label="Depth to (m)"
       )

       class Meta(SampleFilterMixin.Meta):
           model = CoreSample
           fields = [*SampleFilterMixin.Meta.fields, "lithology"]
   ```

3. Add a date range filter with a date input.

   ```python
   from django_filters.widgets import RangeWidget

   cored_on = django_filters.DateFromToRangeFilter(
       label="Cored between",
       widget=RangeWidget(attrs={"type": "date"}),
   )
   ```

   Declare it in the class body, as in step 2.

4. Add a filter for a field that stores a term from a vocabulary. Such a field stores the term's name as a string, so give a `ChoiceFilter` the vocabulary's choices. The sample status is one.

   ```python
   from fairdm.core.vocabularies import FairDMSampleStatus

   status = django_filters.ChoiceFilter(
       label="Status",
       choices=FairDMSampleStatus().choices,
       empty_label="Any status",
   )
   ```

5. Add a filter that calls a method of the filter set, for a condition no field holds. This one keeps the samples that other samples are children of.

   ```python
   from fairdm.core.sample.models import SampleRelation

   has_children = django_filters.BooleanFilter(
       method="filter_has_children", label="Has child samples"
   )

   def filter_has_children(self, queryset, name, value):
       if value:
           parents = SampleRelation.objects.filter(type="child_of").values("target_id")
           return queryset.filter(pk__in=parents)
       return queryset
   ```

   The method belongs in the class body, beside the filters.

6. To offer the datasets as a searchable control, declare `dataset` as a record filter. See [How to filter a list by a record](filter-a-list-by-a-record.md).

7. Tell the registry to use the filter set. Put the configuration in your app's `config.py`.

   ```python
   import fairdm
   from fairdm.core.sample.config import BaseSampleConfiguration
   from myportal.models import CoreSample


   @fairdm.register
   class CoreSampleConfig(BaseSampleConfiguration):
       model = CoreSample
       filterset_class = "myportal.filters.CoreSampleFilter"
   ```

   A configuration declares either `filterset_fields` or `filterset_class`, never both.

## The result

The listing of the type offers your filters beside the mixin's. Filters combine, so each one a visitor sets narrows the list further. A filter set used outside the listing needs the request to scope its record filters, as `CoreSampleFilter(request.GET, queryset=queryset, request=request)` does.
