---
myst:
  html_meta:
    "description lang=en": "Glossary of terms used in FairDM portals and their documentation"
    "keywords": "FairDM, research data, glossary"
---

(glossary)=

# Glossary

This page defines the terms a portal developer, administrator or user meets in a FairDM portal.
It does not explain how the parts fit together. For that, start with
[the core data model](../explanation/the-core-data-model.md).

:::{glossary}
:sorted:

Account state
    Where a {term}`person` stands with the portal. A person is a {term}`ghost`, {term}`invited`,
    {term}`claimed` or {term}`inactive`. The portal works the state out from the person's
    email address and flags each time it is needed. It is never stored.

Affiliation
    The link between a {term}`person` and an {term}`organization`. An affiliation has a type of
    Pending, Member, Admin or Owner. Pending means the organization has not yet verified it.

API token
    A secret a person creates on their account pages so that a script can call the portal's REST
    API as them. A script sends it in the `Authorization` header.

Claimed
    The {term}`account state` of a person who has taken over their profile and can sign in. See
    [how a profile is claimed](../explanation/how-a-profile-is-claimed.md).

Community Manager
    A {term}`portal role`. It lets the holder view and change people, organizations,
    affiliations and contributions across the portal.

Contribution
    One credit: a {term}`contributor` listed on one record, with the roles they played and the
    {term}`contribution level` they hold on it. Also called a credit.

Contribution level
    What a person may do on one record: Can view, Can edit or Can manage. Each level includes the
    ones before it. A person holds a level through their {term}`contribution` to the record or to
    the record above it. See
    [how access to a record is decided](../explanation/how-access-to-a-record-is-decided.md).

Contributor
    A {term}`person` or an {term}`organization` that can be credited on a record.

Controlled vocabulary
    A fixed list of terms, each with a definition, that a field accepts instead of free text.
    See [controlled vocabularies](../explanation/controlled-vocabularies.md).

Data Curator
    A {term}`portal role`. It lets the holder view, add, change and delete projects, datasets,
    samples and measurements, and publish datasets, across the whole portal.

Dataset
    A collection of {term}`samples <sample>` and the {term}`measurements <measurement>` made on
    them, held inside a {term}`project`. A dataset has a {term}`visibility`, a licence and a
    {term}`published` flag.

Description
    A piece of text on a record with a type, such as an abstract or a methods note. A record can
    hold several.

Developer
    A {term}`portal role` that carries no permissions of its own.

DOI
    A Digital Object Identifier. A DOI can be stored as an {term}`identifier` on a project, dataset,
    sample or measurement.

Ghost
    The {term}`account state` of a {term}`person` with no email address. A ghost is created so
    that someone can be credited on a record. They cannot sign in.

Identifier
    A persistent code that names a record, person or organization in another system, such as an
    {term}`ORCID` or a {term}`ROR` identifier. An identifier value must be unique across projects,
    datasets, samples and measurements.

IGSN
    An International Generic Sample Number, the identifier for a physical specimen. A
    {term}`sample` accepts an IGSN or a {term}`DOI` as its identifier type.

Inactive
    The {term}`account state` of a {term}`person` whose account has been deactivated. It takes
    precedence over the other states.

Invited
    The {term}`account state` of a {term}`person` who has an email address and has not yet
    claimed their profile.

Key dates
    The dated events on a record, such as when work started or ended. Each date has a type and is
    kept as precisely as it was entered.

Keywords
    The terms that describe a record. A record carries free keywords, and a project or dataset can
    also carry keywords from a {term}`controlled vocabulary`.

Measurement
    A single observation or analysis made on a {term}`sample`. A measurement belongs to a
    {term}`dataset`. Each kind of measurement is a {term}`measurement type` of its own.

Measurement type
    A kind of measurement that a portal developer has registered, such as a spectrometer reading.
    It sets which fields a measurement of that kind holds.

Organization
    A {term}`contributor` that is an institution, such as a university or a funder. It can have a
    parent organization, an {term}`affiliation` for each member, and a point on the map.

ORCID
    An identifier for a researcher. A {term}`person` can sign in with ORCID, and a profile can be
    created or filled in from an ORCID record.

Person
    A {term}`contributor` that is an individual. A person is also the portal's user account.

Portal
    A research data website built on FairDM.

Portal Administrator
    A {term}`portal role`. It lets the holder view groups, view and change people, and change the
    portal's identity. The same words name the reader who runs a portal.

Portal developer
    The person who builds a portal on FairDM and deploys it.

Portal role
    A named set of portal-wide rights that an administrator gives to a person. FairDM ships four:
    {term}`Portal Administrator`, {term}`Data Curator`, {term}`Community Manager` and
    {term}`Developer`. A portal role is not the same as the roles a {term}`contributor` plays on a
    record.

Portal user
    A person who adds, edits and publishes research data in a portal.

Project
    A body of research that groups {term}`datasets <dataset>`. A project has a
    {term}`project status`, a {term}`visibility` and an owning {term}`organization`.

Project status
    The stage a project is at: Concept, Planning, In progress, Complete or Searching for
    collaborators.

Published
    A flag on a {term}`dataset` that says its data may be shown publicly. It is separate from
    {term}`visibility`, which governs the metadata.

Role (on a record)
    What a {term}`contributor` did on a record, such as Creator, Data Collector or Contact Person. It is listed in
    the credit and is separate from the {term}`contribution level` and the {term}`portal role`.

ROR
    The Research Organization Registry. An {term}`organization` can be created or filled in from
    its ROR identifier.

Sample
    Anything that is measured or observed, such as a rock or a water sample. A sample belongs to a {term}`dataset` and is always of one {term}`sample type`.

Sample status
    Where a physical {term}`sample` is held: Available, In Use, Stored, Destroyed or Unknown. A
    sample's status can move from any value to any other.

Sample type
    A kind of sample that a portal developer has registered, such as a rock sample. It sets which
    fields a sample of that kind holds.

Visibility
    Whether a project, dataset, sample or measurement is Private or Public. A private record can
    be opened only by people who hold a {term}`contribution level` on it and by holders of a
    {term}`portal role` that grants the right.

:::
