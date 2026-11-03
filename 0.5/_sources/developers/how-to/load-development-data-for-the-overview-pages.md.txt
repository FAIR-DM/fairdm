# How to load development data for the overview pages

The overview pages answer for many states: a private project, an unpublished dataset, a sample with no measurements, a person with an incomplete profile. You load development data so that you can open each state as a visitor and as a member of a team while you work on a page.

## Before you start

The commands live in the demo portal, in the FairDM repository's `demo/` directory, so you run them from a checkout of that repository. A portal built on the FairDM package does not have them. Write seeds of your own on the pattern of `demo/seed/`.

The commands refuse to run outside development, because the accounts they create have a password that is written down. Set `DJANGO_ENV=development`. The accounts are listed in [Development accounts](../reference/development-accounts.md).

## Steps

1. Load the record pages' data:

   ```bash
   DJANGO_ENV=development uv run python manage.py seed_overviews
   ```

   The command creates the accounts `regular.user`, `staff.user` and `super.user` at `example.com` when they are missing, with the password `password`, and leaves any that exist as they are. It then runs three seeds, `ProjectSeed`, `SampleSeed` and `MeasurementSeed`, in `demo/seed/`.

2. To load the data for the person and organization pages, run:

   ```bash
   DJANGO_ENV=development uv run python manage.py seed_profiles
   ```

   It builds on the records `seed_overviews` creates, so run that first.

3. Sign in as `staff.user` to see the pages as a member of a team. `staff.user` holds the manage level on every seeded project and dataset, so its pages show the readiness checklist. `regular.user` holds none. Open the pages signed out to see them as a visitor.

4. Run the command again whenever you want fresh data. It replaces only the records it created, and leaves records someone else made.

## The result

The database holds records that reach each state the pages describe:

- projects: one described in full, with datasets, samples, measurements, a large team, funding and identifiers, one brand-new private project with only a name, and one sparse public project with a very long title
- samples: one with a full history, an identifier, a location, measurements and subsamples, one that has been destroyed, one with only a name, and one in an unpublished dataset
- measurements: one with its procedure, a DOI and a location of its own, one recorded in another team's dataset, one with nothing else recorded, and one in an unpublished dataset

Types with a template of their own show the extended page, and types without one show the shared page. See [How to give a sample or measurement type its own overview page](give-a-sample-or-measurement-type-its-own-overview-page.md).

## Helpers for your own seeds

`demo/seed/common.py` has the functions the seeds share:

| Function | What it does |
|---|---|
| `example_accounts()` | Returns the three example accounts, creating any that are missing. |
| `profile_accounts()` | Returns the accounts the editing pages are tried with. |
| `create_accounts(accounts)` | Creates the missing accounts from `(email, first, last, is_staff, is_superuser)` entries and returns them keyed by the part of the address before the `@`. |
| `remove_own_projects(names, users)` | Deletes the projects an earlier run created. |
| `grant_team_rights(user, *records)` | Lists an account at the manage level on the projects and datasets it is given. |
| `data_curator()` | Returns the development account that holds the Data Curator role, creating it when missing. |
