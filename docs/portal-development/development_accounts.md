# Development accounts

Everything a portal role changes is invisible until somebody signs in as that role and sees what
they can do. `manage.py create_dev_accounts` creates five accounts for exactly that: one holding
each of the four [portal roles](portal_roles.md), and one holding none, so you can sign in as a
curator, a community manager, a developer or an ordinary contributor without inventing test data
of your own.

Four commands create development accounts, for different purposes:

| Command | Accounts | For |
| --- | --- | --- |
| `manage.py create_dev_accounts` | Five accounts at `fairdm.org`, one per portal role and one holding none | Seeing what each [portal role](portal_roles.md) can do |
| `manage.py seed_overviews` | Three accounts at `example.com`: a regular user, a staff user and a superuser | Opening the [overview pages](overview-pages.md) as a visitor, as a team member and as an administrator |
| `manage.py seed_contributors` | The same three accounts at `example.com`, and the Data Curator account at `fairdm.org` | Opening a record's [Contributors tab](../user-guide/crediting-a-record.md) in every state it has, and stepping in on a record as a data curator |
| `manage.py seed_profiles` | Five more accounts at `example.com`: an administrator, an ordinary member and a former administrator of the organization `regular.user` owns, a community manager and a data curator | Opening and saving an [organization's editing page](contributors.md#editing-a-profile) as each kind of person around it |

```bash
poetry run python manage.py create_dev_accounts
```

| First name | Last name     | Email                              | Role                  |
| ---------- | ------------- | ----------------------------------- | ---------------------- |
| Portal     | Administrator | `portal.administrator@fairdm.org`   | Portal Administrator   |
| Data       | Curator       | `data.curator@fairdm.org`           | Data Curator           |
| Community  | Manager       | `community.manager@fairdm.org`      | Community Manager      |
| Portal     | Developer     | `portal.developer@fairdm.org`       | Developer              |
| Regular    | User          | `regular.user@fairdm.org`           | *(none)*                |

Every account uses the password `password` and is ready to sign in with immediately: active, and
its email address already confirmed - there is no verification link to follow. Sign in at
`/accounts/login/` with any of the addresses above.

Running the command again does not create duplicates. If one of the five addresses already
belongs to somebody else, it refuses rather than take over that account.

```{warning}
These accounts exist **only outside production**. The command refuses to run - and creates
nothing - on any environment FairDM does not ship a non-production override for
(`fairdm.apps.NON_PRODUCTION_ENVIRONMENTS`; the shipped example is `development`). They share a
password published in this document, so that refusal is their whole safety. A second check,
`fairdm.E501`, reports any of the five addresses it finds on a portal that is not in development -
guarding against a database copied down from production, a dump restored the wrong way round, or
an environment variable changed under a database that already has these accounts in it.
```

They ship with the FairDM package itself, not with the demo application, so they are available
to any portal built on the framework - not only this repository's own demo.

## Accounts for the overview pages

`manage.py seed_overviews` loads records that reach every state of the four
[overview pages](overview-pages.md), and signs them in through three accounts:

| Email | Rights |
| --- | --- |
| `regular.user@example.com` | None. It is on the team of no record, so it sees what any visitor sees once signed in. |
| `staff.user@example.com` | On the team of each seeded project and dataset that has one: it may view, change and delete them. |
| `super.user@example.com` | A superuser. |

```bash
poetry run python manage.py seed_overviews
```

The password of all three is `password`. The command creates an account only when its address is
missing. An account that already exists is left exactly as it is, so its password stays whatever
it was, and you sign in with that instead. Running the command again replaces only the projects
and datasets it created earlier, and leaves any project somebody else made under the same name.

Like `create_dev_accounts`, it refuses to run outside development, and `fairdm.E501` reports the
three `example.com` addresses on a portal that is not in development.

## Accounts for editing an organization's profile

`manage.py seed_profiles` loads the person and organization pages in every state they answer for.
On the organization `regular.user@example.com` owns, it adds five more accounts, each with the
password `password`:

| Email | Affiliation to that organization |
| --- | --- |
| `admin.user@example.com` | A current administrator. It may open and save the editing page. |
| `member.user@example.com` | A current ordinary member. It is refused the editing page. |
| `former-admin.user@example.com` | An administrator whose affiliation has ended. It is refused the editing page. |
| `community-manager.user@example.com` | Holds the Community Manager role. It may open and save the editing page of any organization and of a person who does not have an active account. |
| `data-curator.user@example.com` | Holds the Data Curator role. It is refused the editing page of every profile it does not own. |

```bash
poetry run python manage.py seed_profiles
```

The command creates an account only when its address is missing, so an account that already exists
keeps its password. Like the other seeds, the command refuses to run outside development, and
`fairdm.E501` reports these five addresses on a portal that is not in development.

## Accounts for the Contributors tab

`manage.py seed_contributors` loads a project, datasets, a sample and a measurement that reach
every state a record's Contributors tab answers for, and signs them in through the three
`example.com` accounts of `seed_overviews`. The command is `ContributorSeed`, in
`demo/seed/contributors.py`. It prints the address of each record's tab.

```bash
poetry run python manage.py seed_contributors
```

One of the datasets is private, belongs to no project, and has no manager who can sign in: the
person managing it has no account. Nobody can change its contributors until someone steps in, which
is what the Data Curator role is for. The command creates `data.curator@fairdm.org` if it is
missing, with the Data Curator role and the password `password`, and does not list it on the
dataset. Sign in as that account, open the dataset's Contributors tab and raise Yusuf Demir to
manage. From then on he is the only person who can sign in and manage it, so lowering or removing
him is refused, and so is removing the organization he is credited from.

Only the Data Curator account is created, not the other four at `fairdm.org`: `regular.user@fairdm.org`
has the same name as `regular.user@example.com`, and the seed finds people by name.

Running the command again replaces only the records it created. Pass `--keep-records` to add what
a newer version of the seed needs to the records an earlier run made, without replacing them:

```bash
poetry run python manage.py seed_contributors --keep-records
```

It gives the example people their affiliations, credits some of them from one, and adds the private
dataset and the Data Curator account if they are missing. No record changes its address, and
running it again changes nothing. Use it on a development database whose record addresses you
want to keep. Like the other seeds, the command refuses to run outside development.
