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

- Change the portal's identity: its name, branding and metadata.
- View any group, and add a person to or remove a person from a role by editing that person's
  record.

The role deliberately holds no right to edit a group's own permissions. Membership is granted and
revoked on the **Groups** field of a person's own record, not by editing a `Group` object — a role
that could edit groups could rewrite what every role, including its own, is allowed to do.

### Data Curator

Runs the research records: every project, dataset, sample and measurement in the portal, and
their attached descriptions, dates and credits, regardless of who created them or whether they
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
- Edit the profile of any organization, and the profile of any person who does not have an active
  account, from the portal's own editing page. See [Who may edit a profile](#who-may-edit-a-profile).

The role cannot delete a person record, and it holds nothing over projects, datasets, samples or
measurements.

### Developer

Names a person as part of the portal's team with no further rights. A person holding only the
Developer role has exactly the access of any other signed-in contributor.

## Who may edit a profile

Every person's and organization's profile has an editing page in the portal, reached from the
**Edit profile** or **Edit details** action on the profile itself. The same page, with the same
fields, is offered to everyone who may use it. Nobody else is offered it, and a request for its
address by anyone else is refused.

| Profile | Who may edit it |
|---|---|
| A person with an active account | That person, and nobody else. |
| A person whose profile nobody has claimed, whose owner has been invited and has not yet signed in, or whose account has been deactivated | Any Community Manager. |
| An organization | Its owner and its administrators while their affiliations have not ended, and any Community Manager. |

A person who gets an active account again, by claiming the profile or by being reactivated, edits
their own profile from that moment, and Community Managers can no longer edit it. A Community
Manager who had the editing page open at the time cannot save it.

The Portal Administrator, Data Curator and Developer roles give no right to edit a profile, and
neither does being a superuser or an ordinary member of an organization. A superuser still changes
any record in the administration interface. An edit by a Community Manager is not marked as theirs
anywhere a reader can see, and it does not change whether a profile is claimed, whether an account
is active, or who owns, administers or belongs to an organization. The rights a role holds are
unchanged by this: the Community Manager's right here follows from the role itself, not from the
`change_person` and `change_organization` permissions it also holds.

## Portal roles and the levels on a record

A portal role applies to every record of a kind in the portal. A level (view, edit or manage) is
held on one project, dataset, sample or measurement, by a person who is listed on it as a
contributor or on the record above it, and decides what they may do there. The two work together
and neither takes anything from the other:

- A Data Curator holds the right to view and change every project, dataset, sample and measurement,
  and so opens, edits and manages the contributors of any record without being listed on it.
  Doing so does not add them to the record or mark the change as theirs.
- A person who holds a level on a record and also holds a portal role has everything either gives
  them.
- The portal roles do not change what any level allows. Holding the Community Manager, Portal
  Administrator or Developer role gives no right over a record.
- Being a member, administrator or owner of an organization that is credited on a record gives no
  access to it. Neither does being credited from an organization elsewhere.

People who manage a record set levels themselves, on its **Contributors** tab, so a portal
administrator is never asked to grant access to a record. See
[Managing Users and Permissions](managing_users_and_permissions.md) for the levels.

### Stepping in on a record

A research team can be left with nobody who can manage its record, for example when its only
manager leaves the institution. A Data Curator can open that record, whether it is private or
public, go to its **Contributors** tab and raise one of the remaining contributors to manage.
The curator is not added to the record by doing so, and nothing stored with the contributors names
them as having made the change.

A Data Curator is bound by the same refusals as a person who manages the record:

- The last person who counts as able to manage a record cannot be removed or lowered. A person
  counts when they have an active account that can sign in and hold the manage level on the record
  or on a record above it. A person who can act only through a portal role does not count, so a
  record never depends on portal staff to stay manageable. A record that has nobody who counts can
  be given a manager by raising one of its contributors.
- An organization that people on the record are credited from cannot be removed.

The other roles give no way in. A person who holds only the Community Manager, Developer or Portal
Administrator role, and is not listed on a private record, is refused it as any other signed-in
person is: the record answers as if it did not exist. On a public record they can read the
**Contributors** tab and are refused its changing pages.

Rights follow the role. A person removed from the Data Curator role is refused on their next
request. To see the whole flow on development data, run `manage.py seed_contributors` and sign in as
`data.curator@fairdm.org`, as described in [Development accounts](../portal-development/development_accounts.md#accounts-for-the-contributors-tab).

## Holding more than one role

A person can hold more than one of these roles at once, and their rights are everything those
roles hold together. Reaching the administration interface requires holding at least one role that
carries rights — the Portal Administrator, Data Curator or Community Manager role. Holding only the
Developer role does not.

## The portal team page

Every portal has a public page listing who holds each role, grouped by role, reachable from the
**Community** section of the main navigation beside **People** and **Organizations**. Anyone can
read it without signing in.

Putting somebody in a role — on the **Groups** field of their record, as described above — is what
puts them on this page; taking them out of a role takes them off it. Deactivating an account
removes its holder from the page the same way, even though the role is still recorded on their
record: a deactivated account holds nothing, so listing it as the portal's administrator would tell
a visitor something untrue. A role nobody currently holds is left off the page entirely rather than
shown with nobody under it, and a person holding more than one role appears once under each.

Each person on the page is shown by their name, linked to their public profile. No email address
appears anywhere on it. The page lists these four roles only: a contributor's credit on a project,
dataset, sample or measurement is a different kind of role and never appears here, however many
records they are credited on.

## The four roles cannot be deleted or renamed

The **Groups** page in the administration interface lists these four roles alongside any group
your portal has created for itself. The four are protected: there is no delete option for one of
them, and changing its name is refused with a message rather than saved. Both refusals apply
everywhere, not only in the administration interface, so a role cannot be removed by accident
through a script or a management command either.

A group your portal created for itself, for one project's team say, has neither restriction:
it deletes and renames like any other Django group.

If a role is ever missing anyway (removed directly against the database, for instance), FairDM
restores it, together with its rights, the next time the portal is brought up to date. Anyone the
role had already been granted to keeps that role once it is restored, so nobody needs to be
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
permission granted any other way, whether directly to a person or through a group the portal made
up itself, is unchanged from before.
```
