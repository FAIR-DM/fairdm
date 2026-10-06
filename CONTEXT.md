# CONTEXT.md — domain glossary

The vocabulary this codebase speaks. Use these terms, with these meanings, in issues, commit
messages, test names, specs and code. Where a term has a tempting synonym, the synonym to avoid
is named so that it does not creep back in.

Definitions here describe the code as it stands, not as it is planned to be.

## Core data model

### Project

The outermost container. A research initiative, grant or collaboration that groups related
datasets. Its schema is fixed, and portals do not extend it. In practice it is an administrative
grouping rather than a scientific one.

Implemented by `Project` in `fairdm/core/project/models.py`.

### Dataset

The unit of citation and distribution, aligned with DataCite. A discrete body of research data
(samples plus measurements) that can be formally published and attributed. Where one dataset ends
and the next begins is the research team's decision, not the framework's: they may split by
location, time, sample type, or any combination.

A dataset has a visibility of its own, which decides who may open it while its project is public.
A private project hides every dataset in it, whatever that dataset's own visibility is.

Implemented by `Dataset` in `fairdm/core/dataset/models.py`.

### Sample

The polymorphic base class every sample type inherits from. Portals define their own sample types
by subclassing it and registering them. `Sample` cannot be created at all — through the ORM, a
form, the admin, or a factory; every route refuses it. It is the shared schema, not a specimen.

Avoid "Base Sample" as a term. Earlier notes proposed renaming the class `BaseSample`; that rename
never happened, and the class is `Sample` in `fairdm/core/sample/models.py`.

### Measurement

A result or observation made on a sample. Also polymorphic, so portals define their own
measurement types. A measurement always references a sample, but may belong to a different dataset
than that sample does, which is what makes multi-team workflows possible.

Implemented by `Measurement` in `fairdm/core/measurement/models.py`.

### Contributor, Person, Organization

`Contributor` is the polymorphic base for everyone credited on FairDM content, with two concrete
subclasses: `Person` and `Organization`. It holds publicly visible attribution information,
following the DataCite contributor schema.

There is no separate "contributor profile" entity. A profile is the public-facing view of a
`Person` or `Organization` record, not a record of its own.

`Person` also subclasses Django's `AbstractUser`, so one model covers both the credited individual
and the portal account.

### Contribution

The link between a contributor and a specific project, dataset, sample or measurement. There is one
row per contributor per object, enforced by a uniqueness constraint on content type, object id and
contributor. Roles accumulate on that single row rather than producing duplicates.

A contribution carries a **level** for a person, which is what they may do on that record. There
are three, and each includes the one before it: **view** opens the record, even while it is
private; **edit** also changes the record and the data in it; **manage** also changes its
contributors and their levels, changes its visibility and deletes it. A new person starts at view.
`RecordLevelBackend` answers every permission question about a project, dataset, sample or
measurement from these levels, and permissions stored in django-guardian for them grant nothing.
The level is empty for an organization, which holds no access. A level on a project applies to its datasets, and a
level on a dataset applies to its samples and measurements, so rights flow from the record above
to the records beneath it and never the other way. Where a person holds a level on a record and
another from above, the higher applies. A contribution role carries no level and changes none.

A contribution carries the organization a person is credited from on that record, or none. It is
chosen when the person is added, defaults to their primary affiliation, and is kept with the record:
a later change to the person's affiliations does not change it. The organization is listed on the
record once, as its own contribution.

### Collaborator

Another contributor credited on the same project, dataset, sample or measurement as a given
contributor. Collaborators are ranked by how many records they share with that contributor, and
only records the viewer may open count: someone who shares nothing but a private record is not a
collaborator on a profile page. A collaborator may be a person or an organization.

Implemented by `Contributor.get_collaborators()` in `fairdm/contrib/contributors/models.py`.

### Profile maintainer

Whoever may edit a profile in the portal. For a person with an active account it is that person and
nobody else. For a person nobody can sign in to (a profile nobody has claimed, whose owner has not
yet signed in, or whose account has been deactivated) it is any person holding the Community Manager
role. For an organization it is its owner and administrators with a current affiliation, and any
Community Manager. A superuser and the other portal roles are not profile maintainers.

Implemented by `Contributor.is_editable_by()` in `fairdm/contrib/contributors/models.py`.

### Member

A person with a verified affiliation to an organization that has not ended. A pending request and a
former member are not members. Owner and administrator are kinds of member.

Implemented by the `Affiliation` model: a type of member or above, with no end date.

## People, in three contexts

These are not three roles. They are three contexts in which the same `Person` record is discussed,
and conflating them is the most common source of confusion in this domain.

- **Person** — the record itself. Exists for attribution whether or not anyone ever logs in.
- **Portal user** — a person with an account on a running portal. May never have contributed data.
- **Contributor** — a person linked to a specific object through a `Contribution`. May never log in.

A fourth term, **framework contributor**, means someone who contributes to FairDM's own source
code. It is unrelated to any portal's research community, and should never appear in discussion of
portal data.

## Roles

Two more terms both use the bare word "role", and neither is the other:

- **Portal role** — one of the four named rights a person can hold on a portal: Portal
  Administrator, Data Curator, Community Manager or Developer. Declared once, in code, on
  `PortalRoles` (`fairdm/portal_roles.py`), and installed into every portal's `auth.Group` table
  automatically every time its database is brought up to date. Avoid the bare word "role" for
  this; say "portal role".
- **Contribution role** — the credit a `Contribution` records for how a contributor took part in
  a project, dataset, sample or measurement (e.g. "Data Collector", "Editor"). It carries no
  rights of any kind and decides nothing about what its holder can do. What a person may do on one
  record is their **level** on it (view, edit or manage), which is a different thing.

A **rights-carrying role** is a portal role that holds at least one permission — today, the Portal
Administrator, Data Curator and Community Manager roles. Holding one gives access to the
administration interface; the Developer role holds no permissions and is not rights-carrying, so
holding only it does not.

## Framework mechanisms

### Registry

How portal-specific models tell FairDM about themselves in order to receive generated admin
pages, forms, filters, list views and API endpoints. Registration happens through
`ModelConfiguration` classes and the `@register` decorator.

The split of responsibility is the point: the registry owns the plumbing, and the research team
owns the model class, its fields and its validation.

### Plugin

A unit of behaviour attached to a model's detail view, registered against one or more models. The
public API is what `fairdm/contrib/plugins/__init__.py` exports: `Plugin`, `Card`, `Place`,
`Column`, `register`, `registry`, `is_instance_of`, `reverse` and `slugify`.

Plugin groups and tabs were removed from this system. Do not reintroduce either term.

A registration also names the place its plugin appears: an entry in the record's local navigation,
which is the default, an entry among the page actions, or a card in the overview.

### Page action

A plugin offered in a dropdown among the header buttons of a record's overview, in place of an entry
in the local navigation. It is served at its own address, and the dropdown lists exactly the actions
the visitor may open for that record. Choosing one takes the visitor to that address. The dropdown is
not drawn when there is nothing to list.

### Overview card

A plugin drawn as a card inside a record's overview, in the wide column or the side column. It has no
page, no address of its own and no entry in the navigation or the page actions. The overview draws
it only for a visitor its access decision admits, so nothing of it, its stylesheets and scripts
included, reaches anyone else. A card that raises is left out and the page is still served. Further
views it owns are refused to a visitor the card is hidden from.

### Manage menu

The menu on a record's overview that holds what people with rights over the record can do to it,
such as editing its details or deleting it. It is separate from the page actions, and a plugin does
not register an entry in it.

### Polymorphic models

`Sample` and `Measurement` use django-polymorphic. Subtypes share one table and are distinguished
by `polymorphic_ctype`; queries return instances of the correct subtype without the caller asking.

### Visibility

`Visibility` is a two-value choice, `PRIVATE` (0) and `PUBLIC` (1), defined in
`fairdm/utils/choices.py`.

Access flows downward. A private project hides everything beneath it. Under a public project, each
dataset's own visibility decides, and samples and measurements follow their dataset. A
contributor's page goes further and names only public projects and public datasets, for every
viewer. A person who holds a level on a record opens it whatever the visibility of the records
above it, and gains nothing over those records from it.

Some docstrings in the dataset layer still refer to an `INTERNAL` visibility. No such value
exists; treat those mentions as stale.

## Standing principles

1. **Configuration over code.** The registry handles plumbing; research teams write model classes.
2. **The research team decides the science.** Dataset boundaries, sample subtypes and measurement
   schemas belong to the domain, not the framework.
3. **Provenance crosses dataset boundaries.** A measurement may reference a sample in another
   dataset.
4. **Publication constrains deletion.** Published datasets are protected, as are the links from
   samples to their measurements.
5. **One attribution per contributor per object.** Roles accumulate on that row.
