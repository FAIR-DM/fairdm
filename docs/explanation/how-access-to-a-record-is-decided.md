# How access to a record is decided

This page explains how a FairDM portal decides who may see and change a project, dataset, sample or measurement, and what the three refusals (a 404, a request to sign in, a 403) tell you. It covers the reasoning and the order in which the questions are asked. It does not tell you how to give someone access, which is a task covered in [How to let a colleague into a private record](../users/contributors/let-a-colleague-into-a-private-record.md), and it does not list the code that answers each question, which is in [Contribution levels and record access](../developers/reference/contribution-levels-and-record-access.md).

## Four separate questions

Access is not one switch. A portal asks four different questions, and each has its own answer.

| Question | Decided by | Applies to |
|---|---|---|
| May this person read that the record exists? | The record's visibility, or a level the person holds on it | A project or dataset page |
| May this person see the data beneath it? | Whether the dataset is published | Samples and measurements |
| May this person change it? | A level on the record, or a portal role | Every record |
| May this person do something to the portal itself? | A portal role | People, organizations, profile claims, the administration interface |

Keeping them apart is deliberate. A researcher can describe their work publicly without releasing the data, and the person who looks after accounts does not need to read anyone's samples.

## Visibility and publication are different flags

A project and a dataset each have a visibility, either private or public. A new record is private. Visibility decides whether the record's own page, and the metadata on it, may be read by anyone who is not on its team.

A dataset also has a separate `published` flag. Publication decides whether the samples and measurements held in the dataset may be shown. It is set in the administration interface and nowhere a researcher can reach, so releasing data is never one click on the dataset page. Every dataset starts unpublished.

Neither flag implies the other. These are all ordinary states:

- A public dataset that is not published. Its description, counts and charts are open to everyone, and its records are not.
- A published dataset that is private. Its records belong in portal-wide listings, but its own page is closed to people outside the team.
- A dataset that is both public and published. This is the state in which everyone may see its samples and measurements.

A sample or measurement has no visibility of its own. It follows its own dataset: anyone may open it when that dataset is public and published, and otherwise only people who hold a level on it, or on its dataset or project, may. A record's presence is decided by the dataset that owns it, never by a dataset it merely refers to. A measurement can be made on a sample in a different dataset, and the two datasets are judged separately. The reasoning is in [ADR 0014](../adr/0014-publication-is-a-separate-flag-from-visibility.md) and [ADR 0015](../adr/0015-a-records-own-dataset-decides-and-a-row-never-links-past-it.md).

## Contribution levels

Who may do what on a particular record is a single level, stored on the person's credit for that record. There are three, and each includes the one before:

| Level | What it allows |
|---|---|
| Can view | Open the record and every page of it, even while it is private |
| Can edit | Also change the record and the data in it |
| Can manage | Also change who is credited and at what level, change the record's visibility, publish it, and delete it |

No level lets a person delete a record without being able to change it.

A level travels downward. A level on a project applies to its datasets, and a level on a dataset applies to its samples and measurements. A measurement follows its own dataset, not the dataset of its sample. A level never travels upward: someone listed only on a dataset cannot open its project, even when the project is private. Where a person holds a level on a record and another from a record above, the higher one applies.

Organizations hold no level. Being a member or owner of an organization that is credited on a record gives no access to it.

A contribution role, such as the one that says someone collected the data, describes how a person took part. It never gives or removes a level.

### Why one level, not a set of permissions

The Contributors tab has to show what each person may do, and has to let a manager choose it. A level can be read and chosen. A set of independent permissions allows combinations that nobody can reason about, such as being able to delete a dataset but not open it. Leaving permissions stored per person and per record in force beside the levels would also have kept a second way into a private record that the tab does not show, so those stored permissions grant nothing on these four kinds of record. The full argument is in [ADR 0025](../adr/0025-a-level-on-the-contribution-decides-rights-over-a-core-record.md).

A consequence is that rights over a core record cannot be given to a group. If you need that, the group would have to appear on the Contributors tab, which is a feature of its own.

### A record always keeps a manager

The portal refuses to remove the last person who can manage a record, or to lower them below manage, and it refuses to move a record to a parent where nobody could manage it. Only a person who can sign in and holds the manage level on the record, or on one above it, counts. Someone who can act only through a portal role does not count, so a record never depends on portal staff to stay manageable. The refusal applies to everyone, a superuser included.

## Portal roles

A portal role answers a different question: what may this person do across the whole portal, whoever is credited on a record? FairDM ships four. Their stored names are Portal Administrator, Data Curator, Community Manager and Developer.

| Role | Looks after | Rights over records |
|---|---|---|
| Portal Administrator | The portal's identity and who holds which role | None |
| Data Curator | Every project, dataset, sample and measurement | View, add, change and delete any of them, import data, and publish |
| Community Manager | People, organizations, affiliations, profile claims and merges | None |
| Developer | Nothing. It names the people who build the portal on its team page | None |

The roles are separate because looking after people is not the same job as looking after records. The person a research group trusts with its sample data is not automatically the person they want reading account records. A small portal can put one volunteer in both roles at no cost. See [ADR 0019](../adr/0019-a-portal-role-is-the-unit-of-portal-wide-rights.md).

A role and a level combine by addition. A person who holds both has everything either gives them. A role never changes what a level allows, and a level never gives a right over other records. A Data Curator therefore opens, edits and manages the contributors of any record without being listed on it, and doing so does not add them to the record.

Portal-wide rights apply to individual records only through these four roles. A permission granted straight to a person, or through a group a portal made up for itself, is not turned into a right over a particular record. A person holding only such a model-wide permission is refused on a private record's editing pages, because a page that inherited its visibility rule from the model would not be guarded.

A superuser holds every permission, and is a flag for whoever deploys the portal rather than a role. A superuser cannot be credited on a record.

### Roles are protected

The four roles cannot be deleted or renamed through the portal. If one goes missing anyway, bringing the database up to date installs it again with its rights. A portal in production refuses to start while a role is missing and names which one. The reasoning, including why a single hard refusal could not work, is in [ADR 0020](../adr/0020-a-missing-role-is-answered-four-ways.md).

### Profiles and claims

Editing a person's or an organization's profile is not decided by a model permission either. The record is asked. A person with an active account edits their own profile. A Community Manager edits an organization's profile and the profile of any person nobody can sign in as. An organization's owner and current administrators also edit its profile. A superuser, and the holders of the other three roles, get no right to edit profiles from the portal's pages, although the administration interface is unchanged. See [ADR 0024](../adr/0024-the-right-to-edit-a-profile-is-asked-of-the-record.md).

Generating a profile claim link and merging one person into another belong to the Community Manager role rather than to superusers. A claim link is a credential and a merge destroys an identity, so neither is an ordinary staff operation, and a named role is exactly the person whose job this is. See [ADR 0021](../adr/0021-claims-and-merges-belong-to-a-named-role.md).

## What a refusal means

When you ask for a page you may not use, the portal answers in one of three ways. Which one you get depends on whether you could see the record at all.

| Answer | What it means |
|---|---|
| 404, "No dataset matches the given query" | You may not see the record. The portal answers exactly as it would for a record that does not exist |
| Sent to the sign-in page | You are not signed in, you may see the record, and the page needs a right you do not hold |
| 403 | You are signed in, you may see the record, and you do not hold the right the page needs |

The first answer is the important one. A 403, or a redirect to sign in, would confirm that something private exists at that address. So a private project, dataset, sample or measurement answers a stranger with a 404, whether or not they are signed in, and so does every page that belongs to it, including its Contributors tab and its editing pages.

The editing pages ask the questions in a fixed order on every request, so a save is refused as a page view is:

1. Someone who may neither see the record nor holds the right on it gets a 404.
2. A visitor who may see the record, and may not use the page, is sent to sign in.
3. A signed-in person who may see the record, and may not use the page, gets a 403.

On a public record, the same order produces a sign-in request or a 403 for a page you cannot use, because the record's existence is no secret.

The REST API follows the same reasoning. A request for a private record you cannot see is answered 404, and a request to change a public record you may see but not change is answered 403. Reading is open to anyone for public data, and every write needs a signed-in caller. Where one record refers to another you may not see, the reference is `null` rather than naming it. The status codes are listed in the [REST API reference](../developers/reference/rest-api.md).

## Listings never depend on who is looking

A portal-wide listing of a sample or measurement type shows the records held in published datasets, and shows the same rows to every viewer. Signing in changes nothing about it. A researcher does not see their own unpublished records mixed into a portal-wide listing. They find them on their dataset's page.

The alternative, showing each viewer what they are entitled to, costs more than it returns. Every listing becomes viewer-dependent, nothing can be shared between viewers, every filter's choice list has to be worked out per viewer or it leaks the existence of records the table excluded, and every column added later inherits the same obligation. A single rule can be checked with one assertion that holds for every viewer. See [ADR 0013](../adr/0013-a-listing-shows-published-records-only-for-everyone.md).

Two further rules follow from it:

- A row never links past what the visitor may read. Where a row would name or link a record you cannot read, the cell keeps its place and shows a placeholder. The sample column reads "Unpublished", and the dataset column keeps its icon without the link. A filter's choice list obeys the same test, so a name withheld from a cell is not offered from a dropdown beside it.
- A listing of projects shows public projects, and a listing of datasets shows public datasets. Neither depends on the viewer.

A placeholder is a meaningful state. Read it as "there is a record here that you may not read".

## Why every page states its own rule

A page that asks "may this person open me?" answers from its own declaration, not from the page it belongs to. The reason is that an inherited rule once failed silently. A page resolved its visibility rule from its class while the link to the owning page was attached only to the instance, so the lookup found nothing and fell back to an open default. A project's own page refused a user with 403 while its update page returned 200 for the same user.

A rule that silently does not apply is worse than no rule, because the page carrying it reads as guarded. So each page names both the permission it needs and the visibility rule it applies, even where the owning page says the same thing. Repetition here is intended. See [ADR 0012](../adr/0012-every-page-states-its-own-access-rules.md).

## Where to go next

- [Portal roles](../administrators/reference/portal-roles.md) lists what each role holds.
- [How to find why a user cannot see a dataset](../administrators/how-to/find-why-a-user-cannot-see-a-dataset.md) works through a missing-access report step by step.
- [Contributors](../users/contributors/contributors-tab.md) describes the tab where levels are set.
- [How contributor accounts and credits work](how-contributor-accounts-and-credits-work.md) explains the credit that carries a level.
