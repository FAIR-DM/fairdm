# How to filter a list by a record

This guide lets a visitor narrow a list to the rows that point at any of several chosen records, such as the samples that belong to either of two datasets. The filter draws a searchable control and offers only records the visitor may be shown.

## Before you start

You need a list view that takes its filters from a filter set. If yours does not, see [How to add search and sort to a list view](add-search-and-sort-to-a-list-view.md). This guide uses `CoreSample`, a sample type of your portal.

## Steps

1. Import the multiple field for the kind of record you want to choose, and the filter.

   ```python
   import django_filters

   from fairdm.contrib.autocomplete.fields import DatasetMultipleChoiceField
   from fairdm.contrib.autocomplete.filters import RecordMultipleFilter
   from myportal.models import CoreSample
   ```

2. Declare the filter on the filter set. Pass the field class and the name of the relation it filters.

   ```python
   class CoreSampleFilter(django_filters.FilterSet):
       dataset = RecordMultipleFilter(DatasetMultipleChoiceField, field_name="dataset")

       class Meta:
           model = CoreSample
           fields = ["dataset"]
   ```

3. Give the filter set to the list view.

   ```python
   from fairdm.views import FairDMListView


   class CoreSampleListView(FairDMListView):
       model = CoreSample
       filterset_class = CoreSampleFilter
   ```

   A list view builds its filter set with the request. If you build it yourself, pass the request:

   ```python
   filterset = CoreSampleFilter(request.GET, queryset=queryset, request=request)
   ```

4. To offer more than public records, pass `scope`. The filter then offers the records the signed-in visitor may view.

   ```python
   dataset = RecordMultipleFilter(
       DatasetMultipleChoiceField, scope="view", field_name="dataset"
   )
   ```

## The result

The filter panel of the list shows a search box for datasets. A visitor and a signed-in researcher are offered the same public datasets. Ticking two keeps the rows that point at either, and the values come back as repeated parameters, such as `?dataset=3&dataset=5`. A record the field would not offer is refused.

A filter set built with no request offers and accepts nothing. For the filter's arguments, see [Record fields](../reference/record-fields.md).
