# Sketch: autocomplete fields for records, people and organizations

## What exists

- Visibility comes from the querysets in `fairdm/core/managers.py` (`with_level`, `accessible_to`,
  `visible_to`) and `get_visible()` on projects and datasets. `Dataset.objects` already leaves
  private datasets out, and `Dataset.all_objects` holds every dataset.
- `Contributor.get_collaborators()` ranks people by shared records. A person's affiliations are
  `Person.affiliations`, and `primary_affiliation()` and `orcid()` give the details a result shows.
- django-mvp-forms 0.6.0 draws django-tomselect's four widgets as daisyUI selects. It also reads a
  result's `optgroup` key as its group heading, through its own `django_tomselect/tomselect.html`.
  That template wins only while `mvp_forms` sits above `django_tomselect` in `INSTALLED_APPS`.
- The portal has no page that creates a sample or a measurement (R16). The edit pages leave out
  the fields that would move a record to another dataset or sample, so no page shows those fields
  today.
- The generated list for a registered sample or measurement type shows a related-record filter
  only where the type's registration lists that field. The XRF measurement list has the dataset
  and sample filters. The rock sample list has neither.

## What the screens need from the code

- Each field needs an address per scope (public, view, edit), so a request cannot widen what a
  field offers by changing a parameter.
- A result needs its group, its name, one line of detail and an optional badge. A person or an
  organization also needs a picture or initials. django-tomselect's option templates only swap in
  values and cannot branch, so the server sends a class that hides an empty badge or a missing
  picture.
- Record results are ordered by group first (the person's own, then public, then anything else a
  portal-wide role shows), then by name. An exact local ID, identifier, ROR, ORCID or DOI comes
  before both.
- The measurement form's sample field needs the chosen dataset's id sent with every search, and
  needs to clear itself when the dataset changes.
- A public list's filter offers public records to everyone, signed in or not. The XRF list
  currently offers a signed-in person their private datasets, and the sketch removes that.
- The person filter groups by collaborators. It must count only records the person searching may
  open (FR-017). The sketch uses `get_collaborators()` as it is, and that method counts every
  shared record.
- The data publication search reads authors and the DOI out of each publication's stored CSL
  item, which has no index.
- django-tomselect's `AutocompleteModelView.__init_subclass__` gives every subclass empty
  `search_lookups` and `value_fields` unless the subclass declares its own, so a shared base class
  loses them. Its `page_size` can be raised by the request up to the library's maximum, which
  FR-022 does not allow.
- Every multiple field shows a count ("3 datasets") in place of chips, as django-mvp-forms'
  counted control does. django-mvp-forms draws the count from `data-none-text` and
  `data-count-text` on the control, but only its own `TomSelectMultiple` copies them there. For
  django-tomselect's widgets the sketch copies them in `fairdm/templates/django_tomselect/tomselect.html`.
  That copy belongs in django-mvp-forms.
- A search needs two characters, and the first page is still fetched when a field opens.
  django-tomselect refuses an empty search once a minimum length is set, so the sketch lets an
  empty search through in the same template. That belongs in django-tomselect or django-mvp-forms.
- A result is drawn on the server, from `autocomplete/record_option.html` and
  `autocomplete/contributor_option.html`, and sent as HTML. FairDM's copy of django-tomselect's
  `render/option.html` shows that HTML as it is. A person and an organization use
  `c-contributor.avatar` and the affiliation line's organization icon, with no links inside the row.
- The tag field takes `allow_new`. A form that records tags turns it on, and a filter by tags
  leaves it off.
- django-tomselect shows its own red error box when a search fails, in fixed colours outside the
  daisyUI theme. FR-021 needs a "searching is paused" message in the theme instead.

## What the sketch faked

- `fairdm/contrib/autocomplete/records.py`, `records_fields.py` and `sketch_pages.py`: untested
  code, rebuilt test-first in the build.
- Two stand-in create pages at `/autocomplete/sketch/new-sample/` and
  `/autocomplete/sketch/new-measurement/`. They draw the sample and measurement forms limited to
  the name, dataset and sample fields, and they save nothing.
- `seed_autocomplete_sketch`, a management command that seeds organizations with ROR
  identifiers, people with ORCID identifiers, two unclaimed people, a private project and two
  private datasets for the regular user, thirty public datasets, twelve samples with local IDs
  and IGSNs, publications with DOIs, and tags.
- No request limits, no cap on search length or page depth, and no "searching is paused" message
  (FR-020 to FR-025).
- No field yet for a stored link to a private record the editor cannot see (FR-012).
- The filter on a profile's own list (FR-009) is not built. The profile's project list shows
  public projects only today.
- The ROR lookup is not moved off django-select2's script.
- The keyword filters on the project list still use django-autocomplete-light. They raise
  "jQuery is not defined" there, as they already do on main.
- django-autocomplete-light, django-select2 and django-addanother are still installed. Every
  field the sketch did not touch still uses them.

## What was ruled by eye

- Multiple fields show a count, never chips. Chips are only for tag fields (round 1).
- A person's ORCID sits on its own line beneath their affiliation. An organization's ROR sits
  beneath its place (round 1).
- Result text starts at the left of the row (round 1).
- Adding a new tag is allowed in forms and never in filters (round 1).
- A search needs two characters, and the first page loads when a field opens (round 1).

Still open to his eye:

- Group headings read "Your datasets", "Public datasets", "People you have worked with",
  "Everyone else", "Your organizations" and "Other organizations".
- A list with only one group shows no heading, so a public filter is a plain list.
- A record result is a name over one line of muted detail, with a small ghost badge on the right
  for "Private" or "Unclaimed", and the DOI as an outline badge on a publication.

