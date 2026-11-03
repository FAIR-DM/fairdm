# How to search a registered type by more than its name

The search box on a registered type's listing matches the record's name and nothing else. You widen it when visitors look for records by another text field, such as a species or a site.

## Before you start

You need a registered type. See [How to register a sample or measurement type](register-a-sample-or-measurement-type.md). This guide uses `PlantSample`, a sample type in an app named `fieldwork`, with a `species` field that is a `CharField`.

## Steps

1. Add `search_fields` to the type's configuration. Name `name` as well if records should still be found by it, because declaring the option replaces the default.

   ```python
   # fieldwork/config.py
   from fairdm.core.sample.config import BaseSampleConfiguration
   from fairdm.registry import register

   from .models import PlantSample


   @register
   class PlantSampleConfig(BaseSampleConfiguration):
       model = PlantSample
       fields = [
           *BaseSampleConfiguration.fields,
           "species",
           "collected_on",
           "notes",
       ]
       search_fields = ["name", "species"]
   ```

   Each entry is a path to a text field. A path across a relation is allowed, such as `"dataset__name"`.

2. If the configuration overrides `get_filterset_class()` and builds the filter set with `FilterFactory`, pass the paths on. A filter set you build without them has no search box.

   ```python
   def get_filterset_class(self):
       return FilterFactory(
           model=self.model,
           fields=["species", "collected_on"],
           search_fields=self.get_search_fields(),
       ).generate()
   ```

3. If the configuration supplies a filter set in `filterset_class`, `search_fields` does not reach it. Give that class a `SearchFilter` named `q` from `mvp.filters` and list the paths there.

4. Restart the portal and open the type's listing at `/collections/samples/plantsample/`. Type a word from a plant's species into the search box.

## The result

The listing keeps every record in which any word of the term appears, ignoring case, in any of the paths. A search for `quercus` finds a plant sample whose species is `Quercus robur`.

A path that names no field, or ends in a field that is not a `CharField` or a `TextField`, stops the portal at start-up with a `FieldValidationError` that names the configuration and the path. A number, a boolean, a date and a geometry are all refused, and so is `search_fields = ["weight_grams"]` on a `FloatField`.

The framework indexes `name` and no other field. A field you add to `search_fields` is yours to index, and on a large table a search over it scans every row. See [ADR 0016](../../adr/0016-the-framework-indexes-the-fields-it-searches-by-default.md).

The option is described on [Model configuration](../reference/model-configuration.md#search-fields). To add search and sort to a list view of your own, see [How to add search and sort to a list view](add-search-and-sort-to-a-list-view.md).
