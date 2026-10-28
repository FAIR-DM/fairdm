# Overview plugins

An overview page's numbers, lists and cards are worked out by a plugin registered as the first tab of the record. This page lists those plugin classes, their attributes and methods, the context each provides and the helper functions they share. It does not describe the template blocks that draw the context, which [Overview page blocks](overview-page-blocks.md) covers, or how to register a plugin, which [Plugins](plugins.md) covers.

## Classes

| Class | Module | Registered on | Template |
|---|---|---|---|
| `OverviewPlugin` | `fairdm.core.plugins` | Base class. A tab with the label "Overview" and the page title taken from the record's string form. | |
| `RecordOverviewPlugin` | `fairdm.core.plugins` | Base class of the four core overview plugins. | |
| `TypedOverviewPlugin` | `fairdm.core.plugins` | Base class of the sample and measurement overviews. | |
| `Overview` | `fairdm.core.project.plugins` | `Project` | `project/project_detail.html` |
| `Overview` | `fairdm.core.dataset.plugins` | `Dataset` | `dataset/dataset_detail.html` |
| `Overview` | `fairdm.core.sample.plugins` | `Sample` | `sample/sample_overview.html`, or a type's own |
| `Overview` | `fairdm.core.measurement.plugins` | `Measurement` | `measurement/measurement_overview.html`, or a type's own |
| `Overview` | `fairdm.contrib.contributors.plugins.overview` | `Contributor` | `contributors/overview/person.html` or `organization.html` |

Each core `Overview` has `url_path = None`, so the overview sits at the record's own address.

## `RecordOverviewPlugin`

It holds what every record overview works out the same way. A portal changes one piece of a page by subclassing a record's `Overview` and overriding one attribute or method.

### Attributes

| Attribute | Default | What it sets |
|---|---|---|
| `people_shown` | `18` | How many faces the People card draws before it counts the rest. |
| `resolvable_identifier_types` | `(DOI, IGSN)`, the addresses from `fairdm.core.vocabularies` | The identifier types that link to doi.org. A value links only when it starts with `10.`. |

### Methods

| Method | Returns |
|---|---|
| `get_context_data(**kwargs)` | The context with `people_url` (the record's Contributors tab) and `manage_menu` added. |
| `get_contributions()` | The record's credits, people first and then organizations, each in the order set on the Contributors tab, each with its real contributor and roles loaded. |
| `get_role_uris(contribution)` | The set of the addresses of the roles held on one credit. |
| `get_contributors_with_role(entries, role)` | The contributors of every entry in `get_credits()` that holds the role, given by its address. |
| `get_credits()` | One dictionary per credit, in the order of `get_contributions()`: `contributor`, `roles` (a dictionary of role address to label) and `affiliation` (the organization recorded on the credit, or `None`). |
| `get_people(entries=None)` | What the People card shows: `shown` (up to `people_shown`), `more` and `total`. |
| `get_identifiers()` | One dictionary per identifier: `type`, the identifier type's concept, `value` and `link`. |
| `get_citation(*, authors, year, title, link)` | The citation as text: `Creators (Year). Title. Publisher. Identifier.` The publisher is the current site's name. |
| `get_timeline(steps, dates, descriptions, entries)` | One dictionary per step that has a date, a person or a note, with `label`, `date`, `day`, `people` and `note`. Dated steps come first. `steps` is a list of `(date_type, role, description_type, label)`, each type and role given by its address. |
| `get_license_entry(licence, note=None)` | A row for [`c-card.details`](components.md#c-carddetails), or a warning row when no licence is chosen. |
| `get_composition_chart(samples, measurements)` | A dictionary of `chart`, `height` and `description`, counting records by registered type, or `None` when there is nothing to count. |
| `get_growth_chart(samples, measurements)` | A dictionary of `chart` and `description` for the running total by month, or `None` when the records span fewer than two months. |

```python
from fairdm.core.plugins import RecordOverviewPlugin


class Summary(RecordOverviewPlugin):
    people_shown = 8
```

## `TypedOverviewPlugin`

It subclasses `RecordOverviewPlugin` for the records portals subclass: samples and measurements.

| Attribute | Default | What it sets |
|---|---|---|
| `base_model` | `None` | The core model the records share. A subclass that names it opens a record only for a user the base model's `visible_to` admits. A subclass with none opens no record. |
| `fallback_template` | `None` | The template used when no type has one. |

| Method | Returns |
|---|---|
| `get_template_names()` | For each concrete class from the record's own type up to `base_model`, `<app_label>/<model_name>_overview.html`, then `fallback_template`. |
| `get_type_info()` | A dictionary of `description`, `authority`, `citation` and `keywords` read from the type's registry configuration, or `None` when the type is not registered or the registry holds nothing to say. |
| `handle_no_permission()` | Raises a 404, so the address never confirms the record exists. |

## Project `Overview`

| Attribute | Default | What it sets |
|---|---|---|
| `dataset_preview` | `5` | Datasets listed before the page hands over to the Datasets tab. |
| `lead_roles` | The addresses of the project leader and project manager roles | The roles that name the people a visitor sees first. |

| Method | Returns |
|---|---|
| `get_descriptions()` | The descriptions the project has text for, in the vocabulary's order. |
| `get_progress()` | The start and end dates, `percent` elapsed, the year the project is in, the number of years and a `label`. |
| `get_team()` | `leads`, `contact`, `contact_is_lead`, `others`, `total`, `people`, `organizations`, `has_contact` and `reach`. |
| `get_counts(datasets, samples, measurements, can_manage)` | The counts of datasets, samples and measurements, each with a `_desc` line. |
| `get_datasets_preview(datasets)` | `rows` (up to `dataset_preview`) and `more`. |
| `get_licenses(datasets)` | `items` (licence name and count, most common first) and `unlicensed`, over the public datasets. |
| `get_citation_details()` | `text`, `link`, `has_doi` and `creators`. |
| `get_readiness(page)` | The checklist: `items`, `done`, `total` and `percent`. The project checklist has ten items. |
| `get_details(licenses)` | The rows of the Details card. |
| `get_shared_context(page)` | The entries every overview provides. |

Context entries: `project`, `can_manage`, `descriptions`, `timeline` (from `get_progress()`), `team`, `funding`, `counts`, `datasets_preview`, `licenses`, `composition_chart`, `growth_chart`, `citation`, `json_ld`, `api_url`, `urls`, and for the team `readiness`, plus the shared entries.

`project_is_visible(request, obj)` in the same module is the plugin's `check`: a public project is visible to all and a private one to holders of `project.view_project`.

## Dataset `Overview`

| Attribute | Default | What it sets |
|---|---|---|
| `bookkeeping_fields` | a set of field names | Fields every record carries that say nothing about its data, left out of `get_record_types()`. |

| Method | Returns |
|---|---|
| `get_access()` | `state` (`private`, `public` or `published`) and its `label`. |
| `get_descriptions()` | The descriptions the dataset has text for, in the vocabulary's order. |
| `get_dates()` | `collection_start`, `collection_end`, `available`, `submitted`, `published` and `withdrawn`, each `None` or a partial date, and `withdrawn_text`. |
| `get_lifecycle(dates)` | The timeline's steps, in the order they happened. |
| `get_team()` | `creators`, `has_contact` and `total`. |
| `get_literature()` | `items`, each with `relation` (worded from the publication's side), `item`, `doi` and `year`. |
| `get_record_types(samples, measurements)` | One dictionary per registered type the dataset holds, with `kind`, `label` and the labels of its `fields`. |
| `get_counts(samples, measurements, data_types)` | The counts of samples and measurements, each with a `_desc` line. |
| `get_project_info()` | The project and how many other datasets in it the viewer may see, or `None` when the viewer may not see the project. |
| `get_citation_details(page)` | `text`, `link`, `has_doi`, `from_reference` and `creators`. |
| `get_schema_org(page)` | The schema.org `Dataset` description for the page head. |
| `get_readiness(page)` | The checklist: `items`, `done`, `total`, `percent`, `ready` and `missing_required`. It has seven required and three recommended items. |
| `get_details(project_info)` | The rows of the Details card. |
| `get_shared_context(page)` | The entries every overview provides. |

Context entries: `dataset`, `can_manage`, `access`, `descriptions`, `dates`, `team`, `literature`, `data_types`, `counts`, `composition_chart`, `growth_chart`, `project_info`, `api_url`, `urls`, `citation`, `json_ld`, `lifecycle`, and for the team, while the dataset's data is not public, `readiness`, plus the shared entries.

`dataset_is_visible(request, obj)` is the plugin's `check`.

## Sample `Overview`

| Attribute | Default | What it sets |
|---|---|---|
| `lifecycle` | a list of steps | The steps of a sample's history, each `(date_type, role, description_type, label)`, by address. Replace it in a subclass. |
| `status_variants` | a dictionary | The badge colour of each custody status. |
| `status_meanings` | a dictionary | What each status means for re-examining the specimen. |
| `measurements_shown` | `10` | Measurements listed before the rest are counted. |

| Method | Returns |
|---|---|
| `get_status()` | `value`, `label`, `variant` and `meaning`. |
| `get_measurements()` | The measurements the viewer may see: `items`, `total` and `more`. Each item has `measurement`, `type` and `elsewhere`. |
| `get_related_samples()` | `items`, `parents`, `children` and `hidden`, the number of relations the viewer may not see. |
| `get_relations_summary(relations)` | A caption such as "1 parent · 2 subsamples", or "None recorded". |
| `get_citation_details(entries, dates, identifiers)` | `title` and `text`, with a `note` when the sample has no IGSN. |
| `get_details(project, status)` | The rows of the Details card. `project` is `None` when the viewer may not see it. |

Context entries: `sample`, `record`, `can_manage`, `sample_type`, `status`, `lifecycle`, `notes`, `measurements`, `relations`, `location`, `project`, `counts`, `citation`, `identifiers`, `api_url`, `type_info`, `people` and `details`.

## Measurement `Overview`

| Attribute | Default | What it sets |
|---|---|---|
| `procedure_steps` | a list of steps | The steps of how a measurement was made, each `(date_type, role, description_type, label)`, by address. Replace it in a subclass. |
| `siblings_shown` | `8` | Rows in the list of other measurements on the same sample. |

| Method | Returns |
|---|---|
| `get_result()` | A dictionary with `text` when the type declares a `value`, else `None`. |
| `get_sample_status()` | The sample's status `label` and `variant`, or `None` when it records none. |
| `get_siblings()` | The other measurements on the same sample that the viewer may see: `rows`, `more` and `total`. |
| `get_citation_details(entries, dates, identifiers, sample)` | `title` and `text`, with `note`, `note_url` and `note_link` when there is no DOI. `sample` is `None` when the viewer may not see it. |
| `get_details(project)` | The rows of the Details card. |
| `get_page_title()` | The measurement's name, else its portal ID. |

Context entries: `measurement`, `record`, `record_title`, `can_manage`, `measurement_type`, `result`, `type_info`, `procedure`, `notes`, `sample`, `sample_type`, `sample_status`, `sample_visible`, `effective_location` (from `Measurement.effective_location_for(user)`, with `point`, `elevation`, `uncertainty` and `source`), `other_dataset`, `siblings`, `project`, `citation`, `identifiers`, `api_url`, `people` and `details`.

## Contributor `Overview`

One plugin serves the person page and the organization page and chooses the template by `is_organization`. It does not subclass `RecordOverviewPlugin`.

| Attribute | Default | What it sets |
|---|---|---|
| `collaborators_shown` | `18` | Faces in the Frequent collaborators card. |
| `records_shown` | `5` | Projects, and datasets, listed in each record card. |
| `member_slots` | `10` | Places in the Members card, the "+n" entry included. |

| Method | Returns |
|---|---|
| `get_record_card(entries, active=None)` | A Projects or Datasets card's data, active records first and then the most recently updated, cut to `records_shown`. |
| `get_readiness(items, title, about, badge)` | A checklist shaped for [`c-card.readiness`](components.md#c-cardreadiness). |
| `get_shared_context()` | `record`, `identifiers`, `identifier`, `identifier_url`, `links`, `languages`, `json_ld`, `api_url` and `urls`. |
| `get_person_context()` | The person page's context. |
| `get_organization_context()` | The organization page's context. |

Person context entries: `person`, `is_self`, `can_edit`, `update_url`, `is_unclaimed`, `is_inactive`, `affiliations`, `primary_organization`, `location_text`, `orcid_verified`, `portal_roles`, `people`, `counts` (with `project` and `dataset`), `projects`, `datasets`, `roles`, `member_since`, and, for the person themselves, `readiness`.

Organization context entries: `organization`, `can_manage`, `can_edit`, `update_url`, `is_member`, `members`, `projects`, `datasets`, `org_counts`, `hierarchy`, `location_text`, `has_map`, and, for the people who keep the record, `readiness`.

Models supply the data: `Person.get_affiliation_history()`, `Person.get_profile_completeness()`, `Organization.get_current_memberships()`, `Organization.get_hierarchy()`, `Organization.get_public_projects()`, `Organization.get_public_datasets()`, `Organization.get_record_completeness()`, `Organization.is_managed_by(user)` and `Organization.is_editable_by(user)`.

## Helper functions

`fairdm.core.overview`:

| Function | Returns |
|---|---|
| `format_authors(contributors)` | Creators in citation style: `Keller, A., Oliveira, T. & Brandt, L.` |
| `author_name(contributor)` | One creator: surname and first initial, or the contributor's string form when there is no first and last name. |
| `json_ld(data)` | `data` serialised for an inline script element, with `<`, `>` and `&` escaped. |
| `as_date(partial)` | A plain date from a partial date, or `None`. Use it to sort and compare, never to show. |
| `format_partial_date(partial)` | A partial date as a day, a month and year, or a year, as it was recorded. |
| `sentence_case(text)` | The text with its first letter capitalised and the rest untouched. |
| `safe_reverse(name, **kwargs)` | A URL, or `None` when the name does not resolve. |

`fairdm.contrib.contributors.profiles`:

| Function | Returns |
|---|---|
| `ranked_shares(counts)` | `label`, `count` and `percent` for each count, largest first, where the largest is 100. |
| `fill_slots(items, slots, reserve=False)` | `shown`, `more` and `total`. With `reserve`, the last slot is kept for a "+n more" entry. |
| `active_then_recent(items, modified, active=None)` | The items with active ones first, each group most recently updated first. |
| `checklist(items)` | The items with `done`, `total` and whether all are done. |

## Visibility methods

A sample or measurement overview decides who may open a record through the base model's manager, never the type's own. `fairdm.core.managers.RecordVisibilityMixin` gives a queryset these methods:

| Method | Keeps |
|---|---|
| `published()` | The records whose own dataset is published. |
| `visible_to(user)` | The records in a dataset that is public and published, and those the user holds at least the view level on, on the record or from its dataset or that dataset's project. |
| `with_level(user, level)` | The records the user holds at least that level on. |

`SampleQuerySet` and `MeasurementQuerySet` have all three. A queryset of your own for a record with a `dataset` foreign key can use the mixin. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).
