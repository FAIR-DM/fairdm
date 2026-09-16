# Quickstart — 017 Portal roles and the people who hold them

What this feature looks like from the outside, for the two people who touch it.

## For a portal administrator

The roles are already there. Bringing the portal's database up to date installs them:

```bash
python manage.py migrate
```

Four roles exist afterwards, whatever the portal had before:

| Role | The job |
|---|---|
| Portal Administrator | Runs the portal: its identity, and who holds which role |
| Data Curator | Looks after the content: every project, dataset, sample and measurement |
| Community Manager | Looks after the people: accounts, profiles, organisations and merges |
| Developer | Builds and maintains the portal. Holds no rights; appears on the team page |

Putting somebody in one is done in the administration interface, on their person record. A holder of
any of the first three can reach that interface from then on; a Developer cannot.

Deleting or renaming one of these four is refused. A portal that wants a different split of rights
creates a group of its own, which nothing here prevents.

If a role does go missing — from a shell, or a script — a production portal will refuse to start and
name it. Running `migrate` puts it back.

```bash
python manage.py check --deploy
```

reports the same thing without stopping anything, in development and in continuous integration.

## For somebody building a portal on FairDM

Five accounts, one per role plus one holding none, for signing in as each in turn. Development only:

```bash
python manage.py create_dev_accounts
```

| Sign in as | Sees the portal as |
|---|---|
| portal.administrator@fairdm.org | Portal Administrator |
| data.curator@fairdm.org | Data Curator |
| community.manager@fairdm.org | Community Manager |
| portal.developer@fairdm.org | Developer |
| regular.user@fairdm.org | an ordinary contributor |

The password for all five is `password`. Every address is already confirmed, so there is no
confirmation step between the command and being signed in.

The command refuses to run on anything but a development environment, and creates nothing when it
refuses. That refusal is the only thing standing between a published password and an administrator
account, so it is asserted by a test rather than trusted.

## For a visitor

**Community → Portal team** names who holds which role. Names and profile links, nothing else.
