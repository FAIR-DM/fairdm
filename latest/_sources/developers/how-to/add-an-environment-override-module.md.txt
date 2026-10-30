# How to add an environment override module

An environment override module holds the settings that differ between environments, such as a language list that only your production portal narrows or a relaxed setting for a staging copy. You add one when assigning the value in your settings module would need an `if` on the environment.

## Before you start

Your portal's settings module calls `fairdm.setup()`. You know the name of the environment, which is the value of `DJANGO_ENV`. The name is `development` for FairDM's development settings, `production` when the variable is unset, or a name of your own such as `staging`. See [Configuration](../reference/configuration.md#the-resolved-environment).

## Steps

1. Create a file named exactly after the environment, with `.py` on the end, in the same directory as your settings module. For the recommended layout, that is `config/`.

   ```text
   config/
   ├── settings.py       # calls fairdm.setup()
   ├── development.py    # applied when DJANGO_ENV=development
   ├── staging.py        # applied when DJANGO_ENV=staging
   └── production.py     # applied when DJANGO_ENV=production
   ```

   The name is matched literally. `DJANGO_ENV=development` finds `development.py`, not `dev.py` or `Development.py`. The file must sit beside the settings module and not in a subdirectory.

2. Assign the settings in the file. Do not call `fairdm.setup()` in it. FairDM runs the module inside the call that is already in progress, so every setting built so far, `env` and `BASE_DIR` are in scope.

   ```python
   # config/staging.py
   SECURE_HSTS_SECONDS = 0
   SITE_NAME = "My Portal (staging)"
   ```

3. If you narrow `LANGUAGES`, narrow the translation settings in the same file. django-parler refuses language codes that `LANGUAGES` does not list, and FairDM reports the mismatch as `fairdm.E400`.

   ```python
   # config/production.py
   from django.utils.translation import gettext_lazy as _

   LANGUAGES = [
       ("en", _("English")),
       ("de", _("German")),
   ]

   PARLER_LANGUAGES = {
       1: (
           {"code": "en"},
           {"code": "de"},
       ),
       "default": {
           "fallback": "en",
           "hide_untranslated": False,
       },
   }
   ```

4. Set `DJANGO_ENV` to the environment name, with the rest of the portal's variables, and list the layers FairDM applied.

   ```bash
   DJANGO_ENV=staging python manage.py show_config
   ```

## The result

The command prints a line for each layer. The line for your module reads `portal override: found`. If it reads `portal override: absent`, the file name or its place is wrong.

Your module is layer 4. It overrides FairDM's defaults, FairDM's own `development` module and your addons, and an assignment in your settings module after the `fairdm.setup()` call overrides it. When FairDM and your portal both have a module for the environment, both apply, FairDM's first, so your values win.

A name with no FairDM module, such as `staging`, composes the production baseline with your module on top. FairDM therefore checks a `staging` portal as production when it starts. It needs a real secret key, a database and a shared cache, as [Configuration checks](../../administrators/reference/configuration-checks.md) lists. Only `development` skips those checks.

The environment name also selects the environment file `stack.<environment>.env`, which [Configuration](../reference/configuration.md#environment-files) describes. [How FairDM configures a portal](../../explanation/how-fairdm-configures-a-portal.md) explains why a module is chosen by existing.
