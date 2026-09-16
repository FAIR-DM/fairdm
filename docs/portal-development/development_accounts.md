# Development accounts

Everything a portal role changes is invisible until somebody signs in as that role and sees what
they can do. `manage.py create_dev_accounts` creates five accounts for exactly that: one holding
each of the four [portal roles](portal_roles.md), and one holding none, so you can sign in as a
curator, a community manager, a developer or an ordinary contributor without inventing test data
of your own.

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
