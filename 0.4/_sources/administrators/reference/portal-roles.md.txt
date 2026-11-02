# Portal roles

FairDM ships four portal roles. This page lists each role, the permissions it holds, who may edit a profile, how a person reaches the administration interface, and how the roles are protected. It does not explain why access is divided this way, which is in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md), and it does not give steps for assigning a role, which are in [How to assign a portal role](../how-to/assign-a-portal-role.md).

A portal role applies across the whole portal. The level a person holds on one record is a different thing, and the two add together without either changing the other.

## The roles

The roles are declared in code and installed into every portal each time its database is brought up to date.

| Role | Looks after | Reaches the administration interface |
|---|---|---|
| Portal Administrator | The portal's identity and who holds which role | Yes |
| Data Curator | Every project, dataset, sample and measurement | Yes |
| Community Manager | People, organizations, affiliations and profile merges | Yes |
| Developer | Nothing. It names a person as part of the portal's team | No |

A person can hold more than one role and has everything the roles hold together.

## Portal Administrator

| Permission | What it allows |
|---|---|
| View groups | Open the list of groups and the **Groups** field on a person's page |
| View people | Open the **Users** list and a person's page |
| Change people | Edit a person, including the roles in **Groups** |
| Change identity | Edit the portal's name, branding and metadata |

The role holds no right to change a group, because a person who could edit groups could rewrite what every role, their own included, is allowed to do. A role is assigned on the person's own page.

## Data Curator

The role holds the permissions below for every project, dataset, sample and measurement, whoever created it and whether or not it is private.

| Permission | Applies to |
|---|---|
| View, add, change and delete | Projects, datasets, samples and measurements |
| View, add, change and delete | The descriptions of each of those four |
| View, add, change and delete | The dates of each of those four |
| View, add, change and delete | Contributions, the credits that carry a level |
| Import data | Datasets |
| Publish | Datasets |

The permissions are those of the base sample and measurement records. The role holds no permission of any registered sample or measurement type.

Because the role can change a record, it can open the record's **Contributors** tab and change who is credited on it, without being listed. Doing so does not add the holder to the record or mark the change as theirs. See [How to give a record a manager when its only manager has left](../how-to/give-a-record-a-manager-again.md).

## Community Manager

| Permission | Applies to |
|---|---|
| View and change | People |
| View and change | Organizations |
| View and change | Affiliations |
| View and change | Contributions |

The role can also:

- Deactivate and reactivate an account, with **Active** on a person's page.
- Edit the profile of any organization, and the profile of a person nobody can sign in as. See [Who may edit a profile](#who-may-edit-a-profile).

The role cannot delete a person, and it holds nothing over projects, datasets, samples or measurements.

The Users list offers the action **Merge selected Person into another** to anyone who holds the permission to change people. That is both the Community Manager and the Portal Administrator role.

## Developer

The role holds no permission. A person who holds only this role has the access of any signed-in person. The role lists them on the portal's [Team](../../users/community/team.md) page.

## Who may edit a profile

Every person's and organization's profile has an editing page in the portal, reached from the **Edit profile** or **Edit details** action on the profile. Nobody else is offered it, and a request for its address by anyone else is refused.

| Profile | Who may edit it |
|---|---|
| A person whose account is active and who has claimed the profile or signed in | That person, and nobody else |
| A person nobody has claimed, whose owner has been invited and has not signed in, or whose account is deactivated | Any Community Manager |
| An organization | Its owner and its administrators while their affiliations have not ended, and any Community Manager |

The Portal Administrator, Data Curator and Developer roles give no right to edit a profile, and neither does being a superuser or an ordinary member of an organization. A superuser still changes any record in the administration interface.

When a person gets an active account, by claiming the profile or by being reactivated, only they edit their own profile from then on. See [ADR 0024](../../adr/0024-the-right-to-edit-a-profile-is-asked-of-the-record.md).

An edit by a Community Manager is not marked as theirs anywhere a reader can see. It does not change whether a profile is claimed, whether an account is active, or who owns, administers or belongs to an organization.

## Superuser and Portal Administrator

A superuser is an account flag. It holds every permission without exception, belongs to whoever deploys and maintains the portal, and is not a role. A superuser cannot be credited on a record.

The Portal Administrator is a role that a person is given in the administration interface. It holds only the permissions listed above.

## Reaching the administration interface

The administration interface is at `/admin/` on the portal, unless the portal sets another address with `ADMIN_URL`. The setting is described on the [settings reference](../../developers/reference/settings.md). Its pages are headed **Portal Administration**.

A person is admitted when their account is active and either is marked as staff or holds at least one role that carries permissions. The Portal Administrator, Data Curator and Community Manager roles carry permissions. The Developer role does not, so holding only that role does not admit a person.

Admission does not decide what a person sees inside. Each section appears only for a person who holds the permission to view it.

## Protection of the roles

The **Groups** list in the administration interface shows the four roles beside any group the portal made for itself.

- A shipped role has no delete option. A request to delete one is refused with a message that reads "FairDM requires the “Data Curator” role and refuses to delete it", naming the role.
- Renaming a shipped role is refused with a message in the same form.
- Both refusals apply everywhere, including a script or a management command.
- A group the portal made for itself can be deleted and renamed like any other group.

Every time the database is brought up to date, FairDM creates any missing role and sets each role's permissions to exactly the lists above. A permission added to a role by hand is removed and one removed by hand is put back. Membership is never changed, so nobody has to be added again.

A portal running in production refuses to start while a role is missing, and names it. The check is `fairdm.E500`, described under [Configuration checks](configuration-checks.md).

## The Team page

The portal's public [Team](../../users/community/team.md) page lists the holders of each role, in the order Portal Administrator, Data Curator, Community Manager, Developer. A role nobody holds is left out, a person with more than one role appears under each, and a deactivated account is left out.
