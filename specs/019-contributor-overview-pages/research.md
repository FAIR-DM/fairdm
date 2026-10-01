# Research: Overview pages for people and organizations

## The prototype is the design source

Both pages were reviewed with the maintainer over six rounds on a working prototype, and the
specification was written from what that review settled. Implementation starts from that code.

## What the prototype lacks

Measured on the merged branch (98a231c7) on 2026-10-01:

- 6 of 3,282 tests fail: five render an include the prototype replaced with a component, one
  expects the `account-center` address that changed with django-mvp 0.25.1.
- `deptry` reports `PIL` imported without being declared.
- The docs check reports six undocumented public names.
- The pages have no tests of their own, and neither do the model methods added for them.

## Findings in the existing code

- `Dataset.objects` is `DatasetManager`, which excludes private datasets
  (`fairdm/core/dataset/models.py`, `DatasetManager.get_queryset`). It does not look at the
  dataset's project.
- `ProjectQuerySet.get_visible()` returns public projects (`fairdm/core/project/models.py`).
- Samples and measurements share `visible_to(user)` (`fairdm/core/managers.py`).
- `AffiliationQuerySet.current()`, `.past()` and `.owners()` exist
  (`fairdm/contrib/contributors/managers.py`). `Affiliation.MembershipType` orders pending, member,
  administrator, owner.
- The contributor tabs `ContributorProjects` and `ContributorDatasets` return
  `self.base_object.projects.all()` and `.datasets.all()`, with no visibility filter
  (`fairdm/contrib/contributors/plugins/person.py`).
- `Statistics` and `Network` are registered on `Contributor` in the same module.
- Identifier resolver addresses for three types are wrong in `IdentifierLookup` (#386). The page
  reads `ContributorIdentifier.resolver_url`, which returns nothing for an address that is not
  `http`, so those types are listed without a link until #386 is fixed.

## Libraries

No new library. The organization's map uses the MapLibre include specification 018 added.
