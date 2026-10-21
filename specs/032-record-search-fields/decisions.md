# Decisions: autocomplete fields for records, people and organizations

Rationale too long for the specification, and every ambiguity resolved while it was written.

## D1. What a field offers depends on what it is for

A field that places a record inside another needs edit access: putting a sample into a dataset
changes that dataset, so offering a dataset the person may only view would offer a choice the
save then refuses. A field that links to a record, such as a measurement's sample, needs view
access, because linking reads the other record and changes nothing in it. A filter on a list page
offers public records only, since a filter on a public page is the wrong place to learn that a
private record exists, and the list it filters already decides what the person sees. Each default
can be changed per field, which is what lets a developer build a "my datasets" filter or a
manager-only form.

**ADR:** docs/adr/0038-each-autocomplete-scope-is-its-own-view.md

## D2. A public list's filter offers public records to everyone

The maintainer's ruling: a public list, such as the portal's project or dataset list, shows public
records to everyone, so its filters offer public records to everyone, signed in or not. A signed-in
researcher gets no private records there, because the list would never show them. A list of one
person's records, such as the projects on their profile, is different: that person sees their
private records as well as the public ones, and everyone else sees the public ones only. Its filter
follows the list. The current django-autocomplete-light views return nothing to anyone not signed
in, which cannot stand for filters visitors use.

**ADR:** docs/adr/0038-each-autocomplete-scope-is-its-own-view.md

## D3. Visibility rules are taken as they are

The rules differ between record types today: a dataset is public when it and its project are
public, while a sample or measurement also needs its dataset to be published. These fields follow
whatever rules FairDM applies when they are built. Bringing the rules into line is R14, and doing
it here would make this feature a second owner of visibility.

**ADR:** none — follows rules owned by R14, nothing new to inherit

## D4. A stored link the person cannot see is kept

A project manager may edit a record that links to a private record they have no access to. Dropping
the link on save would destroy someone else's data. Showing its name would leak it. The field shows
it as a private record and keeps it when the form is saved unchanged. Validation treats the value
already stored on the record as allowed, and every other value must be one the field would offer.

**ADR:** none — a property of the fields, recorded in their reference page

## D5. Groups follow how the person relates to the result

Records group as the person's own, then public, then anything else a portal-wide role lets them
see, because a researcher almost always chooses among their own records. People group by
collaboration, which `Contributor.get_collaborators()` already defines and limits to records the
viewer may open. Organizations group by membership, as `CONTEXT.md` defines it. A record appears
once, in its first group, so a list never repeats itself.

**ADR:** none — presentation of results, recorded in the reference page

## D6. People are never found by email

An email address is personal data that a profile does not publish. Searching by it would let anyone
confirm whether an address belongs to a portal user. Unclaimed profiles are marked instead, which
answers the question searching by email would have been used for: whether this person is already
in the portal.

**ADR:** none — a privacy rule already set by FR-019 and tested

## D7. Vocabulary concepts keep working through a stopgap

Concepts are out of scope because django-controlled-vocabularies will provide a dedicated field.
Removing django-autocomplete-light now would break the keyword filters and the contribution roles
field in the meantime. They move to django-mvp-forms' tom-select widget that needs no view, which
lets the library go in this feature and costs one swap when the concept field lands.

**ADR:** docs/adr/0037-autocomplete-fields-are-built-on-django-tomselect.md

## D8. Data publications, tags and the ROR lookup are in scope

None of them is one of the six record kinds, but each runs on a library this feature removes, so
leaving them out would leave the removal undone. #304 names the data publication field as the one
that most needs a search.

**ADR:** none — scope of this feature only

## D9. The admin moves to Django's own autocomplete

Admin pages are used by staff and already rely on `autocomplete_fields` in several places. The few
that use django-autocomplete-light or django-select2 move to it, rather than to the new fields,
because the admin has its own widget and styling and gains nothing from the portal's.

**ADR:** docs/adr/0037-autocomplete-fields-are-built-on-django-tomselect.md

## D10. Creating a record from inside a form is deferred

#304 asked whether the "add another" capability stays. It is not part of this feature: none of the
fields needs it to be useful, and it brings its own questions about permissions and partially
filled forms. It is listed among the needs expected later, so the fields are designed not to rule
it out.

**ADR:** none — a deferral, listed among later needs in the spec

## D11. The broken widgets are replaced, not repaired

The dataset search on `title`, the two missing addresses, the organization search's `label` and
the unused `data-depends-on` attribute all sit in code this feature removes. Fixing them first
would be work thrown away.

**ADR:** none — local to this feature

## D12. Field addresses are public, so they are limited

The maintainer's ruling: these addresses serve public pages, so anyone can call them, and they must
stand up to someone hammering them. The API already limits each caller over a short window and over
a day, counted by account or by network address, with rates a portal sets. The field addresses get
limits of their own on the same pattern rather than sharing the API's, because a person typing
sends requests in quick bursts the API's rates were not set for, and a busy search box should not
use up someone's API allowance. Limits alone are not enough: a single request asking for ten
thousand results or a search text of ten thousand characters can be costly, so the field, not the
request, decides the page size, the search length, how deep the pages go and what narrowing is
allowed. A refused request is refused before any search runs, so being over the limit costs the
portal almost nothing.

**ADR:** docs/adr/0039-autocomplete-addresses-are-limited-per-caller.md

## D13. Design review: five high findings applied to the plan, two put to the maintainer

The design review returned five verified high findings. Three were plan faults and are fixed in
`plan.md` and `tasks.md`:

- django-tomselect rebuilds the view it validates against without its `as_view()` arguments, and
  with the current page's search and filter parameters. Each scope is now its own view class, and
  FairDM's fields validate through the view's `offered()` with their own settings.
- The person view accepted `e=` and `ordering=` on any field, which could test whether an email
  belongs to a user. django-tomselect's own allow-lists replace the custom one.
- The ROR and tag fields could not save a ROR ID or a new tag, because django-tomselect validates
  against an unsearched list. Both fields validate by form instead.

Every medium and low finding was taken: limits and caps on all seven views, both fields defaulting
to `view`, one profile address per kind, tags drawn only from records the requester may view, a
fallback rate when a portal's settings lack a scope, the merge page's script, the demo's
django-select2 uses, a timed seed for SC-002, and four smaller edits.

The two spec findings (the "searching is paused" message of FR-021, and FR-018 still naming an
organization's ROR after the sketch removed it) went to the maintainer as a delta brief.

**ADR:** docs/adr/0038-each-autocomplete-scope-is-its-own-view.md

## D14. The autocomplete rates live on their throttle classes, not in the API's rate dictionary

**Decision**: The four autocomplete throttles carry their default rates as `default_rate` and
read `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` only when a portal gives a scope there.
`fairdm/api/settings.py` is unchanged.

**Why**: `tests/test_api/test_throttling.py` pins that dictionary to exactly the API's four scopes
(`test_the_four_throttles_are_the_ones_the_api_applies`), and a test written for another story
cannot be edited here. The fallback the plan asks for already gives a portal the defaults without
any entry, and a portal that wants other figures adds the four scopes to its own dictionary.

**Revisit if**: that test is widened to the eight scopes, when the defaults can move into the
shipped dictionary beside the API's.

**ADR:** docs/adr/0039-autocomplete-addresses-are-limited-per-caller.md

## D15. A form built with no request keeps the queryset it was given

**Decision**: A record field used outside any request (a script, a test) validates against
`field.queryset` as the form left it. By default that queryset is empty. `DatasetForm` leaves
every project there when it is built with no request, as its docstring has always said.

**Why**: `DatasetForm` validated against every project when built without a request, and tests
already pin that. The sample and measurement forms assign nothing, so they offer nothing then.

**Revisit if**: a caller builds a form without a request and expects the person's own records.

**ADR:** none — an implementation detail of the fields

## D16. Tests that pinned the old dataset and project widgets are replaced across six files

**Decision**: The tests expecting the add-another wrapper or a plain select on the sample,
measurement and dataset forms were rewritten to expect the new fields. They sit in the sample,
measurement and dataset form tests, `test_sample/test_config.py` and `test_registry/test_factories.py`.
The two classes that only checked the add-another URL were removed with the wrapper.

**Why**: Each one asserted the widget of a field this story moves, so each had to change with it.
Nothing else in those files was touched.

**Revisit if**: a reviewer wants the registry and config tests kept for the generated-form story.

**ADR:** none — test housekeeping

## D17. Each concrete record view names its own value_fields

**Decision**: `SampleAutocompleteView` and `MeasurementAutocompleteView` each set
`value_fields = DATASET_RECORD_FIELDS` on their own class, not on their shared base.

**Why**: django-tomselect's `__init_subclass__` replaces `value_fields` with an empty list on any
subclass that does not set it in its own `__dict__`, so a base class's list never reaches the
concrete view and the rows came back without type, local ID or dataset.

**Revisit if**: django-tomselect inherits the list.

**ADR:** none — a workaround for a library quirk inside the views

## D18. The measurement form refuses a sample of another dataset

**Decision**: `MeasurementFormMixin.sample` is `SampleChoiceField(depends_on="dataset")`, which
accepts only a sample of the dataset submitted with the form (AS 2.5). The older test
`test_form_handles_cross_dataset_sample_reference` and the portal docs on cross-dataset
measurements assume the opposite. The test was not edited and now fails.

**Why**: the brief and AS 2.5 require the refusal; the test is not one this story may change.

**Revisit if**: cross-dataset measurements are to stay possible through forms. Then `depends_on` for
the measurement's sample is dropped, or the old test and docs are rewritten.

**ADR:** none — superseded by D27 after the maintainer's ruling

## D19. A filter hands its field the filter set's request

**Decision**: `RecordMultipleFilter.field` sets `given_request` on the field it builds, from the
filter set's own request. The field reads its person from the form's request, then
`given_request`, then the current request.

**Why**: a django-filter form has no `request`, so a filter set built with `request=` in a script, a
test or a view that skips the middleware would otherwise offer and accept nothing.

**Revisit if**: the filter set's form carries the request, as FairDM's own record forms do.

**ADR:** none — an implementation detail of the filters

## D20. The API swaps a record filter for a plain one

**Decision**: `DatasetFilterSet.match_relations_on_uuid` replaces a `RecordMultipleFilter` with the
plain `ModelMultipleChoiceFilter` that `RecordMultipleFilter.for_api()` returns, over the records
the filter offers at its scope, and then matches on `uuid` as it does for any relation filter.

**Why**: the field behind a record filter keys its choices on the database number and has no control
to draw in the API. The API matches records by short identifier. The mixins' own dataset and sample
filters never reach the API, because the API's filter sets come first in the bases and declare their
own.

**Revisit if**: the API takes the record field's choices directly.

**ADR:** none — local to the API's filter sets

## D21. The no-vocabulary keyword list is left as it is

**Decision**: the generic `keywords` filter used when no vocabulary is configured keeps its checkbox
list. The per-vocabulary keyword filters are `TomSelectMultiple(counted=True)`, and the project
list's owner and contributor filters are record filters over the organization and person fields.

**Why**: the generic list never used django-autocomplete-light.

**Revisit if**: a portal with no vocabulary configured has enough keywords to need the counted control.

**ADR:** none — left as it was

## D22. Tests that offered private records through a list filter changed with the scope

**Decision**: in `test_sample/test_filters.py`, `test_dataset/test_filters.py`, `test_dataset/test_views.py`,
`test_measurement/test_filters.py`, `test_collections/test_views.py` and `test_registry/test_factories.py`,
the tests that pinned a filter's `queryset`, passed a single value for a filter that is now multiple,
or expected a private record to be offered to someone who may view it, now read the field's offered
records, pass a list, and expect public records only.

**Why**: each pinned the type or the visibility of a filter this story moves to public scope.

**Revisit if**: a list filter is to offer a person's private records.

**ADR:** none — test housekeeping

## D23. People and organizations have one address and are offered at one scope

**Decision**: `PersonAutocompleteView` and `OrganizationAutocompleteView` share a base that is not a
record view. Each has the single address `autocomplete:person-public` and
`autocomplete:organization-public`. Their fields declare `scopes=("public",)`, so the single field
defaults to `public` like the multiple one and any other scope raises `ValueError`. The base answers
`for_scope()` with itself and `offered()` with every contributor of the kind (people without
superusers), so the shared field code needs no change beyond reading `scopes`.

**Why**: a person or an organization has no visibility, so there is nothing for a scope to decide.

**Revisit if**: a portal can hide a profile.

**ADR:** none — recorded in the reference page

## D24. A collaboration counts only through a record the searcher can open

**Decision**: the people listed first are `get_collaborators()` over the searcher's credits on records
the record views offer at the `view` scope. A credit with no level on a private record opens nothing,
so a person met only there is not grouped.

**Why**: AS 5.7. The profile page's list of visible credits answers a different question, what a
profile may name, and counts a private record the searcher holds as not visible.

**Revisit if**: `get_collaborators()` takes a queryset of records instead of credits.

**ADR:** none — follows the CONTEXT.md definition of collaborator

## D25. A filter naming `email` offers nothing, as any other field outside the allow-list

**Decision**: `f` and `e` naming `email` get the library's allow-list answer, an empty page, and
`ordering` naming it is ignored. Nothing special is written for `email`.

**Why**: the brief reads "change nothing". The ordering case does change nothing. For `f` and `e`
the allow-list already refuses the request, which is the answer every other address gives.

**Revisit if**: a filter on `e` that names a disallowed field should be dropped instead of refused.

**ADR:** none — follows from the allow-lists in ADR 0039

## D26. The person form no longer passes `is_current` when it adds an affiliation

**Decision**: `PersonCreateForm.save()` creates the affiliation with `organization` and `is_primary`
only. The form's "Current affiliation" checkbox is left in place and has no effect.

**Why**: `Affiliation` has no `is_current` field, so the old call raised `TypeError` whenever an
affiliation was chosen. The model has no way to record "past" without an end date.

**Revisit if**: the checkbox should ask for an end date.

**ADR:** none — a defect fix

## D27. A measurement may name a visible sample from another dataset

The maintainer kept FS-006's FR-006 on 2026-10-21: a measurement may name a sample from another
dataset. FS-032's FR-007 and FR-010 still hold: no field accepts a record its user may not see.
FS-006 says nothing about whether the person linking may see the sample. The one existing test of
the cross-dataset case created the other dataset with the factory's private default and gave the
user no access to it. That fixture detail is incidental to what the test checks. The test now gives
the user view access to the other dataset, and still asserts that the cross-dataset sample is
accepted. Linking a private sample nobody has let you see would name it to you, so it stays refused.

**ADR:** none — the meeting point of two specs' rules, recorded here and in the test

## D28. A tag is offered by the record's content type as well as its key

**Decision**: `TagAutocompleteView.offered()` matches a tag item to a record by the key and by the
content type of the record's model and its subclasses, never by the key alone.

**Why**: a tag item holds the record's key as text, and the keys of different tables are equal
integers. By key alone, a private dataset's tag was offered because a public project had the same
key. A test builds that case. Samples and measurements are tagged under their concrete subclass,
so the view takes every model that subclasses the record's model.

**Revisit if**: tagging moves to one table for all record kinds.

**ADR:** none — an implementation detail of the tag view

## D29. The publication view and field have no scope

**Decision**: `PublicationAutocompleteView` and `PublicationChoiceField` offer and accept every
literature item, and `for_scope()` on the view returns the view itself.

**Why**: a literature item has no visibility of its own, so no rule can narrow it. The field
still never calls django-tomselect's `clean()` (D13).

**Revisit if**: literature gains a visibility.

**ADR:** none — local to the publication field

## D30. The keyword page tests read the form's value, and the ROR field keeps the value as chosen

**Decision**: two existing keyword page tests read `option[selected]` out of the old tag widget's
markup. django-tomselect renders an empty `<select>` and fills the options with script, so they now
read the form's value on the page's context, and the `chosen` helper only they used is removed.
`RorChoiceField.clean()` returns the value stripped and otherwise as chosen, the ROR address
unchanged, since `Organization.from_ror()` takes either form.

**Why**: the brief lets tests that pin the replaced widgets change. The form's value is what the
page was showing as chosen.

**Revisit if**: the tag control's script-built options need a browser test.

**ADR:** none — test housekeeping

## D31. The ROR lookup shows the standard message when ROR is down

AS 8.3 asked the ROR field to say that the lookup is unavailable. django-tomselect shows one fixed
message for every failed search, the gap the maintainer agreed on 2026-10-21 for request limits
(FR-021). The ROR lookup takes the same ruling: the address answers 503, the field shows
django-tomselect's standard failure message, and the form still saves. The fourth gap in #554
covers both.

**ADR:** none — the same ruling as FR-021, applied to the second place it reaches

## D32. `owner` selects the profile address, `type` is a model, the multiple field defaults to view

**Decision**: a record field given `owner` (a person or a key) is served by one extra address per
kind, `autocomplete:<kind>-profile`, which reads `owner` from the request. The profile scope offers the
records the owner holds at least view on, private ones only when the person searching is the owner.
`owner` cannot be given with `scope`, and people and organizations take neither. `type` is the model
of a registered sample or measurement type; it is sent as a constant `polymorphic_ctype` filter, which
the views already allow, and validated through `offered(type=)`. Both single and multiple fields now
default to `view`, as plan D4 says; the list filters still pass `public`.

**Why**: the owner is a request-time fact the page cannot be trusted to name, so it lives on one
address and is checked again by `offered()` when the form validates. The multiple field defaulting to
`public` contradicted D4 and the T029 scenario of a multiple field offering a private record the
person may view.

**Revisit if**: a filter declared on a class needs the owner of the page it is drawn on. The field
takes `owner` at construction, so such a filter builds its field per request.

**ADR:** none — recorded in the reference page

## D33. The three libraries are gone from FairDM; django-select2 stays installed through django-mvp

**Decision**: django-autocomplete-light, django-select2 and django-addanother leave `pyproject.toml`, `INSTALLED_APPS`, the URL conf and the cache settings. `uv.lock` drops the first and third. django-select2 stays in the lock because django-mvp depends on it, so it is installed but nothing in FairDM, the demo, the tests or the docs names it. `suggest_widget` for a relation now answers the plain `Select` and `SelectMultiple`. The `.select2` rule in `fairdm/contrib/identity/static/configuration/admin.css` stays: Django's own admin autocomplete draws a `select2` element and the rule sizes it in the admin's flex rows.

**Why**: the migration guide tells a portal to declare any of the three itself. FairDM cannot remove a package another dependency requires.

**Revisit if**: django-mvp drops django-select2, or the admin stylesheet gets a rule of its own for the admin's autocomplete.

**ADR:** docs/adr/0037-autocomplete-fields-are-built-on-django-tomselect.md

