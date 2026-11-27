# How to add search and sort to a list view

This guide gives a list page a search box and a sort control. A list page takes its search, its sort and its filters from one django-filter filter set, so you add the search and the sort to that filter set and name it on the view.

## Before you start

You need a list view that subclasses `FairDMListView` or `FairDMTableView`, and a model to list. This guide uses `CoreSample`, a sample type of your portal with a `lithology` text field. For the view classes, see [Base views](../reference/base-views.md).

## Steps

1. Declare a `SearchFilter` named `q` and a `SortFilter` named `o` on a filter set. `q` and `o` are django-mvp's names for the search and the sort, and each filter's name is its query parameter, as in `?q=basalt&o=newest`.

   ```python
   import django_filters
   from mvp.filters import SearchFilter, SortFilter

   from myportal.models import CoreSample


   class CoreSampleFilter(django_filters.FilterSet):
       q = SearchFilter(fields=["name", "local_id"])
       o = SortFilter(
           options=[
               ("name", "Name (A-Z)", ["name", "pk"]),
               ("newest", "Recently changed", ["-modified", "-pk"]),
           ]
       )

       class Meta:
           model = CoreSample
           fields = ["lithology"]
   ```

   `SearchFilter` keeps the rows in which some word of the text appears in some of the named fields, ignoring case, and it returns each row once. It searches the first ten words, and `max_words` changes that. Each `SortFilter` option is a key, a label and the columns to order by. End the columns with a unique one, usually `"pk"`, so the order holds across pages.

2. Name the filter set on the view and say which of its fields the toolbar draws.

   ```python
   from fairdm.views import FairDMListView


   class CoreSampleListView(FairDMListView):
       model = CoreSample
       filterset_class = CoreSampleFilter
       toolbar_filters = ["q", "lithology"]
   ```

   The toolbar draws the fields named in `toolbar_filters`, in that order, and the sort at the end of the row. A name that is not a field of the filter set raises `ImproperlyConfigured`. The page's filter panel holds every other field of the filter set.

3. Leave a range filter in the panel. A `RangeFilter` or a `DateFromToRangeFilter` with its default widget cannot be drawn in the toolbar, and naming one in `toolbar_filters` raises `ImproperlyConfigured`.

4. On a table view, sort by the column headers. A `FairDMTableView` drops a `SortFilter` from its filter set without an error, so the same filter set serves a list page and a table page. Set the table's own `order_by` or `Meta.order_by` for the default order.

5. For a registered sample or measurement type, set `search_fields` on its configuration instead. The generated filter set gets a `q` filter over those fields. See [How to search a registered type by more than its name](search-a-registered-type-by-more-than-its-name.md).

## The result

Open the list page. The toolbar shows a search box, the filters you named and the sort, and the filter panel holds the rest. Searching and sorting change the results, and the page tells the visitor what is narrowing the list and offers a link that clears it.

A list view takes its search and sort from its filter set only. A view that declares `search_fields`, `max_search_words`, `order_by`, `get_search_fields` or `get_order_by_choices` is refused with `ImproperlyConfigured` when Django imports its module. So is a view that also composes django-filter's `FilterView`, because a list view builds its own filter set.
