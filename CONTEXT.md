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

A dataset's visibility is independent of its project's.

Implemented by `Dataset` in `fairdm/core/dataset/models.py`.

### Sample

The polymorphic base class every sample type inherits from. Portals define their own sample types
by subclassing it and registering them. `Sample` is never meaningfully instantiated on its own. It
is the shared schema, not a specimen.

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

## People, in three contexts

These are not three roles. They are three contexts in which the same `Person` record is discussed,
and conflating them is the most common source of confusion in this domain.

- **Person** — the record itself. Exists for attribution whether or not anyone ever logs in.
- **Portal user** — a person with an account on a running portal. May never have contributed data.
- **Contributor** — a person linked to a specific object through a `Contribution`. May never log in.

A fourth term, **framework contributor**, means someone who contributes to FairDM's own source
code. It is unrelated to any portal's research community, and should never appear in discussion of
portal data.

## Framework mechanisms

### Registry

How portal-specific models tell FairDM about themselves in order to receive generated admin
pages, forms, filters, list views and API endpoints. Registration happens through
`ModelConfiguration` classes and the `@register` decorator.

The split of responsibility is the point: the registry owns the plumbing, and the research team
owns the model class, its fields and its validation.

### Plugin

A unit of behaviour attached to a model's detail view, registered against one or more models. The
public API is what `fairdm/contrib/plugins/__init__.py` exports: `Plugin`, `register`, `registry`,
`is_instance_of`, `reverse` and `slugify`.

Plugin groups and tabs were removed from this system. Do not reintroduce either term.

### Polymorphic models

`Sample` and `Measurement` use django-polymorphic. Subtypes share one table and are distinguished
by `polymorphic_ctype`; queries return instances of the correct subtype without the caller asking.

### Visibility

`Visibility` is a two-value choice, `PRIVATE` (0) and `PUBLIC` (1), defined in
`fairdm/utils/choices.py`.

Access flows downward. A private project hides everything beneath it. Under a public project, each
dataset's own visibility decides, and samples and measurements follow their dataset.

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
