# Collections App

The `collections` app renders one browsable, filterable listing page per registered Sample or
Measurement type. A type needs no view, URL or template of its own to appear here: registering it
with `fairdm.registry` is enough.

## Purpose

This app is responsible for:

1. **Listing pages**: one page per registered type, with search, column sorting, django-filter
   filtering, and pagination
2. **Table classes**: the base table classes (`BaseTable`, `SampleTable`, `MeasurementTable`) every
   generated table starts from, unless a registration supplies its own
3. **Navigation**: the Samples/Measurements entries in the portal's main menu, one per registered
   type

## Components

### Views (`views.py`)

- **`DataTableView`**: the listing view for one registered Sample or Measurement type
  - Filters every row through `published()` so only published records ever appear
  - Search fields, filters and columns all come from the type's own registration
  - `get_urls()` builds one route per registered type, under `samples/<slug>/` or
    `measurements/<slug>/`, and refuses two registrations that would collide on the same address

### Tables (`tables.py`)

- **`BaseTable`**: shared rendering - the UUID column, dataset/location icons, per-field-type CSS
  classes, and `ConceptManyToManyField` rendering
- **`SampleTable`**: adds latitude/longitude and a linkified location column
- **`MeasurementTable`**: adds a linkified sample column and the same location columns, read
  through the measurement's own sample

`TableFactory` (`fairdm/registry/factories.py`) builds each registered type's table from one of
these two by default; a registration only needs its own `table_class` to replace that outright.

## Templates

- **`templates/collections/listing.html`**: the page `DataTableView` renders. Extends the
  application shell's own `table_view.html` and adds the cross-listing switcher - a control
  offering every other registered type's listing - whenever more than one type is registered.

## Integration

The collections app is self-contained and integrates with the rest of the framework through:

1. **Registry**: `fairdm.registry` is where every listing's routes, columns, search fields and
   filters come from
2. **Menus**: `apps.py`'s `CollectionsConfig.populate_data_collection_menu()` builds the
   Samples/Measurements navigation entries from the registry when the app starts

## Usage

Registering a type is enough for its listing to appear, addressed and linked from the navigation,
with no further configuration:

```python
import fairdm
from fairdm.core.sample.config import BaseSampleConfiguration


@fairdm.register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
    fields = ["name", "location", "rock_type"]
    search_fields = ["rock_type"]
```

### Custom Table Classes

To customise a type's listing columns beyond what `fields` can say, subclass the matching base
table and reference it from the registration:

```python
from fairdm.contrib.collections.tables import SampleTable


class RockSampleTable(SampleTable):
    class Meta:
        model = RockSample
        fields = ["id", "dataset", "name", "rock_type", "mineral_content"]

    def render_rock_type(self, value):
        return value.upper()


@fairdm.register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
    table_class = RockSampleTable
```

## Dependencies

- `django-tables2`: table rendering
- `django-filter`: filtering, via the registry-generated filterset
- `research-vocabs`: `ConceptManyToManyField` rendering
- `easy-icons`: icon rendering
