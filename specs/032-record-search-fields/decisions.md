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

## D2. A public list's filter offers public records to everyone

The maintainer's ruling: a public list, such as the portal's project or dataset list, shows public
records to everyone, so its filters offer public records to everyone, signed in or not. A signed-in
researcher gets no private records there, because the list would never show them. A list of one
person's records, such as the projects on their profile, is different: that person sees their
private records as well as the public ones, and everyone else sees the public ones only. Its filter
follows the list. The current django-autocomplete-light views return nothing to anyone not signed
in, which cannot stand for filters visitors use.

## D3. Visibility rules are taken as they are

The rules differ between record types today: a dataset is public when it and its project are
public, while a sample or measurement also needs its dataset to be published. These fields follow
whatever rules FairDM applies when they are built. Bringing the rules into line is R14, and doing
it here would make this feature a second owner of visibility.

## D4. A stored link the person cannot see is kept

A project manager may edit a record that links to a private record they have no access to. Dropping
the link on save would destroy someone else's data. Showing its name would leak it. The field shows
it as a private record and keeps it when the form is saved unchanged. Validation treats the value
already stored on the record as allowed, and every other value must be one the field would offer.

## D5. Groups follow how the person relates to the result

Records group as the person's own, then public, then anything else a portal-wide role lets them
see, because a researcher almost always chooses among their own records. People group by
collaboration, which `Contributor.get_collaborators()` already defines and limits to records the
viewer may open. Organizations group by membership, as `CONTEXT.md` defines it. A record appears
once, in its first group, so a list never repeats itself.

## D6. People are never found by email

An email address is personal data that a profile does not publish. Searching by it would let anyone
confirm whether an address belongs to a portal user. Unclaimed profiles are marked instead, which
answers the question searching by email would have been used for: whether this person is already
in the portal.

## D7. Vocabulary concepts keep working through a stopgap

Concepts are out of scope because django-controlled-vocabularies will provide a dedicated field.
Removing django-autocomplete-light now would break the keyword filters and the contribution roles
field in the meantime. They move to django-mvp-forms' tom-select widget that needs no view, which
lets the library go in this feature and costs one swap when the concept field lands.

## D8. Data publications, tags and the ROR lookup are in scope

None of them is one of the six record kinds, but each runs on a library this feature removes, so
leaving them out would leave the removal undone. #304 names the data publication field as the one
that most needs a search.

## D9. The admin moves to Django's own autocomplete

Admin pages are used by staff and already rely on `autocomplete_fields` in several places. The few
that use django-autocomplete-light or django-select2 move to it, rather than to the new fields,
because the admin has its own widget and styling and gains nothing from the portal's.

## D10. Creating a record from inside a form is deferred

#304 asked whether the "add another" capability stays. It is not part of this feature: none of the
fields needs it to be useful, and it brings its own questions about permissions and partially
filled forms. It is listed among the needs expected later, so the fields are designed not to rule
it out.

## D11. The broken widgets are replaced, not repaired

The dataset search on `title`, the two missing addresses, the organization search's `label` and
the unused `data-depends-on` attribute all sit in code this feature removes. Fixing them first
would be work thrown away.

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
