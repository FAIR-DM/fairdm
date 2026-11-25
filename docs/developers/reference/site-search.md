# Site search

The search field in the header, the search dialog and the search page at `/search/` are django-mvp's (`mvp.search`). FairDM supplies what they find: seven kinds in `fairdm.search`, registered by `register_kinds()` when the `fairdm` app is ready. The landing page has its own header and carries no search.

## The record types

The search page and the dialog list the types in this order.

| Kind name | Finds | Matches | Who sees a record |
|---|---|---|---|
| `projects` | Projects | Name, portal ID and external identifiers | Public projects, and projects the person holds a contribution level on |
| `datasets` | Datasets | Name, portal ID, external identifiers, descriptions and keywords | Datasets the person may open, as `Dataset.all_objects.visible_to(user)` decides |
| `samples` | Samples of every registered type | Name, local ID and portal ID | Samples the person may open, as `Sample.objects.visible_to(user)` decides |
| `measurements` | Measurements of every registered type | Name and portal ID | Measurements the person may open, as `Measurement.objects.visible_to(user)` decides |
| `people` | People | Name | Every person except superusers and the anonymous user |
| `organizations` | Organizations | Name | Everyone |
| `literature` | References | Citation key, titles, contributors' names and identifiers, as the literature catalogue matches them | Everyone |

A record the person may not open is neither listed nor counted. Each result links to the record's own page, and a registered sample or measurement type links to the page of its own type. Each type's results are ordered by name or title, then by primary key, so paging is stable.

## What a result shows

| Kind | Line under the title |
|---|---|
| Projects, people, organizations, literature | The record type |
| Datasets | The dataset's project |
| Samples | The sample's type, then its local ID and dataset |
| Measurements | The measurement's type, then its sample |

## How matching works

A kind runs the `q` filter of its type's list page over the records the person may open. The header and the list page therefore agree on what matches, and nothing is indexed. A query that is only a DOI prefix such as `doi:` matches no references.

The `search_fields` of a registered sample or measurement type match only in that type's own table. The site search uses the base filter, so a field named only there does not match.

## Names

| Name | What it is |
|---|---|
| `fairdm.search.RecordKind` | Base class of the seven kinds. It sets `filterset_class` and `ordering`, and defines `records(user)` and `describe(item)`. |
| `ProjectKind`, `DatasetKind`, `SampleKind`, `MeasurementKind`, `PeopleKind`, `OrganizationKind`, `LiteratureKind` | The seven kinds in `fairdm.search`, one for each row of the table above, each built on `RecordKind`. |
| `fairdm.search.register_kinds()` | Registers the seven kinds in the order above. |
| `mvp-search`, `mvp-search-panel` | The names of django-mvp's search page and dialog panel, mounted at `search/`. |
| `MVP_CONFIG["search"]["kinds"]` | django-mvp's setting that names the kinds to search, in the order their groups appear. Empty searches every registered kind. |
| `mvp.search.register` | django-mvp's function that registers a kind. |
