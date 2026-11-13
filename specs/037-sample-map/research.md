# Research

## Assumptions checked

Run before the specification was put up for approval, against the development stack seeded with
`seed_overviews` and `seed_overview_prototype`.

| Assumption | Result |
|---|---|
| `Project.spatial_coverage(user)` returns the box of a project's located samples and measurements for a visitor | Works. A seeded project gave a box of about 7.8° to 8.7° E, 48.8° to 49.2° N |
| `Dataset.spatial_coverage(user)` does the same for a dataset | Works. A seeded dataset gave a smaller box inside the project's |
| The project and dataset samples lists are routed (`project:samples`, `dataset:samples`) | Both resolve and the project's list answers 200 |
| The samples list gives each sample's latitude and longitude, which FR-021 relies on | It does: the list has latitude and longitude columns filled for each located sample |
| A located sample the visitor may open has a page | Yes, through `Sample.objects.visible_to(None)` and `get_absolute_url()` |
| The sample and measurement maps draw OpenFreeMap tiles with no key | Yes: `fairdm/templates/overview/includes/map_library.html` uses `tiles.openfreemap.org`, with MapLibre 5 pinned |

None failed.
