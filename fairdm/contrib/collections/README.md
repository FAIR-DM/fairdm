# Collections App

The `collections` app provides tabular views and data management functionality for FairDM Sample and Measurement sub-types.

## Purpose

This app is responsible for:

1. **Tabular Views**: Displaying Sample and Measurement data in rich, interactive tables with filtering, sorting, pagination, and export capabilities
2. **Table Classes**: Providing base table classes (`BaseTable`, `SampleTable`, `MeasurementTable`) for rendering data using django-tables2
3. **Data Plugins**: Offering plugins that show tabular views of data related to core objects (Projects, Datasets)

## Components

### Views (`views.py`)

- **`DataTableView`**: Main view class for displaying tabular data with django-tables2 integration
  - Provides filtering, sorting, pagination
  - Supports multiple export formats (CSV, XLS, XLSX, JSON, etc.)
  - Integrates with FairDM's registry system

- **`CollectionRedirectView`**: Redirect view for navigating to the first registered collection

### Tables (`tables.py`)

- **`BaseTable`**: Base table class providing common functionality for all FairDM tables
  - Icon rendering for datasets and locations
  - Automatic handling of ConceptManyToManyField rendering
  - UUID column management

- **`SampleTable`**: Specialized table for Sample models
  - Includes location-specific columns (latitude, longitude)
  - Sample name linkification

- **`MeasurementTable`**: Specialized table for Measurement models
  - Links to associated samples
  - Prefetches sample data for efficiency
  - Location data from samples

### Plugins (`plugins.py`)

- **`DataTablePlugin`**: Plugin for displaying data collections in detail views
  - Automatically generates URLs for all registered Sample and Measurement types
  - Provides tabular interface within Dataset detail views
  - Category: EXPLORE
  - Icon: table

## Templates

- **`collections/table_view.html`**: Main template for rendering tabular data views
  - Responsive design with mobile-friendly controls
  - Toolbar with search, filter, and export actions
  - Pagination and record count display

## Integration

The collections app is self-contained and integrates with the core FairDM framework through:

1. **Registry**: Uses `fairdm.registry` to discover registered Sample and Measurement models
2. **Import/Export**: Integrates with `fairdm.contrib.import_export` for data export functionality
3. **Menus**: Uses `fairdm.menus.SiteNavigation` for navigation integration
4. **Plugins**: Extends the FairDM plugin system to provide tabular views in detail pages

## Usage

### In Core URLs

```python
from fairdm.contrib.collections.plugins import DataTablePlugin
from fairdm.contrib.collections.views import CollectionRedirectView

urlpatterns = [
    path("data/collections.html", CollectionRedirectView.as_view(), name="data-collections"),
    path("", include(DataTablePlugin.get_urls()[0])),
]
```

### Custom Table Classes

To use custom table classes for your Sample or Measurement models, specify the `table_class` in your model's `FairDM` configuration:

```python
class MySample(Sample):
    class FairDM:
        table_class = "myapp.tables.MySampleTable"
```

Or reference the collections base tables:

```python
class FairDM:
    table_class = "fairdm.contrib.collections.tables.SampleTable"
```

## Dependencies

- `django-tables2`: For table rendering
- `django-filter`: For filtering (via FairDMListView)
- `research-vocabs`: For ConceptManyToManyField rendering
- `easy-icons`: For icon rendering
