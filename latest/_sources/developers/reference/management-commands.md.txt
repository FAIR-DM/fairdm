# Management commands

This page lists the `manage.py` commands FairDM adds to a portal, with the arguments each takes, what it does and when it refuses to run. It does not cover the commands Django and other packages provide, and it does not say when to run a command. The [development accounts](development-accounts.md) the account commands create have a page of their own.

FairDM adds seven commands to every portal. The demo project in the FairDM repository adds four more, which a portal does not have.

| Command | Does |
|---|---|
| [`backup`](#backup) | Backs up the database and the media now |
| [`cleanup_permissions`](#cleanup_permissions) | Deletes permission rows that no model declares |
| [`create_dev_accounts`](#create_dev_accounts) | Creates one development account for each portal role and one holding none |
| [`generate_fake_data`](#generate_fake_data) | Fills a development database with projects, datasets, samples and measurements |
| [`seed_licenses`](#seed_licenses) | Creates the recommended licences |
| [`show_config`](#show_config) | Reports where the portal's settings came from |
| [`upgrade_vocabularies`](#upgrade_vocabularies) | Converts a database that stored terms with django-research-vocabs |

## FairDM commands

### backup

```bash
uv run python manage.py backup
uv run python manage.py backup --database-only
uv run python manage.py backup --media-only
```

Writes the backups the scheduled tasks write, in the foreground, to the `dbbackup` storage in [`STORAGES`](settings.md#storages). With no option it writes one database backup and one media archive. `--database-only` writes the database backup alone, and `--media-only` writes the media archive alone. The two options exclude each other.

After each backup it removes the oldest of that kind beyond [`BACKUP_KEEP`](settings.md#backup_keep). Database backups and media archives are counted separately. A failed backup ends the command with an error and leaves the existing backups in place.

The command needs `pg_dump` for the database backup. The [container images](container-images.md) carry it. [How to back up a portal](../how-to/back-up-a-portal.md) shows the command in a running container.

### cleanup_permissions

```bash
uv run python manage.py cleanup_permissions
```

Takes no arguments. Scans every installed model for the permissions it declares, in `default_permissions` and `Meta.permissions`. Prints the stale permission rows it finds, deletes them, and prints how many it deleted. There is no dry run.

```{warning}
Deleting a permission also removes it from every group and person that held it. Read the list the command prints before you run it on a portal with data you care about.
```

### create_dev_accounts

```bash
uv run python manage.py create_dev_accounts
```

Takes no arguments. Creates five accounts: one for each of the four portal roles and one that holds none. Each account is active and its email address is already confirmed.

- It refuses and creates nothing when the resolved environment is not `development`. The accounts share a published password, so the refusal is their safety.
- It runs in one transaction, so a refusal part-way leaves nothing behind.
- Running it again creates no duplicates. An account that already exists with the same name is left unchanged, and its role and confirmed email are applied again.
- An address that already belongs to a person with a different name is refused with an error. The command does not take that account over.

The accounts, their roles and their password are in [Development accounts](development-accounts.md). The check `fairdm.E501` reports these accounts on a portal that is not in development. See [Configuration checks](../../administrators/reference/configuration-checks.md). [How to sign in as each portal role while developing](../how-to/sign-in-as-each-portal-role-while-developing.md) uses them.

### generate_fake_data

```bash
uv run python manage.py generate_fake_data --projects 5 --min-datasets 3
```

Fills the database with a hierarchy of fake records: people, organizations, projects, datasets, samples and measurements, with descriptions and dates on each record. Projects and datasets also carry credits. The projects and datasets it makes are private.

| Option | Type | Default | Sets |
|---|---|---|---|
| `--projects` | integer | 3 | The number of projects |
| `--min-datasets` | integer | 2 | The fewest datasets in a project |
| `--max-datasets` | integer | 4 | The most datasets in a project |
| `--min-samples` | integer | 5 | The fewest samples in a dataset |
| `--max-samples` | integer | 15 | The most samples in a dataset |
| `--min-measurements` | integer | 10 | The fewest measurements in a dataset |
| `--max-measurements` | integer | 30 | The most measurements in a dataset |
| `--people` | integer | 12 | The number of people created |
| `--organizations` | integer | 5 | The number of organizations created |
| `--clear` | flag | off | Deletes existing records first |

- It builds samples and measurements with the factories named in the `FAIRDM_FACTORIES` setting, which maps a model label to a factory's dotted path. It chooses among them at random. [How to add a factory for a portal model](../how-to/add-a-factory-for-a-portal-model.md) writes one. `FAIRDM_FACTORIES` is described in [Settings](settings.md).
- When no sample factory is listed, it creates no samples. When no measurement factory is listed, it creates no measurements. It never falls back to the base `Sample` or `Measurement`, which cannot be created.
- A measurement is made on one of the samples created for its dataset.
- Each project is owned by one of its credited organizations when it has one.
- It does not check the environment. It runs wherever you run it.

```{danger}
`--clear` deletes every measurement, sample, dataset, project, credit, person and organization in the database, including real people and your own account. Never use it on a portal that holds real data.
```

### seed_licenses

```bash
uv run python manage.py seed_licenses
```

Takes no arguments. Creates the three licences FairDM recommends if they do not exist: `CC0 1.0`, `CC BY 4.0` and `CC BY-SA 4.0`. It reads their text and canonical addresses from the fixture that `django-content-license` ships. It does not create the no-derivatives and non-commercial variants that fixture also holds. A portal that wants one adds it itself.

- It is safe to run again. A licence is matched by name, and one that already exists is left unchanged, even if you edited it.
- When it cannot read the fixture, it prints a warning on standard error, creates nothing and exits normally.
- Run it on every deployment, beside `sync_vocabularies`, so an existing portal gets the licences on its next one. A portal does that with a [start step](container-images.md#start-sequence).

### show_config

```bash
uv run python manage.py show_config
uv run python manage.py show_config DEBUG
```

Takes one optional argument, the name of a setting.

- With no argument it lists every layer `fairdm.setup()` considered, in the order they were applied, each marked `found` or `absent`.
- With a name it prints the setting's value and the layer that produced it, as `NAME = value (layer)`. A setting no layer produced is reported as `unattributed`.
- The value passes through Django's setting cleanser first, so a secret such as a key or password is masked.

[How FairDM configures a portal](../../explanation/how-fairdm-configures-a-portal.md) explains the layers.

### upgrade_vocabularies

```bash
uv run python manage.py upgrade_vocabularies
uv run python manage.py upgrade_vocabularies --database=archive
```

Takes `--database`, the alias of the database to convert, `default` unless given. It converts a database that stored terms with django-research-vocabs, which FairDM used before it stored them by their vocabulary addresses, and is run once, before `migrate`. It skips a model whose table does not exist yet, because `migrate` creates that table with the new schema.

- A database that holds nothing from django-research-vocabs is reported and left unchanged, so a new portal never needs it.
- When the tables of django-controlled-vocabularies are missing, it creates them and stops, so that `sync_vocabularies` can load the vocabularies before it runs again.
- It stops, and changes no stored term, while any of FairDM's five vocabularies is not loaded.
- It matches each stored type name and sample status to the concept of its field's vocabulary whose `skos:notation` is that name. It matches a keyword or role from one of FairDM's own vocabularies by notation in the same way, and one from any other vocabulary by the address django-research-vocabs held for it.
- It matches every value before it writes anything. If any value has no match, it lists every one with its field and how many rows hold it, and changes nothing.
- Otherwise it stores every term by its address in one transaction, moves the keywords and roles into tables that point at the loaded concepts, drops the tables of django-research-vocabs and removes its migration records.

[How to upgrade a portal to vocabulary addresses](../how-to/upgrade-a-portal-to-vocabulary-addresses.md) walks through the whole upgrade.

## Demo project commands

The commands below belong to the demo project in the FairDM repository, in `demo/management/commands/`. A portal built on FairDM does not have them. They load development data for the demo's screens.

All four refuse to run, and create nothing, when the resolved environment is not `development`. They sign in through accounts whose password is published, which is why.

| Command | Argument | Does |
|---|---|---|
| `seed_overviews` | None | Seeds a project, datasets, samples and measurements that reach every state of the four record overview pages. Signs them in through `regular.user`, `staff.user` and `super.user` at `example.com` |
| `seed_profiles` | None | Seeds the person and organization pages in every state they answer for, and five more accounts around the organization `regular.user` owns. Runs `seed_overviews` first when its records are missing |
| `seed_contributors` | `--keep-records` | Seeds every state of a record's Contributors tab on a project, a dataset, a sample and a measurement |
| `seed_record_search` | `--large` | Seeds the records the record search fields are tried against. `--large` adds a public dataset of 100,000 samples |

- Running one again replaces only the records it created. `seed_record_search` adds only what is missing.
- `seed_contributors --keep-records` adds what a newer seed needs to the records an earlier run made, without replacing them, so their addresses stay the same.
- The accounts these commands create and their rights are in [Development accounts](development-accounts.md).
