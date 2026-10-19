# How to move a list view's search and sort into its filterset

FairDM 0.29 builds on django-mvp 0.29, where a list page takes its search, sort and filters
from one django-filter filterset. A view that subclasses `FairDMListView` or
`FairDMTableView` and declares `search_fields` or `order_by` raises `ImproperlyConfigured` when
Django imports its module. So does a view that composes django-filter's `FilterView`. Follow
these steps for each such view.

## Move the search and the sort

1. Find the view's `search_fields` and `order_by`.

   ```python
   class ProductListView(FairDMListView):
       model = Product
       filterset_class = ProductFilter
       search_fields = ["name", "description"]
       max_search_words = 20
       order_by = [
           ("name_asc", "Name (A-Z)", ["name", "pk"]),
           ("newest", "Newest first", ["-created", "-pk"]),
       ]
   ```

2. Add a `SearchFilter` and a `SortFilter` to the view's filterset, and delete the three
   attributes from the view. `max_search_words` becomes `max_words`. Each option keeps its key,
   its label and its ordering columns.

   ```python
   import django_filters
   from mvp.filters import SearchFilter, SortFilter


   class ProductFilter(django_filters.FilterSet):
       q = SearchFilter(fields=["name", "description"], max_words=20)
       o = SortFilter(
           options=[
               ("name_asc", "Name (A-Z)", ["name", "pk"]),
               ("newest", "Newest first", ["-created", "-pk"]),
           ]
       )

       class Meta:
           model = Product
           fields = ["status"]


   class ProductListView(FairDMListView):
       model = Product
       filterset_class = ProductFilter
       toolbar_filters = ["q", "status"]
   ```

   A view that had no filterset gets one by declaring the class above and setting
   `filterset_class`.

3. Name the fields to draw in the toolbar in `toolbar_filters`, in the order they should
   appear. The rest of the filterset's fields go in the Filter dialog, and the sort sits at the
   end of the toolbar by the Filter button. A `RangeFilter` or `DateFromToRangeFilter` with its
   default widget cannot be in the toolbar; leave it in the dialog.

4. Declare the `SearchFilter` as `q` and the `SortFilter` as `o`, as in the example. Each filter's
   name is its query parameter, so existing addresses such as `?q=basalt&o=newest` keep working,
   and the sort keys are unchanged.

## Drop django-filter's `FilterView`

5. If the view lists `FilterView` among its bases, remove it. `FairDMListView` and
   `FairDMTableView` build their own filterset, and a view that composes `FilterView` is
   refused at import.

6. A table view sorts by its column headers, so a `SortFilter` on its filterset is ignored. Set
   the table's own `order_by` or `Meta.order_by` instead.

## Fix templates that override the page controls

7. The `page.search` and `page.controls` blocks of the list page are gone. A template that
   filled them, or that used `{{ block.super }}` in `page.actions` to sit next to the Add
   button, needs a new home for its content. `page.actions` still exists in the title row
   of a list page and in the bar of a table page, and is empty by default.

8. Remove any `<c-mvp.page.list.actions.create />` from a template of your own. The Add
   button is the last control in the toolbar, and a second one appears if the template draws
   its own.

## Keep a registered type's search

9. A registered sample or measurement type keeps `search_fields` on its configuration. The
   generated filterset gets a `q` filter over those fields, and the listing draws it in
   the toolbar with the status filter when the type has one. A configuration that overrides
   `get_filterset_class()` and calls `FilterFactory` itself passes the fields on:

   ```python
   def get_filterset_class(self):
       return FilterFactory(
           model=self.model,
           fields=self.FILTERABLE,
           search_fields=self.get_search_fields(),
       ).generate()
   ```

   A `filterset_class` you declare yourself carries its own `SearchFilter` named `q`.

## Check the page

10. Open the list page and confirm the search box, the sort and the Filter button appear, and
    that a search and a sort change the results. Run the project's tests, which fail on any view
    that still declares a removed attribute.
