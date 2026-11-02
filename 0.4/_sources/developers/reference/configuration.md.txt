# Configuration

This page describes `fairdm.setup()`: its arguments, the environment it resolves, the five layers it applies, the environment files it reads and the command that shows what it did. It does not list the settings, which are in [Settings](settings.md), or explain why the layers are ordered as they are, which is in [How FairDM configures a portal](../../explanation/how-fairdm-configures-a-portal.md). The checks that stop a production portal from starting are in [Configuration checks](../../administrators/reference/configuration-checks.md).

## `fairdm.setup()`

```python
fairdm.setup(
    apps: list[str] | None = None,
    addons: list[str] | None = None,
    base_dir: Path | None = None,
    env_file: str | None = None,
) -> None
```

A portal's settings module calls it once. It fills the calling module with a complete Django configuration and returns nothing.

```python
# config/settings.py
import fairdm

fairdm.setup()
```

| Argument | Type | Default | What it does | What it accepts |
| --- | --- | --- | --- | --- |
| `apps` | `list[str]` | `None`, read as `[]` | The portal's own apps. FairDM places them in `INSTALLED_APPS` ahead of its own apps, after the Django contrib apps. They are also kept in the `FAIRDM_APPS` setting. | App module paths or app configuration paths |
| `addons` | `list[str]` | `None`, read as `[]` | The addon packages whose settings FairDM applies as layer 3. | Importable package names. See [Addons](#addons). |
| `base_dir` | `Path` | The directory above the one holding the calling settings module | The directory FairDM looks in for the environment files, `templates/`, `assets/`, `fixtures/` and `project/locale/`, and where it puts `static/` and `media/`. It becomes the `BASE_DIR` setting. | A `Path` to a directory |
| `env_file` | `str` | `None` | An environment file read last, which overwrites variables already set. A path that does not exist is ignored. | A file path |

`setup()` accepts no settings as arguments. Passing any other keyword argument raises `TypeError`. A setting changes by assignment after the call, as [How to override a FairDM setting](../how-to/override-a-fairdm-setting.md) shows.

`setup()` raises `ImproperlyConfigured` when an addon's setup module cannot be found or fails while `DJANGO_ENV` is `production`. It raises `SystemCheckError` when `PARLER_LANGUAGES` names a language that `LANGUAGES` does not include.

`setup()` adds four names to the calling module besides the settings:

| Name | What it holds |
| --- | --- |
| `env` | The django-environ reader FairDM uses. A layer can call `env("NAME")` to read a variable. |
| `BASE_DIR` | The `base_dir` described above |
| `FAIRDM_APPS` | The `apps` list |
| `DJANGO_ENV` | The resolved environment name |

## The resolved environment

FairDM takes the environment from the `DJANGO_ENV` environment variable and uses `production` when it is unset. It does not check the value against a list. Any name is valid, including a name no override module exists for.

FairDM ships one override module, for `development`. Every other name composes the production baseline, and a production portal checks that baseline at start-up. Only the exact value `development` skips the production-critical checks.

## Layers

`setup()` applies five layers in this order. A later layer overrides the same setting in an earlier one.

| Layer | Source | Selected by |
| --- | --- | --- |
| 1. Baseline | Every module under `fairdm/conf/settings/`, in the order listed below | Always applied |
| 2. FairDM override | `fairdm/conf/<environment>.py` | The file exists. Only `development.py` exists. |
| 3. Addons | The setup module of each addon in `addons=` | The addon defines `__fdm_setup_module__` |
| 4. Portal override | `<environment>.py` beside the portal's settings module | The file exists |
| 5. Portal assignments | Assignments in the portal's settings module after the call | Always applied |

A layer chosen by existence is skipped without error when its file is missing. If the settings module has no file on disk, FairDM skips layer 4 and logs a warning.

If FairDM and the portal both have a module for the environment, both apply, FairDM's first. [How to add an environment override module](../how-to/add-an-environment-override-module.md) shows how to add one.

### Baseline modules

The baseline loads these modules in this order, and a module may read names an earlier one defined.

| Module | What it owns |
| --- | --- |
| `apps.py` | `INSTALLED_APPS`, `MIDDLEWARE`, `TEMPLATES`, the site, time and language settings |
| `security.py` | `SECRET_KEY`, `ALLOWED_HOSTS`, `DEBUG` and the HTTPS, cookie and HSTS settings |
| `database.py` | `DATABASES` and the backup and GDAL settings |
| `cache.py` | `CACHES` |
| `static_media.py` | Static files, media storage and thumbnails |
| `celery.py` | The `CELERY_*` settings |
| `auth.py` | Authentication backends, allauth, sign-in and profile forms |
| `logging.py` | `LOGGING` and Sentry |
| `email.py` | The email backend and addresses |
| `addons.py` | Settings for other packages, identifiers, markdown, the page shell and branding. This is a settings module and not the addon loader. |
| `api.py` | The REST framework, OpenAPI and CORS settings |

[Settings](settings.md) groups the settings by subject.

### Addons

An addon is a package that contributes settings. FairDM imports each package named in `addons=` and looks for the module path in the package's `__fdm_setup_module__` attribute. That module must be a single file and not a package. FairDM runs it in a private copy of the settings and merges the result only when the module runs to the end, so a module that fails leaves nothing behind.

| Situation | In production | In any other environment |
| --- | --- | --- |
| The package cannot be imported | Logs an error and skips the addon | Logs an error and skips the addon |
| The package has no `__fdm_setup_module__` | Logs a warning and skips the addon | Logs a warning and skips the addon |
| The setup module cannot be found | Raises `ImproperlyConfigured` naming the addon | Logs a warning and skips the addon |
| The setup module raises while it runs | Raises `ImproperlyConfigured` naming the addon | Logs a warning and skips the addon |

`setup()` applies an addon's settings and nothing else. An addon adds its apps and middleware by assigning `INSTALLED_APPS` and `MIDDLEWARE` in its setup module, and the portal includes the addon's URLs in its own URLconf.

[How to create an addon](../how-to/create-an-addon.md) shows how to write one.

## Environment files

Before FairDM applies any layer, it reads environment files with django-environ. They are looked up in `base_dir`, and they are read in this order.

| Order | File | Overwrites a variable that is already set |
| --- | --- | --- |
| 1 | `stack.env`, if it exists | No |
| 2 | `stack.<environment>.env`, if it exists | No |
| 3 | The file named by `env_file`, if it exists | Yes |

A variable already set in the process environment therefore beats the first two files. Only the explicit `env_file` overwrites it, and it also overwrites variables the two earlier files set. Each file holds one `NAME=value` per line. [Settings](settings.md#environment-variables) lists the variables.

## `show_config`

```bash
python manage.py show_config [SETTING]
```

| Form | What it prints |
| --- | --- |
| `show_config` | One line for each layer `setup()` considered, in order, as `<layer>: found` or `<layer>: absent`. The layers are named `baseline`, `fairdm override`, `addons` and `portal override`. |
| `show_config SETTING` | `SETTING = <value> (<layer>)`, where the layer is the last of those four that changed the setting, or `unattributed` when none did. A secret value is cleansed first. |

The command reports layers 1 to 4. An assignment in the portal's settings module after the `setup()` call is not a layer it records, so for a setting you assign there it names the layer that set the value before your assignment, or `unattributed`.

## Boot checks

When the settings in force are the production baseline, FairDM runs its production-critical checks as the portal starts and stops the portal if one fails. `python manage.py check --deploy` runs the full set against production standards in any environment. The checks, their ids and their fixes are in [Configuration checks](../../administrators/reference/configuration-checks.md).
