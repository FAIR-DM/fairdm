# How to sign in as each portal role while developing

A portal role changes what a person sees, and you only notice when you sign in as that role. This guide creates five accounts, one for each of the four portal roles and one that holds none, so you can use your portal as a curator, a community manager, a developer or an ordinary contributor. Do it in your development environment only.

## Before you start

- Your portal runs with `DJANGO_ENV=development`. The command refuses to run on any other environment. See [Configuration](../reference/configuration.md).
- The database has been migrated, because `migrate` installs the four roles.

## Steps

1. Bring the database up to date, which installs the roles.

   ```bash
   uv run python manage.py migrate
   ```

2. Create the accounts.

   ```bash
   DJANGO_ENV=development uv run python manage.py create_dev_accounts
   ```

   The command prints one line for each account. Running it again creates no duplicates.

3. Sign in with one of these addresses and the password `password`. Their email addresses are already confirmed.

   | Email | Role |
   |---|---|
   | `portal.administrator@example.com` | Portal Administrator |
   | `data.curator@example.com` | Data Curator |
   | `community.manager@example.com` | Community Manager |
   | `portal.developer@example.com` | Developer |
   | `regular.user@example.com` | None |

4. Use the portal as that role. Open a private dataset as the Data Curator, the people list as the Community Manager, and the administration interface as each role. Only the Portal Administrator, Data Curator and Community Manager reach it.

## The result

You can sign in as each role and see what it is allowed to do. What each role may do is in [Portal roles](../../administrators/reference/portal-roles.md). Test with these accounts and not with a superuser, which bypasses the portal's ordinary workflows. The reason is in [How contributor accounts and credits work](../../explanation/how-contributor-accounts-and-credits-work.md).

## If an address already exists

An address that already belongs to a person with the same name is left unchanged and given the role. An address that belongs to a person with a different name stops the command, and it creates nothing.

## Seed data from the demo

The demo application ships more commands that create accounts and records, for opening the overview pages, a record's Contributors tab and the profile editing pages. They exist in the demo only. The accounts and commands are listed in [Development accounts](../reference/development-accounts.md).

Outside development, a portal that holds any of these addresses reports `fairdm.E501` and refuses to start.
