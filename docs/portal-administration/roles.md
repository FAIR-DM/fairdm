# Portal roles

FairDM ships four portal roles, declared in code and installed into every portal automatically
every time its database is brought up to date. Assign one or more of them to a person to decide
what they can do in your portal, beyond what any signed-in contributor can already do.

```{admonition} You are here
:class: tip
**Admin Guide** → Portal Roles

If you landed here from a search, start with the [Admin Guide overview](index.md) to understand
the admin role and core entities.
```

## Superuser vs. Portal Administrator

These are two different things, and conflating them is the most common source of confusion:

Superuser
: A Django account flag (`is_superuser`), set from the command line or the deployment tooling.
  It belongs to whoever deploys and maintains the portal's infrastructure, holds every
  permission unconditionally, and is not a portal role.

Portal Administrator
: A role a portal administrator grants to a person through the ordinary admin interface, for
  the day-to-day job of running the portal: its identity and who holds which role. It holds no
  more than the rights listed below.

A portal's superuser account is the deployer's; the Portal Administrator role is the portal's own
job, and can be held by anyone the deployer chooses to trust with it.

## The four roles

### Portal Administrator

Runs the portal itself: its identity, and who holds which role.

- Change the portal's identity — its name, branding and metadata.
- View any group, and add a person to or remove a person from a role by editing that person's
  record.

The role deliberately holds no right to edit a group's own permissions. Membership is granted and
revoked on the **Groups** field of a person's own record, not by editing a `Group` object — a role
that could edit groups could rewrite what every role, including its own, is allowed to do.

### Data Curator

Runs the research records: every project, dataset, sample and measurement in the portal, and
their attached descriptions, dates and credits — regardless of who created them or whether they
are private.

- View, add, change and delete any project, dataset, sample or measurement, and the description,
  date and contribution records attached to them.
- Import data into a dataset and publish it.

### Community Manager

Runs the people side: accounts, organisations, and the profile-claim and merge workflows that go
with them.

- View and change person and organisation records, including affiliations, and act on profile
  claims and merges.
- Deactivate and reactivate accounts.

The role cannot delete a person record, and it holds nothing over projects, datasets, samples or
measurements.

### Developer

Names a person as part of the portal's team with no further rights. A person holding only the
Developer role has exactly the access of any other signed-in contributor.

## Holding more than one role

A person can hold more than one of these roles at once, and their rights are everything those
roles hold together. Reaching the administration interface requires holding at least one role that
carries rights — the Portal Administrator, Data Curator or Community Manager role. Holding only the
Developer role does not.

## The four roles cannot be deleted or renamed

The **Groups** page in the administration interface lists these four roles alongside any group
your portal has created for itself. The four are protected: there is no delete option for one of
them, and changing its name is refused with a message rather than saved. Both refusals apply
everywhere, not only in the administration interface, so a role cannot be removed by accident
through a script or a management command either.

A group your portal created for itself — for one project's team, say — has neither restriction:
it deletes and renames like any other Django group.

If a role is ever missing anyway (removed directly against the database, for instance), FairDM
restores it, together with its rights, the next time the portal is brought up to date. Anyone the
role had already been granted to keeps that role once it is restored — nobody needs to be
re-added. A portal running in production also refuses to start while a role is missing, naming
which one, so the condition is never silent.

## Upgrading from an earlier version

Earlier versions of FairDM shipped three ungoverned group names with no permissions attached
(`Portal Administrators`, `Data Administrators`, `Developers`), which portal code matched by name
rather than asking the permission system. Upgrading a portal that already used them renames those
groups in place to the roles above — `Portal Administrators` becomes `Portal Administrator`,
`Data Administrators` becomes `Data Curator`, and `Developers` becomes `Developer` — carrying every
existing member across automatically. Nobody needs to be re-added to a role because of this
upgrade.

```{important}
A model-level permission held through one of the four roles above now applies to every instance
of that model across the whole portal, not only to the object it was originally intended for. A
permission granted any other way — directly to a person, or through a group the portal made up
itself — is unchanged from before.
```
