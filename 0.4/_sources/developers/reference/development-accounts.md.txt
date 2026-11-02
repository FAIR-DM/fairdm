# Development accounts

This page lists the accounts that FairDM's development commands create, their addresses, passwords and roles, the environment rule that restricts them, and the check that reports them outside development. It does not give the steps to use them, which are in [How to sign in as each portal role while developing](../how-to/sign-in-as-each-portal-role-while-developing.md), or the reasons for the design, which are in [ADR 0022](../../adr/0022-development-accounts-are-a-command-that-refuses.md).

Every account below uses the password `password`. Sign in at `/account-center/login/` with the address.

## The commands

| Command | Ships with | Accounts | For |
|---|---|---|---|
| `create_dev_accounts` | The `fairdm` package | Five at `example.com`, one for each portal role and one holding none | Seeing what each [portal role](portal-roles.md) can do |
| `seed_overviews` | The demo application only | Three at `example.com`: `regular.user`, `staff.user` and `super.user` | Opening the overview pages as a visitor, as a team member and as an administrator |
| `seed_contributors` | The demo application only | The same three, and the Data Curator account of `create_dev_accounts` | Opening a record's Contributors tab in every state it has, and stepping in on a record as a data curator |
| `seed_profiles` | The demo application only | Five more at `example.com` around the organization `regular.user` owns | Opening and saving an organization's editing page as each kind of person around it |

`seed_record_search` also needs the development environment, but it creates records and no accounts. All four seed commands are listed on [Management commands](management-commands.md) as demo-only.

Run a command with `uv run python manage.py <command>`.

## create_dev_accounts

| First name | Last name | Email | Role |
|---|---|---|---|
| Portal | Administrator | `portal.administrator@example.com` | Portal Administrator |
| Data | Curator | `data.curator@example.com` | Data Curator |
| Community | Manager | `community.manager@example.com` | Community Manager |
| Portal | Developer | `portal.developer@example.com` | Developer |
| Regular | User | `regular.user@example.com` | None |

Each account is active and claimed, and its email address is confirmed, so there is no verification link to follow. The command is idempotent:

- An address that does not exist is created.
- An address that exists with the same first and last name is left unchanged. The role is added to it and its address is confirmed again.
- An address that belongs to a person with a different name stops the command with a `CommandError`, and the command creates nothing.

`regular.user@example.com` is also the account the seed commands sign in through. Whichever command runs first creates it, and the others leave it as it is.

The accounts are declared in `fairdm.management.commands.create_dev_accounts` as `DEV_ACCOUNTS`, with the password in `DEV_ACCOUNT_PASSWORD` and the addresses in `DEV_ACCOUNT_EMAILS`.

## seed_overviews

| Email | Rights |
|---|---|
| `regular.user@example.com` | None. It is on the team of no seeded record, so it sees what any visitor sees once signed in |
| `staff.user@example.com` | A staff account. Listed at the manage level on the seeded projects and datasets that have a team |
| `super.user@example.com` | A superuser |

The command creates an account only when its address is missing. An existing account keeps its password, names and rights. Running the command again replaces only the projects and datasets it created before, which are the ones that carry a seeded name and were created by `super.user`.

## seed_profiles

The command adds five accounts, each with the password `password`, around the organization `regular.user` owns:

| Email | Holds for that organization |
|---|---|
| `admin.user@example.com` | A current administrator affiliation. May open and save the editing page |
| `member.user@example.com` | A current ordinary member affiliation. Is refused the editing page |
| `former-admin.user@example.com` | An administrator affiliation that has ended. Is refused the editing page |
| `community-manager.user@example.com` | The Community Manager role. May open and save the editing page of any organization and of a person who has no active account |
| `data-curator.user@example.com` | The Data Curator role. Is refused the editing page of every profile it does not own |

The command runs `seed_overviews` first when the showcase project is missing. Running it again replaces what it created.

## seed_contributors

The command loads a project, datasets, a sample and a measurement that reach every state a record's Contributors tab answers for. It signs them in through the three accounts of `seed_overviews`. It prints the address of each record's tab.

One dataset is private, belongs to no project, and has no manager who can sign in. The person managing it has no account. The command creates `data.curator@example.com` when it is missing, with the Data Curator role and the password `password`, and does not list it on the dataset. It creates only that account of the five in `create_dev_accounts`.

| Option | What it does |
|---|---|
| `--keep-records` | Adds what the command needs to the records an earlier run made, without replacing them, so their addresses stay the same. Running it again changes nothing |

## Environment rule

Every command above runs only in an environment for which FairDM ships a non-production override. The set is `fairdm.apps.NON_PRODUCTION_ENVIRONMENTS`, which holds `development`. The environment is the value of the `DJANGO_ENV` setting, and it defaults to `production`. See [Configuration](configuration.md).

On any other environment, including a misspelled one and the empty string, the command raises a `CommandError` and creates nothing.

```{warning}
These accounts share a password that is published in this documentation. The refusal above and the check below are their whole safety. Do not create them on a portal that holds real data.
```

## fairdm.E501

`fairdm.E501` is a deployment check, tagged `deploy` and `production_critical`. It runs when the environment is not in `NON_PRODUCTION_ENVIRONMENTS`. It reports an error that names every address it finds among:

- the five addresses of `create_dev_accounts`
- the three addresses of `seed_overviews`
- the five addresses of `seed_profiles`

It guards against a database copied down from production, a dump restored the wrong way round, and an environment variable changed under a database that already holds these accounts. A portal outside development that holds one of the addresses refuses to start. See [Configuration checks](../../administrators/reference/configuration-checks.md).
