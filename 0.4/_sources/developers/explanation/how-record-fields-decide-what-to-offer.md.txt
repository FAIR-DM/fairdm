# How record fields decide what to offer

This page explains why a record field offers the records it does, why it accepts only those, and what it shows for a record the person using it may not see. It covers the reasoning. It does not list the fields, arguments and addresses, which are in [Record fields](../reference/record-fields.md), and it does not describe how to add one to a form, which is in [How to add a record field to a form](../how-to/add-a-record-field-to-a-form.md). Who may open a record in the first place is decided elsewhere, in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## A field is a search box that must not leak

A field that chooses a project, dataset, sample or measurement is a search box over records, and a search box is a way to read them. A person who types "granite" and sees a private dataset's name has learned that the dataset exists, even if they cannot open it. So a field never offers a record by name unless its user may see that record.

The same is true of a filter on a public list. A filter is a second way to read the list, so a name that the list withholds from a cell must not be available from a dropdown beside it. [ADR 0015](../../adr/0015-a-records-own-dataset-decides-and-a-row-never-links-past-it.md) records that rule for listings, and the fields apply it to every choice they draw.

## What a field offers depends on what it is for

How much a field may offer depends on what the form does with the choice.

- A field that places a record inside another needs the right to change the record it places it in. A sample cannot be put in a dataset the person may only read, so the dataset field offers the datasets the person may edit (`edit`).
- A field that links to a record needs only the right to see it. It offers public records and the ones the person may view (`view`).
- A filter on a public list offers public records to everyone (`public`), whoever is signed in, because a filter on a public page must never reveal a private record.

These three are the scopes. A fourth, `profile`, serves one person's records, for a filter on a list of what that person has done. Their private records are offered only to them.

## The scope belongs to the address

Each scope has an address of its own, so a request cannot ask for more than its address offers. FairDM could have taken the scope from a query parameter, but then a request could ask for a wider one. A separate view class for each scope turns the question "which records does this page offer?" into "which address does it call?", and the answer is fixed when the field is created. [ADR 0038](../../adr/0038-each-autocomplete-scope-is-its-own-view.md) records the decision and the library behaviour that made it necessary.

## A field accepts only what it would have offered

A field could trust the browser, which can only send a key it was offered. It does not. A form is a request like any other, and a person can post any key they like. So a field accepts a value only when it would have offered that record to the same person, and it refuses any other record with `invalid_choice`.

This check does not use the validation django-tomselect provides. That validation rebuilds the view without the arguments the field gave it, and with the query string of the page the form is on. A scope set when the field was made would be lost, and a page's own search would narrow what the check allowed. The field instead asks its own view, for the request's user, with the field's own settings. [ADR 0037](../../adr/0037-autocomplete-fields-are-built-on-django-tomselect.md) records why FairDM builds every field on one library.

## A stored link to a record the person cannot see is kept

A record can point at something its editor may not see. A measurement may name a sample from another dataset, and the editor of the measurement may have no part in that dataset. If the field dropped that value, saving the form unchanged would delete the link without anyone choosing to.

So the field accepts the value that is already stored, and shows it as "Private record" with no name. It never offers that record in a search. The person can keep the link, or replace it, and learns nothing about what it points to.

## Records are grouped by whose they are

Results come in groups: the person's own, then public records, then any further records a portal-wide right lets them see. A person looking for a record usually looks for one they work on, so those come first. A record appears once, in its first group.

A record typed exactly by UUID, local ID or identifier is listed first. A person who pastes an identifier already knows what they want, and it should not depend on how many records share a name.

## Narrowing and preferring are different questions

`depends_on` narrows. When a form asks for a dataset and then a sample, a sample of another dataset is a mistake, so the field offers only the chosen dataset's samples, and on submit it refuses any other.

`prefer` only orders. A measurement may be made on a sample that belongs to another dataset, because provenance crosses dataset boundaries. The measurement form's sample field lists the chosen dataset's samples first, since those are the likely ones, and still accepts any sample the person may view. Narrowing there would forbid a valid record, and ordering alone would not.

Both read the other field's value from the form's own data on submit, never from the page's address. A value in the address is something the visitor can edit, so it cannot be the thing that decides what a field accepts.

## People and organizations are public, with nearness first

A person's name and an organization's name are public information in a portal, so these fields have one scope, and one address serves everyone.

Results put the people closest to the searcher first, because the person most often wanted is someone the searcher works with. Two people have worked together when both are credited on a record the searcher can open. A credit on a private record the searcher cannot open does not count, so the grouping reveals nothing about records the searcher has no access to. Organizations the searcher belongs to come first for the same reason, and a pending affiliation does not count as belonging.

An email address is neither searched nor shown, so a result carries a name, an affiliation and an ORCID iD and nothing more personal.

## Tags reveal no record

A tag is a word, not a record, but a tag in use on exactly one private record would reveal something about it. A tag is therefore offered only when it is in use on a record that the record fields of the same scope would offer. A tag in use on no record is not offered, and a field that does not allow new tags refuses it.

## What one request can cost is fixed

The addresses serve public pages, so anyone can call them. Each view fixes what a request could use to make a search expensive or revealing: 20 results a page, no page past the 25th, a search cut to 100 characters, and only the filters and ordering the view names. Each caller is also limited over a minute and over a day. [ADR 0039](../../adr/0039-autocomplete-addresses-are-limited-per-caller.md) records the decision, and [How API callers are limited](how-api-callers-are-limited.md) explains the two limits.
