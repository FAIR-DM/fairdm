# Settings

This page lists every setting that FairDM defines or reads, and the third-party settings that FairDM gives a value and that a portal is expected to change. Each entry gives the name, the type, the default, what the setting does and what it accepts. The settings are grouped by subject, and each group is in alphabetical order. It does not explain how to change a setting, which is in [How to override a FairDM setting](../how-to/override-a-fairdm-setting.md), or how FairDM builds the settings from layers, which is in [Configuration](configuration.md).

Where a default differs between environments, the entry gives one default for production and one for development. Production is the baseline `fairdm.setup()` builds. Development is the baseline with FairDM's `development` override applied, which happens when `DJANGO_ENV` is `development`.

Environment variables are listed in their own group at the end. A setting that reads an environment variable names it in its default, and the variable has an entry of its own.

The groups are:

- [Site and environment](#site-and-environment)
- [Apps, middleware and templates](#apps-middleware-and-templates)
- [Page shell and branding](#page-shell-and-branding)
- [Home page](#home-page)
- [Language and time](#language-and-time)
- [Security and hosts](#security-and-hosts)
- [Database](#database)
- [Cache](#cache)
- [Static and media files](#static-and-media-files)
- [Background tasks](#background-tasks)
- [Email](#email)
- [Authentication and sign-in](#authentication-and-sign-in)
- [Profiles and claiming](#profiles-and-claiming)
- [Records and content](#records-and-content)
- [REST API](#rest-api)
- [Legal documents](#legal-documents)
- [Logging and monitoring](#logging-and-monitoring)
- [Settings for other packages](#settings-for-other-packages)
- [Environment variables](#environment-variables)

## Site and environment

### `ADMIN_URL`

- **Type**: `str`
- **Default**: `"admin/"`, from `DJANGO_ADMIN_URL`
- **What it does**: The address the Django administration interface is served at.
- **Accepts**: A URL route without a leading slash and with a trailing slash, such as `"staff/"`.

### `ADMINS`

- **Type**: `list[tuple[str, str]]`
- **Default**: `[("Super User", <DJANGO_SUPERUSER_EMAIL>)]`
- **What it does**: The people Django emails when a request ends in a server error and `DEBUG` is off.
- **Accepts**: A list of `(name, email address)` pairs.

### `BASE_DIR`

- **Type**: `pathlib.Path`
- **Default**: The `base_dir` argument of `fairdm.setup()`, or the directory above the one that holds the portal's settings module
- **What it does**: The portal's root directory. FairDM looks here for `stack.env`, `stack.<environment>.env`, `templates/`, `assets/`, `fixtures/` and `project/locale/`, and puts `static/` and `media/` here. `fairdm.setup()` sets it.
- **Accepts**: A `Path` to a directory. Pass it through `fairdm.setup(base_dir=...)`. Assigning it after the call does not move the paths FairDM has already built from it.

### `DJANGO_ENV`

- **Type**: `str`
- **Default**: `"production"`, from the `DJANGO_ENV` environment variable
- **What it does**: The name of the environment. It selects the override modules that `fairdm.setup()` applies and the `stack.<environment>.env` file it reads. FairDM also reads it at start-up: only the value `development` skips the production-critical checks.
- **Accepts**: Any string. A name with no override module gets the production baseline. `fairdm.setup()` sets the setting from the environment variable, so set the variable and not the setting.

### `DJANGO_SETUP_TOOLS`

- **Type**: `dict`
- **Default**: One entry under the key `""` with two lists. `on_initial` runs `makemigrations --no-input`, `migrate --no-input`, `createsuperuser --no-input` with the first and last name from `DJANGO_SUPERUSER_FIRSTNAME` and `DJANGO_SUPERUSER_LASTNAME`, and `loaddata django-waffle`. `always_run` runs `migrate --no-input`, `collectstatic --noinput`, `preload`, `seed_licenses` and the script `django_setup_tools.scripts.sync_site_id`.
- **What it does**: The commands and scripts that the django-setup-tools app runs. The [container images](container-images.md) do not use it, and run their own [start sequence](container-images.md#start-sequence).
- **Accepts**: The format django-setup-tools reads: a dictionary of lists, each item a tuple holding a command name and its arguments, or the dotted path of a script.

### `FAIRDM_APPS`

- **Type**: `list[str]`
- **Default**: The `apps` argument of `fairdm.setup()`, or `[]`
- **What it does**: The portal's own apps. `INSTALLED_APPS` places them ahead of FairDM's apps, so a template or static file in a portal app wins over a FairDM file at the same path. `fairdm.setup()` sets it.
- **Accepts**: A list of app module paths. Pass them through `fairdm.setup(apps=[...])`. Assigning the setting after the call does not change `INSTALLED_APPS`.

### `MANAGERS`

- **Type**: `list[tuple[str, str]]`
- **Default**: The value of `ADMINS`
- **What it does**: The people Django emails about broken links when `BrokenLinkEmailsMiddleware` is installed. FairDM does not install it.
- **Accepts**: A list of `(name, email address)` pairs.

### `META_SITE_NAME`

- **Type**: `str`
- **Default**: The value of `SITE_NAME`
- **What it does**: The site name that django-meta writes into the page's `og:site_name` tag.
- **Accepts**: Any string.

### `ROOT_URLCONF`

- **Type**: `str`
- **Default**: `"config.urls"`, from `DJANGO_ROOT_URLCONF`
- **What it does**: The module that holds the portal's URL patterns.
- **Accepts**: The dotted path of a URLconf module. FairDM's own patterns are in `fairdm.conf.urls`, which a portal's URLconf can include.

### `SITE_DOMAIN`

- **Type**: `str`
- **Default**: `""`, from `DJANGO_SITE_DOMAIN`
- **What it does**: The domain the portal answers on. It is the first entry of `ALLOWED_HOSTS`, it forms the default sender addresses in [Email](#email), and it is passed to templates as `config.site_domain`.
- **Accepts**: A host name without a scheme or a path, such as `"portal.example.org"`. An empty value leaves `ALLOWED_HOSTS` empty unless `DJANGO_ALLOWED_HOSTS` names hosts.

### `SITE_ID`

- **Type**: `int`
- **Default**: `1`, from `DJANGO_SITE_ID`
- **What it does**: The primary key of the `Site` row that Django's sites framework treats as this portal.
- **Accepts**: The primary key of an existing `Site`.

### `SITE_NAME`

- **Type**: `str`
- **Default**: `"FairDM Demo"`, from `DJANGO_SITE_NAME`
- **What it does**: The portal's name when no name has been saved on the portal identity in the administration interface. It heads the hero on the home page, prefixes email subjects, names the sender of email and is passed to templates as `config.site_name`.
- **Accepts**: Any string.

### `WSGI_APPLICATION`

- **Type**: `str` or `None`
- **Default**: `None`
- **What it does**: Django's setting for the WSGI application object. FairDM leaves it for the portal to set. The [container images](container-images.md) start gunicorn with the `WSGI_APP` variable and do not read this setting.
- **Accepts**: The dotted path of a WSGI callable, such as `"config.wsgi.application"`.

## Apps, middleware and templates

### `CRISPY_ALLOWED_TEMPLATE_PACKS`

- **Type**: `list[str]`
- **Default**: `["daisyui"]`
- **What it does**: The form template packs that django-crispy-forms accepts.
- **Accepts**: A list of pack names. FairDM's forms render with the `daisyui` pack, so keep it in the list.

### `CRISPY_TEMPLATE_PACK`

- **Type**: `str`
- **Default**: `"daisyui"`
- **What it does**: The pack that django-crispy-forms renders forms with.
- **Accepts**: A pack name that is also in `CRISPY_ALLOWED_TEMPLATE_PACKS`.

### `DJANGO_TABLES2_TEMPLATE`

- **Type**: `str`
- **Default**: `"django_tables2/bootstrap5-mvp.html"`
- **What it does**: The template django-tables2 draws tables with, and the template FairDM gives the tables it generates for registered types.
- **Accepts**: A template path.

### `INSTALLED_APPS`

- **Type**: `list[str]`
- **Default**: In this order, Django's admin-related apps and `django.contrib` apps, the apps in [`FAIRDM_APPS`](#fairdm_apps), `fairdm` and its own apps, then the third-party apps FairDM needs. Development appends `django_browser_reload`.
- **What it does**: The apps Django loads. The order matters, because Django takes the first template and static file it finds for a path.
- **Accepts**: A list of app module paths or app configuration paths. Name a portal's apps in `fairdm.setup(apps=[...])` so they come before FairDM's. An app added by assignment after the call comes last and cannot override a FairDM template.

### `MIDDLEWARE`

- **Type**: `list[str]`
- **Default**: In this order, `SecurityMiddleware`, WhiteNoise, Orbit, django-cors-headers, sessions, CSRF, authentication, `mvp_compliance.middleware.AgreementMiddleware`, messages, locale, common, current site, clickjacking, allauth's account middleware, django-htmx, django-tomselect and django-hijack. Development appends `django_browser_reload.middleware.BrowserReloadMiddleware`.
- **What it does**: The request and response middleware. Security, WhiteNoise and authentication must keep their places, and the agreement middleware must come after authentication.
- **Accepts**: A list of dotted paths. Add a portal's own middleware by assignment after `fairdm.setup()`.

### `TEMPLATES`

- **Type**: `list[dict]`
- **Default**: One Django template backend with `DIRS` set to `[BASE_DIR / "templates"]`. Its context processors are Django's `auth`, `messages`, `i18n`, `debug`, `request`, `media`, `csrf`, `tz` and `static`, then `fairdm.utils.context_processors.fairdm` and `mvp.context_processors.mvp_config`. Its builtins are `django.templatetags.i18n` and `easy_icons.templatetags.easy_icons`.
- **What it does**: The template engine configuration. The two FairDM context processors supply `config`, `identity`, `theme_options`, `registry`, `page_config` and `json_config` to every template.
- **Accepts**: Django's `TEMPLATES` format. Add a directory with `TEMPLATES[0]["DIRS"].insert(0, BASE_DIR / "other")` and a context processor by appending to `TEMPLATES[0]["OPTIONS"]["context_processors"]`. Keep the two FairDM processors.

## Page shell and branding

### `EASY_ICONS`

- **Type**: `dict`
- **Default**: Two sets. `default` draws an icon as an `<i>` tag from the `mvp.utils.BS5_ICONS` pack and maps the names FairDM's pages ask for, such as `add`, `edit`, `delete`, `project`, `dataset`, `sample` and `measurement`, to Bootstrap Icons classes. `svg` draws icons from SVG files in an `icons` directory and maps names such as `orcid`, `ror` and `spinner` to files.
- **What it does**: Maps an icon name to the markup that draws it. Templates and menus ask for icons by name.
- **Accepts**: The format django-easy-icons reads. Add or change a name by assigning an item, such as `EASY_ICONS["default"]["icons"]["flask"] = "bi bi-eyedropper"`. Replacing the whole dictionary removes the names FairDM's pages use.

### `FAIRDM_CONFIG`

- **Type**: `dict`
- **Default**: A dictionary with the keys `colors`, `home`, `external_links`, `icon_links`, `logo`, `announcement`, `footer_start`, `footer_center` and `back_to_top_button`.
- **What it does**: FairDM passes the dictionary to every template as `theme_options`. No template that FairDM ships reads it.
- **Accepts**: Any dictionary. Changing it affects only the templates that read `theme_options`.

### `FLEX_MENUS`

- **Type**: `dict`
- **Default**: `{"renderers": {...}}` with three renderers. `sidebar` is `mvp.renderers.SidebarRenderer`, `dock` is `mvp.renderers.MobileFooterNavRenderer` and `plugin-menu-renderer` is `fairdm.contrib.plugins.menus.PluginMenuRenderer`.
- **What it does**: Names the renderers that django-flex-menus uses to draw FairDM's menus.
- **Accepts**: The format django-flex-menus reads. Add a renderer by assigning an item of `FLEX_MENUS["renderers"]`. Removing one of the three breaks the menu that uses it.

### `MVP_CONFIG`

- **Type**: `dict`
- **Default**: `{"brand": {"avatar_resolver": "fairdm.contrib.contributors.utils.helpers.avatar_url"}, "layout": {"sidebar": {"title": "FairDM", "collapse": "icons"}, "navbar": {"end": []}}}`
- **What it does**: Configures django-mvp's page shell. `brand.avatar_resolver` is the function that returns the image of an avatar. The FairDM function returns the contributor's 150 by 150 thumbnail for sizes up to `md`, the 600 by 600 thumbnail for `lg` and larger, and `None` when the contributor has no image. `layout.sidebar.title` is the text above the sidebar menu. `layout.navbar.end` is empty because the sidebar already carries the sign-in and theme controls.
- **Accepts**: The format django-mvp reads. Assign items, such as `MVP_CONFIG["layout"]["sidebar"]["title"] = "My Portal"`. The avatar resolver is a dotted path to a function that takes the object and a size and returns an address or `None`.

### `PAGE_CONFIG`

- **Type**: `dict`
- **Default**: `brand` with `text` set to [`SITE_NAME`](#site_name), `image_light` set to `"img/brand/logo.svg"` and `icon_light` set to `"img/brand/icon.svg"`. `sidebar` with `show_at` set to `False` and `collapsible` set to `True`. `navbar` with `fixed` set to `False` and `menu_visible_at` set to `"lg"`. `actions` holding three links: a theme toggle, a GitHub link to the FairDM repository and a link to `/docs/`.
- **What it does**: Describes the page shell. FairDM passes it to every template as `page_config`, with the logo, icon and name saved on the portal identity in the administration interface laid over `brand`. FairDM's sign-in and entrance pages read `brand.text`. `sidebar.show_at` is `False` for a navbar-only layout or a breakpoint from `"sm"` to `"xxl"` to show the sidebar in the page flow. `navbar.menu_visible_at` applies only when `sidebar.show_at` is `False`, and `False` hides the navbar menu.
- **Accepts**: A dictionary with the keys above. Assign items so the other keys stay, such as `PAGE_CONFIG["actions"] = []` to remove the three default links.

## Home page

### `HOME_PAGE_CONFIG`

- **Type**: `dict`
- **Default**: Not set. A key you leave out keeps the value in the table below, which comes from `FairDMHomeView.hero_defaults`.
- **What it does**: The words and picture of the hero on the landing page that visitors who have not signed in see. [Home page](home-page.md) describes the page.
- **Accepts**: A dictionary with any of these keys.

| Key | Default | What it does and what it accepts |
| --- | --- | --- |
| `eyebrow` | `"Research data portal"` | The short line above the title. A string, or `False` to hide it. |
| `title` | `"Welcome to {site_name}"` | The page heading. A string, or `False` to hide it. |
| `lead` | A sentence about FAIR research data | The sentence under the title. A string, or `False` to hide it. |
| `image` | `None` | A background picture. A path under your static files, a path that starts with `/`, or a full address. |
| `logo` | `True` | Whether the portal logo shows above the title. It is drawn only when there is no `image`. |

`eyebrow`, `title` and `lead` may contain `{site_name}`. It is replaced by the name saved on the portal identity, or by [`SITE_NAME`](#site_name) when none has been saved.

### `PORTAL_DESCRIPTION`

- **Type**: `str`
- **Default**: Not set, read as `""`
- **What it does**: The paragraph in the about section of the landing page. The description saved on the portal identity in the administration interface takes its place once one exists. FairDM also passes it to templates as `config.portal_description`.
- **Accepts**: Plain text.

## Language and time

### `FIXTURE_DIRS`

- **Type**: `tuple[str, ...]`
- **Default**: `(str(BASE_DIR / "fixtures"),)`
- **What it does**: The directories Django searches for fixture files, in addition to each app's `fixtures` directory.
- **Accepts**: A tuple or list of directory paths.

### `LANGUAGE_CODE`

- **Type**: `str`
- **Default**: `"en"`
- **What it does**: The language used when no other is chosen.
- **Accepts**: A language code that is in `LANGUAGES`.

### `LANGUAGES`

- **Type**: `list[tuple[str, str]]`
- **Default**: Not set by FairDM, so Django's default list applies
- **What it does**: The languages the portal offers. FairDM reads it to check that [`PARLER_LANGUAGES`](#parler_languages) names only languages in this list. A mismatch stops the portal with `fairdm.E400`.
- **Accepts**: A list of `(code, name)` pairs. If you narrow it, narrow `PARLER_LANGUAGES` and `PARLER_DEFAULT_LANGUAGE_CODE` to match. See [How to add an environment override module](../how-to/add-an-environment-override-module.md) for an example.

### `LOCALE_PATHS`

- **Type**: `list[str]`
- **Default**: `[str(BASE_DIR / "project" / "locale")]`
- **What it does**: The directories Django searches for translation files, ahead of each app's own.
- **Accepts**: A list of directory paths.

### `PARLER_DEFAULT_LANGUAGE_CODE`

- **Type**: `str`
- **Default**: `"en"`
- **What it does**: The language django-parler uses for translated fields when no other applies.
- **Accepts**: A code that is in `LANGUAGES`.

### `PARLER_LANGUAGES`

- **Type**: `dict`
- **Default**: Site `1` offers `en`, `fr` and `de`, and the `default` key holds `{"fallback": "en", "hide_untranslated": False}`.
- **What it does**: The languages that translated fields on FairDM models can hold, per site.
- **Accepts**: The format django-parler reads. Every code, and the `default` fallback, must be in `LANGUAGES` or have a code in `LANGUAGES` as its base, such as `fr-ca` with `fr`. Otherwise the portal stops with `fairdm.E400`.

### `TIME_ZONE`

- **Type**: `str`
- **Default**: `"UTC"`, from `DJANGO_TIME_ZONE`
- **What it does**: The time zone Django shows times in.
- **Accepts**: A name from the IANA time zone database, such as `"Europe/London"`. [`CELERY_TIMEZONE`](#celery_timezone) reads the same variable when `fairdm.setup()` runs, so assigning `TIME_ZONE` afterwards does not change it. Set `DJANGO_TIME_ZONE` to change both.

### `USE_I18N`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Turns Django's translation system on.
- **Accepts**: `True` or `False`.

### `USE_L10N`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: FairDM sets it. Django 6 does not read it, because it always localises formats.
- **Accepts**: `True` or `False`, with no effect.

### `USE_TZ`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Stores times in UTC and converts them for display.
- **Accepts**: `True`. FairDM's models assume it.

## Security and hosts

### `ALLOWED_HOSTS`

- **Type**: `list[str]`
- **Default**: Production: `DJANGO_SITE_DOMAIN` followed by each host in `DJANGO_ALLOWED_HOSTS`, leaving out empty entries, so `[]` when both are unset. Development: `["*"]`.
- **What it does**: The host names the portal answers to. An empty list stops a production portal with `fairdm.E003`, and a list holding `"*"` stops it with `fairdm.E004`.
- **Accepts**: A list of host names. Set `DJANGO_ALLOWED_HOSTS` to a comma-separated list for more than the site domain.

### `CSRF_COOKIE_HTTPONLY`

- **Type**: `bool`
- **Default**: `False`
- **What it does**: Whether the CSRF cookie is hidden from scripts. It is `False` because FairDM's scripts read the token for AJAX requests.
- **Accepts**: `True` or `False`.

### `CSRF_COOKIE_NAME`

- **Type**: `str`
- **Default**: Production: `"__Secure-csrftoken"`. Development: `"csrftoken"`.
- **What it does**: The name of the CSRF cookie.
- **Accepts**: A cookie name. A name that starts with `__Secure-` or `__Host-` needs [`CSRF_COOKIE_SECURE`](#csrf_cookie_secure) on, or browsers discard the cookie and `fairdm.E006` reports it.

### `CSRF_COOKIE_SECURE`

- **Type**: `bool`
- **Default**: Production: `True`. Development: `False`.
- **What it does**: Sends the CSRF cookie only over HTTPS.
- **Accepts**: `True` or `False`.

### `CSRF_TRUSTED_ORIGINS`

- **Type**: `list[str]`
- **Default**: `https://` followed by each entry of `ALLOWED_HOSTS`
- **What it does**: The origins Django accepts for requests that carry a CSRF token from another origin.
- **Accepts**: A list of origins with a scheme, such as `"https://portal.example.org"`. The list is built from `ALLOWED_HOSTS` when `fairdm.setup()` runs, so extend it if you add hosts afterwards.

### `DEBUG`

- **Type**: `bool`
- **Default**: Production: `False`, from `DJANGO_DEBUG`. Development: `True`, whatever `DJANGO_DEBUG` says.
- **What it does**: Turns Django's debug pages on. A production portal with `DEBUG` on stops with `fairdm.E005`.
- **Accepts**: `True` or `False`.

### `INTERNAL_IPS`

- **Type**: `list[str]`
- **Default**: For each address of the machine, the same address with its last number replaced by `1`
- **What it does**: The addresses that see debug-only tools.
- **Accepts**: A list of IP addresses.

### `SECRET_KEY`

- **Type**: `str`
- **Default**: Production: `""`, from `DJANGO_SECRET_KEY`. Development: `"django-insecure-dev-key-CHANGE-THIS-IN-PRODUCTION"` when the variable is unset.
- **What it does**: The key Django signs sessions, tokens and cookies with. FairDM ships no working key for production. A production portal stops with `fairdm.E001` when the key is empty, starts with `django-insecure-` or is shorter than 50 characters.
- **Accepts**: A private random string of 50 characters or more. Never commit it. Set `DJANGO_SECRET_KEY`.

### `SECURE_BROWSER_XSS_FILTER`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: FairDM sets it. Django 6 does not read it.
- **Accepts**: `True` or `False`, with no effect.

### `SECURE_CONTENT_TYPE_NOSNIFF`

- **Type**: `bool`
- **Default**: `True`, from `DJANGO_SECURE_CONTENT_TYPE_NOSNIFF`
- **What it does**: Sends `X-Content-Type-Options: nosniff`.
- **Accepts**: `True` or `False`.

### `SECURE_HSTS_INCLUDE_SUBDOMAINS`

- **Type**: `bool`
- **Default**: Production: `True`, from `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`. Development: `False`.
- **What it does**: Adds `includeSubDomains` to the HSTS header.
- **Accepts**: `True` or `False`.

### `SECURE_HSTS_PRELOAD`

- **Type**: `bool`
- **Default**: Production: `True`, from `DJANGO_SECURE_HSTS_PRELOAD`. Development: `False`.
- **What it does**: Adds `preload` to the HSTS header.
- **Accepts**: `True` or `False`.

### `SECURE_HSTS_SECONDS`

- **Type**: `int`
- **Default**: Production: `60`. Development: `0`.
- **What it does**: How long, in seconds, a browser remembers to use HTTPS only. The production value is low so that a mistake lasts a minute. Raise it once HTTPS works.
- **Accepts**: A number of seconds. `0` turns HSTS off.

### `SECURE_PROXY_SSL_HEADER`

- **Type**: `tuple[str, str]`
- **Default**: `("HTTP_X_FORWARDED_PROTO", "https")`
- **What it does**: Tells Django which request header carries the original scheme when a proxy ends TLS. With the default, a request without `X-Forwarded-Proto: https` counts as plain HTTP and is redirected.
- **Accepts**: A `(header, value)` pair, or `None` when no proxy sits in front of the portal.

### `SECURE_SSL_REDIRECT`

- **Type**: `bool`
- **Default**: Production: `True`, from `DJANGO_SECURE_SSL_REDIRECT`. Development: `False`.
- **What it does**: Redirects plain HTTP requests to HTTPS.
- **Accepts**: `True` or `False`.

### `SESSION_COOKIE_HTTPONLY`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Hides the session cookie from scripts.
- **Accepts**: `True` or `False`.

### `SESSION_COOKIE_NAME`

- **Type**: `str`
- **Default**: Production: `"__Secure-sessionid"`. Development: `"sessionid"`.
- **What it does**: The name of the session cookie.
- **Accepts**: A cookie name. A name that starts with `__Secure-` or `__Host-` needs [`SESSION_COOKIE_SECURE`](#session_cookie_secure) on, or `fairdm.E006` reports it.

### `SESSION_COOKIE_SECURE`

- **Type**: `bool`
- **Default**: Production: `True`. Development: `False`.
- **What it does**: Sends the session cookie only over HTTPS.
- **Accepts**: `True` or `False`.

### `X_FRAME_OPTIONS`

- **Type**: `str`
- **Default**: `"DENY"`
- **What it does**: Stops other sites from showing a portal page in a frame.
- **Accepts**: `"DENY"` or `"SAMEORIGIN"`.

## Database

### `BACKUP_PUBLIC_KEY`

- **Type**: `str`
- **Default**: `""`, from the environment variable of the same name
- **What it does**: The public key every backup is encrypted to. With it set, each database and media backup is written as a `.gpg` file that only the holder of the private key reads. With it empty, backups are written unencrypted, which a development portal accepts. A production portal with it empty stops with [`fairdm.E700`](../../administrators/reference/configuration-checks.md#fairdm-e700-no-backup-public-key-is-set), and with a value that cannot encrypt with [`fairdm.E701`](../../administrators/reference/configuration-checks.md#fairdm-e701-the-backup-public-key-cannot-be-used). FairDM trusts this key for the length of a backup, so the key needs no signing or trusting on the server.
- **Accepts**: An armoured OpenPGP public key, the text between `-----BEGIN PGP PUBLIC KEY BLOCK-----` and `-----END PGP PUBLIC KEY BLOCK-----`. The environment variable may hold it on several lines. A private key is refused. See [How to back up a portal](../how-to/back-up-a-portal.md#encrypt-the-backups).

### `DATABASES`

- **Type**: `dict`
- **Default**: One `default` database built by django-environ. It reads `DATABASE_URL` when set, and otherwise composes a URL from `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` and `POSTGRES_DB`. The engine is always `django.contrib.gis.db.backends.postgis`, whatever scheme the URL names. `ATOMIC_REQUESTS` is `True` and `CONN_MAX_AGE` is `60`, from the variable of that name.
- **What it does**: The portal's database connection. FairDM runs only on PostgreSQL with the PostGIS extension. A production portal with another engine stops with `fairdm.E101`, with no database with `fairdm.E100`, and with no database name with `fairdm.E102`.
- **Accepts**: The format Django reads. Change a connection option by assigning an item, such as `DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}`.

### `DBBACKUP_CLEANUP_KEEP`

- **Type**: `int`
- **Default**: `4`, from [`BACKUP_KEEP`](#backup_keep)
- **What it does**: How many database backups django-dbbackup keeps. Each backup removes the oldest beyond this count.
- **Accepts**: A whole number.

### `DBBACKUP_CLEANUP_KEEP_MEDIA`

- **Type**: `int`
- **Default**: `4`, from [`BACKUP_KEEP`](#backup_keep)
- **What it does**: How many media backups django-dbbackup keeps. It counts media backups on their own, apart from database backups.
- **Accepts**: A whole number.

### `DBBACKUP_CONNECTORS`

- **Type**: `dict`
- **Default**: `{"default": {"CONNECTOR": "dbbackup.db.postgresql.PgDumpBinaryConnector"}}`
- **What it does**: How django-dbbackup dumps and restores the database. The connector writes PostgreSQL's custom format, which is already compressed and which `pg_restore` restores, PostGIS included, into an empty database.
- **Accepts**: The format django-dbbackup reads.

### `DBBACKUP_FILENAME_TEMPLATE`

- **Type**: `str`
- **Default**: `"{databasename}-{servername}-{datetime}.{extension}"`
- **What it does**: The file name of a database backup.
- **Accepts**: A template with the placeholders django-dbbackup defines.

### `DBBACKUP_HOSTNAME`

- **Type**: `str`
- **Default**: `"fairdm"`, from [`BACKUP_SERVER_NAME`](#backup_server_name)
- **What it does**: The server name in the file name of a backup.
- **Accepts**: A name without spaces.

### `DBBACKUP_MEDIA_FILENAME_TEMPLATE`

- **Type**: `str`
- **Default**: `"{databasename}_media-{servername}-{datetime}.{extension}"`
- **What it does**: The file name of a media backup.
- **Accepts**: A template with the placeholders django-dbbackup defines.

```{note}
django-dbbackup 5 refuses the two storage settings of the 4.x series, so FairDM no longer sets them. A portal that sets either moves its choice to `STORAGES["dbbackup"]`, described under [`STORAGES`](#storages).
```

### `DEFAULT_AUTO_FIELD`

- **Type**: `str`
- **Default**: `"django.db.models.BigAutoField"`
- **What it does**: The type of the automatic primary key on models that declare none.
- **Accepts**: The dotted path of an auto field class.

### `GDAL_LIBRARY_PATH`

- **Type**: `str` or `None`
- **Default**: `None`, or the value of the variable of the same name when it is not empty
- **What it does**: Where GeoDjango finds the GDAL library. `None` keeps Django's search of the system library path.
- **Accepts**: The path of the GDAL shared library. Needed only where GDAL is not on the system library path. The [container images](container-images.md) need no value.

### `GEOS_LIBRARY_PATH`

- **Type**: `str` or `None`
- **Default**: `None`, or the value of the variable of the same name when it is not empty
- **What it does**: Where GeoDjango finds the GEOS library.
- **Accepts**: The path of the GEOS shared library. Needed only where GEOS is not on the system library path.

## Cache

### `CACHES`

- **Type**: `dict`
- **Default**: Production: two aliases, `default` and `vocabularies`, each a `django_redis.cache.RedisCache` whose `LOCATION` is `REDIS_URL`, with the `DefaultClient` and `IGNORE_EXCEPTIONS` set to `True`. When `REDIS_URL` is unset the location is the placeholder `redis://unconfigured.invalid:6379/0`. Development without `REDIS_URL`: both aliases are Django's in-process `LocMemCache`.
- **What it does**: The portal's caches. They also hold the API and sign-in rate counts, so a production portal needs a cache shared by all its processes. A production portal without one stops with `fairdm.E200`.
- **Accepts**: The format Django reads. Keep both aliases. Change one option by assigning an item, such as `CACHES["default"]["TIMEOUT"] = 600`.

### `COLLECTFASTA_CACHE`

- **Type**: `str`
- **Default**: `"collectfasta"`
- **What it does**: The cache alias django-collectfasta would use. FairDM does not install collectfasta, so the setting has no effect unless a portal installs it.
- **Accepts**: A cache alias.

### `COLLECTFASTA_THREADS`

- **Type**: `int`
- **Default**: `8`
- **What it does**: The number of threads django-collectfasta would use. It has no effect unless a portal installs collectfasta.
- **Accepts**: A whole number.

### `VOCABULARY_DEFAULT_CACHE`

- **Type**: `str`
- **Default**: `"default"`
- **What it does**: The cache alias that django-research-vocabs stores vocabulary data in.
- **Accepts**: A key of `CACHES`.

## Static and media files

### `AWS_ACCESS_KEY_ID`

- **Type**: `str`
- **Default**: `""`, from `S3_ACCESS_KEY_ID`
- **What it does**: The access key for S3 media storage.
- **Accepts**: An access key. Set `S3_ACCESS_KEY_ID`.

### `AWS_S3_REGION_NAME`

- **Type**: `str`
- **Default**: `""`, from `S3_REGION_NAME`
- **What it does**: The region of the S3 bucket.
- **Accepts**: A region name such as `"eu-central-1"`.

### `AWS_SECRET_ACCESS_KEY`

- **Type**: `str`
- **Default**: `""`, from `S3_SECRET_ACCESS_KEY`
- **What it does**: The secret key for S3 media storage.
- **Accepts**: A secret key. Set `S3_SECRET_ACCESS_KEY` and keep it out of the repository.

### `AWS_STORAGE_BUCKET_NAME`

- **Type**: `str`
- **Default**: `""`, from `S3_BUCKET_NAME`
- **What it does**: The S3 bucket that holds the media files.
- **Accepts**: A bucket name.

### `DATA_UPLOAD_MAX_MEMORY_SIZE`

- **Type**: `int`
- **Default**: `5242880`, which is 5 MiB
- **What it does**: The most request body Django reads into memory before it refuses the request. It does not limit file uploads.
- **Accepts**: A number of bytes, or `None` for no limit.

### `MEDIA_ROOT`

- **Type**: `str`
- **Default**: `str(BASE_DIR / "media")`
- **What it does**: The directory uploaded files are written to when media storage is the local file system. A production portal serves static files itself but not `MEDIA_URL`, so serve this directory from the proxy or use S3 storage.
- **Accepts**: An absolute directory path.

### `MEDIA_URL`

- **Type**: `str`
- **Default**: `"/media/"`
- **What it does**: The address that media files are served from. FairDM serves it only when `DEBUG` is on.
- **Accepts**: A path that ends in a slash, or a full address.

### `STATIC_ROOT`

- **Type**: `str`
- **Default**: `str(BASE_DIR / "static")`
- **What it does**: The directory `collectstatic` writes to and WhiteNoise serves from.
- **Accepts**: An absolute directory path.

### `STATIC_URL`

- **Type**: `str`
- **Default**: `"/static/"`
- **What it does**: The address that static files are served from.
- **Accepts**: A path that ends in a slash.

### `STATICFILES_DIRS`

- **Type**: `list[str]`
- **Default**: `[str(BASE_DIR / "assets")]` when `BASE_DIR / "assets"` exists as `fairdm.setup()` runs. Otherwise the setting is not defined.
- **What it does**: Extra directories `collectstatic` takes files from.
- **Accepts**: A list of directory paths.

### `STATICFILES_FINDERS`

- **Type**: `list[str]`
- **Default**: The file system finder and the app directories finder
- **What it does**: How Django finds static files.
- **Accepts**: A list of finder dotted paths.

### `STORAGES`

- **Type**: `dict`
- **Default**: Production: `default` is `FileSystemStorage` at `BASE_DIR / "media"`, and `staticfiles` is `whitenoise.storage.CompressedStaticFilesStorage`. When `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` and `S3_BUCKET_NAME` are all set, `default` is `storages.backends.s3boto3.S3Boto3Storage`. Development: Django's plain file storage for both, and no S3. `dbbackup` is `FileSystemStorage` at the directory in `BACKUP_DIR`, or at `BASE_DIR / "backups"` when `BACKUP_DIR` is empty.
- **What it does**: The storage for uploaded files (`default`), collected static files (`staticfiles`) and backups (`dbbackup`). FairDM does not compress or fingerprint static files.
- **Accepts**: The format Django reads. Add a storage by assigning an item, such as `STORAGES["exports"] = {...}`. Replace where backups go by assigning `STORAGES["dbbackup"]`. The `BACKUP_DIR` container image variable sets the directory the container writes backups to; see [Container images](container-images.md).

### `THUMBNAIL_ALIASES`

- **Type**: `dict`
- **Default**: For all models, `core_small` (600 by 400, smart crop) and `core_large` (1200 by 800, smart crop). For the `contributors` app, `thumb` (48 by 48), `small` (150 by 150) and `medium` (600 by 600), all without cropping.
- **What it does**: The named thumbnail sizes that FairDM's templates ask for.
- **Accepts**: The format easy-thumbnails reads. Add an alias by assigning an item. Replacing the dictionary removes the sizes FairDM's pages use.

### `THUMBNAIL_CACHE_DIMENSIONS`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Caches the dimensions of thumbnails in the database.
- **Accepts**: `True` or `False`.

### `THUMBNAIL_DEBUG`

- **Type**: `bool`
- **Default**: Production: `False`. Development: `True`.
- **What it does**: When on, easy-thumbnails raises an error for a missing source file and the page returns a 500. When off, it shows a blank image.
- **Accepts**: `True` or `False`.

### `THUMBNAIL_PROCESSORS`

- **Type**: `list[str]`
- **Default**: The colourspace, autocrop, scale-and-crop and filters processors of easy-thumbnails
- **What it does**: The steps that make a thumbnail.
- **Accepts**: A list of processor dotted paths.

### `THUMBNAIL_SUBDIR`

- **Type**: `str`
- **Default**: `"thumbs"`
- **What it does**: The directory, beside each source image, that holds its thumbnails.
- **Accepts**: A directory name.

### `THUMBNAIL_WIDGET_OPTIONS`

- **Type**: `dict`
- **Default**: `{"size": (150, 100)}`
- **What it does**: The size of the preview that easy-thumbnails' image widget shows.
- **Accepts**: A dictionary with a `size` pair.

### `WHITENOISE_MANIFEST_STRICT`

- **Type**: `bool`
- **Default**: `False`
- **What it does**: WhiteNoise's setting for a missing manifest entry. FairDM does not use a manifest storage, so the setting changes nothing unless a portal does.
- **Accepts**: `True` or `False`.

## Background tasks

The Celery settings use the `CELERY_` prefix, which FairDM's Celery application reads through `app.config_from_object("django.conf:settings", namespace="CELERY")`.

### `CELERY_ACCEPT_CONTENT`

- **Type**: `list[str]`
- **Default**: `["json"]`
- **What it does**: The content types a worker accepts.
- **Accepts**: A list of Celery content types.

### `CELERY_BEAT_SCHEDULER`

- **Type**: `str`
- **Default**: `"django_celery_beat.schedulers:DatabaseScheduler"`
- **What it does**: The scheduler Celery beat uses, so schedules are stored in the database.
- **Accepts**: The dotted path of a scheduler.

### `CELERY_BROKER_URL`

- **Type**: `str`
- **Default**: `""`, from `REDIS_URL`
- **What it does**: The message broker. A portal without one stops `check --deploy` with `fairdm.E300`.
- **Accepts**: A broker URL such as `"redis://redis:6379/0"`. The setting takes its value when `fairdm.setup()` runs. Set `REDIS_URL` and not the setting, or also reassign `CELERY_RESULT_BACKEND`.

### `CELERY_RESULT_BACKEND`

- **Type**: `str`
- **Default**: The value of `CELERY_BROKER_URL`
- **What it does**: Where task results are stored.
- **Accepts**: A result backend URL.

### `CELERY_RESULT_BACKEND_ALWAYS_RETRY`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Retries reading a result when the backend raises an error that can be retried.
- **Accepts**: `True` or `False`.

### `CELERY_RESULT_BACKEND_MAX_RETRIES`

- **Type**: `int`
- **Default**: `10`
- **What it does**: The most retries of a result backend operation.
- **Accepts**: A whole number.

### `CELERY_RESULT_EXTENDED`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Stores the task name, arguments and worker with each result.
- **Accepts**: `True` or `False`.

### `CELERY_RESULT_SERIALIZER`

- **Type**: `str`
- **Default**: `"json"`
- **What it does**: How results are encoded.
- **Accepts**: A serializer name that is in `CELERY_ACCEPT_CONTENT`.

### `CELERY_TASK_ALWAYS_EAGER`

- **Type**: `bool`
- **Default**: Production: `False`. Development with `REDIS_URL` unset: `True`.
- **What it does**: Runs tasks in the calling process, with no worker. `check --deploy` reports `True` as `fairdm.E301`.
- **Accepts**: `True` or `False`.

### `CELERY_TASK_EAGER_PROPAGATES`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Raises an exception from an eager task in the caller.
- **Accepts**: `True` or `False`.

### `CELERY_TASK_SEND_SENT_EVENT`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Sends an event when a task is sent, so monitoring tools can track it.
- **Accepts**: `True` or `False`.

### `CELERY_TASK_SERIALIZER`

- **Type**: `str`
- **Default**: `"json"`
- **What it does**: How task arguments are encoded.
- **Accepts**: A serializer name that is in `CELERY_ACCEPT_CONTENT`.

### `CELERY_TASK_SOFT_TIME_LIMIT`

- **Type**: `int`
- **Default**: `60`
- **What it does**: Seconds after which a task receives a soft time limit exception.
- **Accepts**: A number of seconds.

### `CELERY_TASK_TIME_LIMIT`

- **Type**: `int`
- **Default**: `300`
- **What it does**: Seconds after which a worker kills a task.
- **Accepts**: A number of seconds.

### `CELERY_TIMEZONE`

- **Type**: `str`
- **Default**: `"UTC"`, from `DJANGO_TIME_ZONE`
- **What it does**: The time zone Celery uses for schedules.
- **Accepts**: A name from the IANA time zone database.

### `CELERY_WORKER_SEND_TASK_EVENTS`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Makes workers send events that monitoring tools read.
- **Accepts**: `True` or `False`.

## Email

### `DEFAULT_FROM_EMAIL`

- **Type**: `str`
- **Default**: `"<SITE_NAME> <noreply@<SITE_DOMAIN>>"`. When `DJANGO_DEFAULT_FROM_EMAIL` is set, its value replaces `noreply@<SITE_DOMAIN>`.
- **What it does**: The sender of email the portal sends to people.
- **Accepts**: An address, or a name and address in the form `"Name <address>"`.

### `EMAIL_BACKEND`

- **Type**: `str`
- **Default**: Production: `"django.core.mail.backends.smtp.EmailBackend"`, from the variable of that name. Development: `"django.core.mail.backends.console.EmailBackend"`, which prints email to the console.
- **What it does**: The class that sends email.
- **Accepts**: The dotted path of an email backend.

### `EMAIL_HOST`

- **Type**: `str`
- **Default**: `""`, from the variable of that name
- **What it does**: The SMTP server. A portal sends no email in production until this is set.
- **Accepts**: A host name.

### `EMAIL_HOST_PASSWORD`

- **Type**: `str`
- **Default**: `""`, from the variable of that name
- **What it does**: The password for the SMTP server.
- **Accepts**: A password. Keep it out of the repository.

### `EMAIL_HOST_USER`

- **Type**: `str`
- **Default**: `""`, from the variable of that name
- **What it does**: The user name for the SMTP server.
- **Accepts**: A user name.

### `EMAIL_PORT`

- **Type**: `int`
- **Default**: `587`, from the variable of that name
- **What it does**: The SMTP port.
- **Accepts**: A port number.

### `EMAIL_SUBJECT_PREFIX`

- **Type**: `str`
- **Default**: `"[<SITE_NAME>]"`, or `"[<SITE_DOMAIN>]"` when the site name is empty
- **What it does**: The text Django puts before the subject of email it sends to `ADMINS` and `MANAGERS`.
- **Accepts**: Any string.

### `EMAIL_TIMEOUT`

- **Type**: `int`
- **Default**: `5`
- **What it does**: Seconds to wait for the SMTP server.
- **Accepts**: A number of seconds.

### `EMAIL_USE_TLS`

- **Type**: `bool`
- **Default**: `True`, from the variable of that name
- **What it does**: Starts TLS on the SMTP connection, which suits port 587.
- **Accepts**: `True` or `False`. For a server that expects TLS from the first byte, usually on port 465, set `EMAIL_USE_TLS` to `False` and Django's `EMAIL_USE_SSL` to `True`. FairDM does not set `EMAIL_USE_SSL`.

### `SERVER_EMAIL`

- **Type**: `str`
- **Default**: `"<SITE_NAME> Server <server@<SITE_DOMAIN>>"`. When `DJANGO_SERVER_EMAIL` is set, its value replaces `server@<SITE_DOMAIN>`.
- **What it does**: The sender of error email to `ADMINS`.
- **Accepts**: An address, or a name and address in the form `"Name <address>"`.

## Authentication and sign-in

### `ACCOUNT_ADAPTER`

- **Type**: `str`
- **Default**: `"fairdm.contrib.contributors.adapters.AccountAdapter"`
- **What it does**: The allauth adapter. It opens signup only while the `allow_signup` django-waffle switch is on, and then either when the visitor's email is verified or when [`FAIRDM_INVITATION_ONLY_SIGNUP`](#fairdm_invitation_only_signup) is `False`.
- **Accepts**: The dotted path of a subclass of the FairDM adapter.

### `ACCOUNT_ALLOW_REGISTRATION`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Whether the portal offers account creation. When `False`, the home page drops its create-account links and asks visitors to sign in. FairDM passes it to templates as `config.allow_registration`.
- **Accepts**: `True` or `False`. To close self-service signup for good, see [FAIRDM_INVITATION_ONLY_SIGNUP](#fairdm_invitation_only_signup) and [How to close self-service signup](../../administrators/how-to/close-self-service-signup.md).

### `ACCOUNT_CONFIRM_EMAIL_ON_GET`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Confirms an email address when the person opens the link, with no extra button.
- **Accepts**: `True` or `False`.

### `ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS`

- **Type**: `int`
- **Default**: `3`
- **What it does**: How many days an email confirmation link works.
- **Accepts**: A whole number of days.

### `ACCOUNT_EMAIL_VERIFICATION`

- **Type**: `str`
- **Default**: Production: `"mandatory"`. Development: `"none"`.
- **What it does**: Whether a person must confirm their email address before signing in. FairDM claims an unclaimed profile when its email is confirmed, and only while this is `"mandatory"`.
- **Accepts**: `"mandatory"`, `"optional"` or `"none"`. Only `"mandatory"` claims profiles by email.

### `ACCOUNT_FORMS`

- **Type**: `dict[str, str]`
- **Default**: `login` is `fairdm.contrib.contributors.forms.account.LoginForm` and `signup` is `fairdm.contrib.contributors.forms.account.SignupForm`.
- **What it does**: The allauth forms FairDM replaces.
- **Accepts**: allauth's format. Subclass the FairDM form, so its fields stay.

### `ACCOUNT_LOGIN_METHODS`

- **Type**: `set[str]`
- **Default**: `{"email"}`
- **What it does**: How a person signs in. People sign in with their email address.
- **Accepts**: allauth's format.

### `ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Signs a person in when they confirm their email address.
- **Accepts**: `True` or `False`.

### `ACCOUNT_LOGOUT_ON_GET`

- **Type**: `bool`
- **Default**: `False`
- **What it does**: Whether a plain link signs a person out. The default requires a form post.
- **Accepts**: `True` or `False`.

### `ACCOUNT_MAX_EMAIL_ADDRESSES`

- **Type**: `int`
- **Default**: `4`
- **What it does**: The most email addresses one account may hold.
- **Accepts**: A whole number.

### `ACCOUNT_SIGNUP_FIELDS`

- **Type**: `list[str]`
- **Default**: `["email*", "password1*", "password2*"]`
- **What it does**: The fields on the signup form. A trailing `*` marks a required field.
- **Accepts**: allauth's format.

### `ACCOUNT_SIGNUP_FORM_CLASS`

- **Type**: `str`
- **Default**: `"fairdm.contrib.contributors.forms.person.SignupExtraForm"`
- **What it does**: A form whose extra fields are added to the signup form.
- **Accepts**: The dotted path of a form class.

### `ACCOUNT_USER_MODEL_EMAIL_FIELD`

- **Type**: `str`
- **Default**: Not set by FairDM. FairDM reads it as `"email"` when it is absent.
- **What it does**: The name of the email field on the user model. FairDM reads it when it matches a person to an email address.
- **Accepts**: A field name.

### `ACCOUNT_USER_MODEL_USERNAME_FIELD`

- **Type**: `str` or `None`
- **Default**: `None`
- **What it does**: Tells allauth that the person model has no user name field.
- **Accepts**: `None`. A person is identified by email.

### `AUTH_PASSWORD_VALIDATORS`

- **Type**: `list[dict]`
- **Default**: Django's four validators: user attribute similarity, minimum length, common passwords and numeric passwords
- **What it does**: The rules a new password must pass.
- **Accepts**: Django's format. Add a validator by appending to the list.

### `AUTH_USER_MODEL`

- **Type**: `str`
- **Default**: `"contributors.Person"`
- **What it does**: The person record is the account, so FairDM has no separate user model. `fairdm.setup()` sets it. Do not set it again.
- **Accepts**: `"contributors.Person"`.

### `AUTHENTICATION_BACKENDS`

- **Type**: `list[str]`
- **Default**: In this order, Django's `ModelBackend`, allauth's backend, `fairdm.core.permissions.PolymorphicObjectPermissionBackend`, `fairdm.contrib.contributors.permissions.OrganizationPermissionBackend`, `fairdm.contrib.contributors.permissions.RecordLevelBackend` and `fairdm.permissions.PortalRolePermissionBackend`.
- **What it does**: The classes that authenticate people and answer permission questions. The FairDM backends decide who may open and edit a record.
- **Accepts**: A list of dotted paths. Keep the FairDM backends. Add a backend by appending to the list. Do not add django-guardian's own backend, because FairDM's polymorphic backend replaces it.

### `FAIRDM_INVITATION_ONLY_SIGNUP`

- **Type**: `bool`
- **Default**: `False`
- **What it does**: When `True`, self-service signup is closed and administrators create accounts. A visitor whose session already holds a verified email address can still sign up. Profile claiming works either way: a person holding a valid claim link can still claim their profile.
- **Accepts**: `True` or `False`. The `allow_signup` django-waffle switch must also be on for any signup to open.

### `LOGIN_REDIRECT_URL`

- **Type**: `str`
- **Default**: `"/"`
- **What it does**: Where a person goes after signing in when no other page was asked for.
- **Accepts**: A path or a URL name.

### `LOGIN_URL`

- **Type**: `str`
- **Default**: `"account_login"`
- **What it does**: The page that asks a person to sign in.
- **Accepts**: A path or a URL name.

### `PASSWORD_HASHERS`

- **Type**: `list[str]`
- **Default**: Argon2, then PBKDF2, PBKDF2 with SHA1 and bcrypt with SHA256
- **What it does**: The algorithms that hash passwords. The first one hashes new passwords, and the rest are accepted for existing ones.
- **Accepts**: A list of hasher dotted paths.

### `SILENCED_SYSTEM_CHECKS`

- **Type**: `list[str]`
- **Default**: `["guardian.W001"]`
- **What it does**: Check ids Django does not report. FairDM silences `guardian.W001`, because the check cannot see the FairDM subclasses of guardian's backend.
- **Accepts**: A list of check ids. Extend it by appending, and keep `guardian.W001`. Silencing a check in a report does not stop a production-critical check at start-up.

### `SOCIALACCOUNT_ADAPTER`

- **Type**: `str`
- **Default**: `"fairdm.contrib.contributors.adapters.SocialAccountAdapter"`
- **What it does**: The allauth adapter for social sign-in. It requires the `allow_signup` switch and links a sign-in with ORCID to the profile that holds the same ORCID iD.
- **Accepts**: The dotted path of a subclass of the FairDM adapter.

### `SOCIALACCOUNT_AUTO_SIGNUP`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Creates the account straight from a social sign-in when the provider returns the details allauth needs.
- **Accepts**: `True` or `False`.

### `SOCIALACCOUNT_FORMS`

- **Type**: `dict[str, str]`
- **Default**: `{"signup": "fairdm.contrib.contributors.forms.account.SocialSignupForm"}`
- **What it does**: The allauth form shown after a social sign-in that needs more details.
- **Accepts**: allauth's format. Subclass the FairDM form.

### `SOCIALACCOUNT_PROVIDERS`

- **Type**: `dict`
- **Default**: `{"orcid": {"BASE_DOMAIN": "orcid.org", "MEMBER_API": False}}`, where the domain comes from `ORCID_BASE_DOMAIN`
- **What it does**: The social sign-in providers and their options. FairDM installs the ORCID provider. To offer another provider, add its app to `INSTALLED_APPS` and an entry for it here, and register the provider's client credentials as allauth describes in its [provider documentation](https://docs.allauth.org/en/latest/socialaccount/providers/index.html).
- **Accepts**: allauth's format. Add a provider by assigning an item, such as `SOCIALACCOUNT_PROVIDERS["github"] = {...}`. For development, set `ORCID_BASE_DOMAIN` to `sandbox.orcid.org`.

## Profiles and claiming

### `CLAIM_TOKEN_MAX_AGE`

- **Type**: `int`
- **Default**: `604800`, which is seven days. FairDM reads it with `getattr`, so the setting is absent unless a portal sets it.
- **What it does**: How long, in seconds, a claim link works. An older token is refused with "Claim token has expired."
- **Accepts**: A number of seconds. See [Profile claiming](profile-claiming.md).

### `CLAIM_TOKEN_SALT`

- **Type**: `str`
- **Default**: `"fairdm.contributor.claim"`. FairDM reads it with `getattr`, so the setting is absent unless a portal sets it.
- **What it does**: The salt that signs claim tokens. A different salt makes every token issued under the old one invalid.
- **Accepts**: Any string. Changing it in production invalidates the claim links already sent.

### `FAIRDM_PROFILE_FORMS`

- **Type**: `dict[str, str]`
- **Default**: `{"person": "fairdm.contrib.contributors.forms.profile.PersonProfileForm", "organization": "fairdm.contrib.contributors.forms.profile.OrganizationProfileForm"}`
- **What it does**: The form each kind of profile is edited with.
- **Accepts**: A dictionary with the keys `person` and `organization`, each a dotted path to a form class. A kind left out keeps the shipped form. See [How to customise the profile form](../how-to/customise-the-profile-form.md).

## Records and content

### `ALLOWED_HTML_ATTRIBUTES`

- **Type**: `list`
- **Default**: `[]`
- **What it does**: FairDM defines it. FairDM's markdown rendering does not read it and sanitises with the default rules of nh3. See [How markdown is sanitised](../explanation/how-markdown-is-sanitised.md).
- **Accepts**: A list, with no effect on FairDM's rendering.

### `ALLOWED_HTML_TAGS`

- **Type**: `list[str]`
- **Default**: A list of tags: `abbr`, `b`, `blockquote`, `br`, `dd`, `dl`, `dt`, `em`, `hr`, `i`, `li`, `ol`, `p`, `pre`, `small`, `span`, `strong`, `sub`, `sup`, `table`, `tbody`, `td`, `tfoot`, `th`, `thead`, `tr`, `u` and `ul`.
- **What it does**: FairDM defines it. FairDM's markdown rendering does not read it.
- **Accepts**: A list, with no effect on FairDM's rendering.

### `ALLOWED_URL_SCHEMES`

- **Type**: `list[str]`
- **Default**: `["https"]`
- **What it does**: FairDM defines it. FairDM's markdown rendering does not read it.
- **Accepts**: A list, with no effect on FairDM's rendering.

### `EXPORT_FORMATS`

- **Type**: `list[type]`
- **Default**: Not set by FairDM. Read as the value of `IMPORT_EXPORT_FORMATS` when absent.
- **What it does**: The formats the export pages offer. Only formats that can export are offered.
- **Accepts**: A list of django-import-export format classes. FairDM reads it when `fairdm.contrib.import_export.utils` is first imported.

### `FAIRDM_ALLOWED_IDENTIFIERS`

- **Type**: `dict[str, dict[str, str]]`
- **Default**: Schemes grouped by model: for `samples.Sample`, `IGSN`; for `contributors.Person`, `ORCID`; for `contributors.Organization`, `ROR`, `GRID`, `Wikidata`, `ISNI` and `Crossref Funder ID`. Each maps the scheme name to its base address, such as `"ROR": "https://ror.org/"`.
- **What it does**: The identifier schemes FairDM offers. FairDM combines the inner dictionaries of every model into one list of schemes and does not read the outer keys.
- **Accepts**: The same shape. Add a scheme by assigning an item to the inner dictionary of a model, such as `FAIRDM_ALLOWED_IDENTIFIERS["samples.Sample"]["IGSN"]`. FairDM reads the setting when `fairdm.utils.choices` is first imported, so set it before then and not in an app that loads later.

### `FAIRDM_DATASET`

- **Type**: `dict`
- **Default**: `{"keyword_vocabularies": []}`
- **What it does**: FairDM defines it and no FairDM code reads it, so changing it has no effect.
- **Accepts**: A dictionary, with no effect.

### `FAIRDM_DEFAULT_LICENSE`

- **Type**: `str`
- **Default**: `"CC BY 4.0"`
- **What it does**: The name of the licence a new dataset starts with, and the licence FairDM's dataset factory uses. FairDM reads it when a form or factory needs it, so a change applies at once.
- **Accepts**: The `name` of a `License` row. `python manage.py seed_licenses` creates `CC0 1.0`, `CC BY 4.0` and `CC BY-SA 4.0`. If no licence has the name, a new dataset starts with none.

### `FAIRDM_FACTORIES`

- **Type**: `dict[str, str]`
- **Default**: Not set. The demo portal sets `{}`. Read as `{}` when absent.
- **What it does**: The factories that `python manage.py generate_fake_data` uses to create samples and measurements of your own types. Without entries the command skips samples and measurements.
- **Accepts**: A dictionary of the model label to the dotted path of its factory, such as `{"myapp.RockSample": "myapp.factories.RockSampleFactory"}`. See [Management commands](management-commands.md).

### `FAIRDM_MARKDOWN_EXTENSIONS`

- **Type**: `list[str]`
- **Default**: `["markdown.extensions.extra", "markdown.extensions.nl2br", "markdown.extensions.smarty", "markdown.extensions.sane_lists", "pymdownx.magiclink", "pymdownx.tilde"]`
- **What it does**: The Python-Markdown extensions applied when markdown is rendered. The `safe_markdown` filter and the editor's live preview both read it, so a change applies to both. Adding an extension does not widen what the sanitiser keeps.
- **Accepts**: A list of Python-Markdown extension names. Extend it with `FAIRDM_MARKDOWN_EXTENSIONS = [*FAIRDM_MARKDOWN_EXTENSIONS, "pymdownx.tasklist"]`. See [How to render markdown in a template](../how-to/render-markdown-in-a-template.md).

### `FAIRDM_PROJECT`

- **Type**: `dict`
- **Default**: `{"keywords": ["fairdm.core.vocabularies.FairDMRoles"]}`
- **What it does**: The `keywords` key lists the vocabularies that get a keyword filter on the project list. Each becomes a filter named `keywords_<ClassName>`. Without any, the list offers one generic `keywords` filter across all vocabularies.
- **Accepts**: A dictionary with a `keywords` list of dotted paths, each to a `research_vocabs` vocabulary class. Keep the setting defined, because FairDM reads it without a fallback. See [How to filter projects by vocabulary keywords](../how-to/filter-projects-by-vocabulary-keywords.md).

### `IMPORT_EXPORT_FORMATS`

- **Type**: `list[type]`
- **Default**: FairDM's `LaTex` format followed by django-import-export's default formats
- **What it does**: The formats FairDM offers for import and export, unless `IMPORT_FORMATS` or `EXPORT_FORMATS` narrows them.
- **Accepts**: A list of django-import-export format classes.

### `IMPORT_FORMATS`

- **Type**: `list[type]`
- **Default**: CSV, TSV, XLS, XLSX and ODS
- **What it does**: The formats FairDM accepts for import. Only formats that can import are offered.
- **Accepts**: A list of django-import-export format classes.

### `MARKDOWNX_MARKDOWNIFY_FUNCTION`

- **Type**: `str`
- **Default**: `"fairdm.utils.markdown.markdownify"`
- **What it does**: The function django-markdownx uses to render the editor's preview. It is the same function the `safe_markdown` filter uses, so the preview matches the page.
- **Accepts**: The dotted path of a function that takes markdown and returns HTML. Keep the default so preview and page agree.

## REST API

### `CORS_ALLOW_ALL_ORIGINS`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Lets a page on any website call the API. Credentials stay off, so a browser never sends the portal's sign-in cookie from another site, and a caller must send a token.
- **Accepts**: `True` or `False`. Set it to `False` with `CORS_ALLOWED_ORIGINS` to answer only some sites. See [How to allow only some sites to call the API](../how-to/allow-only-some-sites-to-call-the-api.md).

### `CORS_ALLOWED_ORIGINS`

- **Type**: `list[str]`
- **Default**: `[]`
- **What it does**: The origins that may call the API when `CORS_ALLOW_ALL_ORIGINS` is `False`.
- **Accepts**: A list of origins with a scheme, such as `"https://app.example.org"`.

### `CORS_URLS_REGEX`

- **Type**: `str`
- **Default**: `r"^/api/.*$"`
- **What it does**: The addresses that django-cors-headers answers cross-origin requests for. Only the API is covered.
- **Accepts**: A regular expression matched against the request path.

### `DEFAULT_THROTTLE_RATES`

A key of [`REST_FRAMEWORK`](#rest_framework).

- **Type**: `dict[str, str or None]`
- **Default**: The API scopes `anon_burst` at `"30/minute"`, `anon_day` at `"2000/day"`, `user_burst` at `"120/minute"` and `user_day` at `"20000/day"`. The four search-box scopes are not in the dictionary. When a scope is missing, the search boxes use `autocomplete_anon_burst` at `"60/minute"`, `autocomplete_anon_day` at `"5000/day"`, `autocomplete_user_burst` at `"240/minute"` and `autocomplete_user_day` at `"50000/day"`.
- **What it does**: How often a caller may use the API. Each kind of caller has a burst limit over a minute and a limit over a day. The search boxes have limits of their own so typing into one does not use an API allowance. [How API callers are limited](../explanation/how-api-callers-are-limited.md) explains the design.
- **Accepts**: For each scope, a string of a number, a slash and `second`, `minute`, `hour` or `day`, or `None` for no limit. Change entries and do not replace the dictionary, because the four API scopes must stay. See [How to change the API rate limits](../how-to/change-the-api-rate-limits.md).

### `FAIRDM_API_DESCRIPTION`

- **Type**: `str`
- **Default**: A Markdown description of the API's resources, filtering and ordering
- **What it does**: The default that `SPECTACULAR_SETTINGS["DESCRIPTION"]` is built from, once, when FairDM loads its API settings.
- **Accepts**: Assigning it after `fairdm.setup()` has no effect. Assign `SPECTACULAR_SETTINGS["DESCRIPTION"]` instead.

### `FAIRDM_API_MAX_PAGE_SIZE`

- **Type**: `int`
- **Default**: `1000`
- **What it does**: The most records a caller may ask for in one page with `?page_size=`. `FairDMPagination` reads it when it answers a request, so a change applies at once.
- **Accepts**: A whole number. See [PAGE_SIZE](#page_size).

### `FAIRDM_API_TITLE`

- **Type**: `str`
- **Default**: `"FairDM Portal API"`
- **What it does**: The default that `SPECTACULAR_SETTINGS["TITLE"]` is built from, once, when FairDM loads its API settings.
- **Accepts**: Assigning it after `fairdm.setup()` has no effect. Assign `SPECTACULAR_SETTINGS["TITLE"]` instead.

### `MVP_ACCOUNTS_API_TOKEN_ACCESS`

- **Type**: `str` or `None`
- **Default**: Not set, which lets every signed-in person hold API tokens.
- **What it does**: Names a function that decides who may see and use the API tokens pages. The function takes the signed-in user and returns whether they may. A visitor who is not signed in may never use them, and the function is not asked.
- **Accepts**: A dotted import path to a function, such as `"myportal.access.may_hold_tokens"`, or `None`. A path that does not import raises `ImportError`. See [How to restrict API tokens to some people](../how-to/restrict-api-tokens-to-some-people.md).

### `NUM_PROXIES`

A key of [`REST_FRAMEWORK`](#rest_framework).

- **Type**: `int` or `None`
- **Default**: Not set. `check --deploy` reports `fairdm.W601` while the key is absent.
- **What it does**: How many proxies stand between a visitor and the portal. The API and the search boxes use it to read the caller's address from `X-Forwarded-For`, so their limits count the right caller.
- **Accepts**: The exact number of proxies, `0` for none, or `None`. Any value you set ends the warning. See [How to count API callers behind a proxy](../how-to/count-api-callers-behind-a-proxy.md).

### `PAGE_SIZE`

A key of [`REST_FRAMEWORK`](#rest_framework).

- **Type**: `int`
- **Default**: `100`
- **What it does**: How many records a list holds when the caller does not ask for another number. `FairDMPagination` reads it when it answers a request.
- **Accepts**: A whole number that is no larger than `FAIRDM_API_MAX_PAGE_SIZE`.

### `REST_FRAMEWORK`

- **Type**: `dict`
- **Default**: FairDM sets these keys.

| Key | Default |
| --- | --- |
| `DEFAULT_AUTHENTICATION_CLASSES` | `knox.auth.TokenAuthentication`, then `rest_framework.authentication.SessionAuthentication` |
| `DEFAULT_PERMISSION_CLASSES` | `fairdm.api.permissions.FairDMObjectPermissions` |
| `DEFAULT_RENDERER_CLASSES` | The orjson JSON renderer, then the browsable API renderer |
| `DEFAULT_PARSER_CLASSES` | The orjson parser, the form parser and the multipart parser |
| `DEFAULT_SCHEMA_CLASS` | `drf_spectacular.openapi.AutoSchema` |
| `DEFAULT_PAGINATION_CLASS` | `fairdm.api.pagination.FairDMPagination` |
| `PAGE_SIZE` | `100` |
| `DEFAULT_THROTTLE_CLASSES` | `fairdm.api.throttling.AnonBurstThrottle`, `AnonDailyThrottle`, `UserBurstThrottle` and `UserDailyThrottle` |
| `DEFAULT_THROTTLE_RATES` | See [DEFAULT_THROTTLE_RATES](#default_throttle_rates) |
| `DEFAULT_FILTER_BACKENDS` | `fairdm.api.filters.FairDMVisibilityFilter`, `fairdm.api.filters.FairDMFilterBackend` and `rest_framework.filters.OrderingFilter` |

- **What it does**: The Django REST framework configuration for the API. Token authentication comes first because the framework answers with 403 instead of 401 when the first authenticator is session authentication.
- **Accepts**: Django REST framework's format. Assign items and do not replace the dictionary. FairDM's classes are the ones that enforce record visibility, limits and paging, so keep them.

### `REST_KNOX`

- **Type**: `dict`
- **Default**: `{"TOKEN_LIMIT_PER_USER": 10, "AUTO_REFRESH": False}`
- **What it does**: The settings of django-rest-knox, which stores the tokens people create on their account pages. `TOKEN_LIMIT_PER_USER` is how many working tokens a person may hold, and at the limit the create page makes none and says so. `AUTO_REFRESH` is off so a token expires on the day the person chose, however often it is used.
- **Accepts**: django-rest-knox's format. Assign items, such as `REST_KNOX["TOKEN_LIMIT_PER_USER"] = 5`.

### `SPECTACULAR_SETTINGS`

- **Type**: `dict`
- **Default**: `TITLE` from `FAIRDM_API_TITLE`, `DESCRIPTION` from `FAIRDM_API_DESCRIPTION`, `VERSION` `"1.0.0"`, `SERVE_INCLUDE_SCHEMA` `False`, `SWAGGER_UI_DIST` and `SWAGGER_UI_FAVICON_HREF` `"SIDECAR"`, `SCHEMA_PATH_PREFIX` `r"/api/v[0-9]+"`, `SORT_OPERATIONS` `False`, and `POSTPROCESSING_HOOKS` holding `drf_spectacular.hooks.postprocess_schema_enums` and `fairdm.api.schema.describe_api`.
- **What it does**: Configures the OpenAPI schema and the interactive documentation. The bundled Swagger assets let the documentation work without internet access. The `describe_api` hook writes the portal's authentication, limits and paging into the description from the live settings.
- **Accepts**: drf-spectacular's format. Assign items, such as `SPECTACULAR_SETTINGS["TITLE"] = "My Portal API"`, and never a new dictionary, which drops the Swagger assets, the path prefix and the `describe_api` hook. See [How to customise the API documentation](../how-to/customise-the-api-documentation.md).

## Legal documents

django-mvp-compliance reads these settings. FairDM sets one of them. [Legal documents](legal-documents.md) describes the pages, and [Who is asked to agree to a legal document](../../explanation/who-is-asked-to-agree-to-a-legal-document.md) explains the rules.

### `MVP_COMPLIANCE_AGREEMENT_CHECK_INTERVAL`

- **Type**: `int` or `float`
- **Default**: Not set by FairDM. The package uses `60`.
- **What it does**: For how many seconds a finding that nothing is outstanding for a person is remembered in their session, so the check does not run on every request.
- **Accepts**: A number of seconds. `0` checks on every request. A value that is not a number is reported as `mvp_compliance.E004`.

### `MVP_COMPLIANCE_AGREEMENT_EXEMPT_URLS`

- **Type**: `list[str]`
- **Default**: `["/hijack/"]`
- **What it does**: Addresses that a person who has not agreed to a required document can still reach. FairDM exempts `/hijack/` so an administrator acting as that person can go back to their own account. Each entry covers its path and everything beneath it.
- **Accepts**: A list of paths. A string is rejected as `mvp_compliance.E003`. Add to the list and do not replace it, such as `MVP_COMPLIANCE_AGREEMENT_EXEMPT_URLS += ["/help/"]`.

### `MVP_COMPLIANCE_AGREEMENT_EXEMPT_USERS`

- **Type**: `list[str]`
- **Default**: Not set by FairDM. The package uses `[]`.
- **What it does**: User names that are never asked to agree.
- **Accepts**: A list of user names. A string is rejected as `mvp_compliance.E003`.

### `MVP_COMPLIANCE_AGREEMENT_REDIRECT_URL`

- **Type**: `str`
- **Default**: Not set by FairDM. The package uses `"/"`.
- **What it does**: Where a person goes after agreeing, when they were not on their way to another page.
- **Accepts**: A path or a URL.

### `MVP_COMPLIANCE_RECORD_IP_ADDRESS`

- **Type**: `bool`
- **Default**: Not set by FairDM. The package uses `False`.
- **What it does**: Records the network address a person agreed from. It is off because the address is personal data.
- **Accepts**: `True` or `False`.

## Logging and monitoring

### `LOGGING`

- **Type**: `dict`
- **Default**: Production: the root logger writes `INFO` and above to the console. `django.request` errors and `django.security.DisallowedHost` go to the site administrators by email when `DEBUG` is off. Development: replaces the whole dictionary with console logging, where the `fairdm` logger is at `DEBUG`, `django` at `INFO` and `django.db.backends` at `WARNING`, and no email.
- **What it does**: Django's logging configuration.
- **Accepts**: Django's format. Add a logger by assigning an item, such as `LOGGING["loggers"]["my_app"] = {"handlers": ["console"], "level": "INFO"}`.

### `ORBIT_CONFIG`

- **Type**: `dict`
- **Default**: `{"AUTH_CHECK": "fairdm.conf.orbit.dashboard_access"}`
- **What it does**: Configures the Orbit dashboard at `/orbit/`, which records requests, queries and exceptions. FairDM's check opens the dashboard when `DEBUG` is on and otherwise allows only signed-in superusers.
- **Accepts**: django-orbit's format. Change who may view the dashboard by assigning another function to `AUTH_CHECK`.

### `SENTRY_DSN`

- **Type**: `str`
- **Default**: `""`, from the variable of that name
- **What it does**: The Sentry project address. When it is set, FairDM starts the Sentry SDK with the Django, Celery, Redis and logging integrations as `fairdm.setup()` runs. When it is empty, Sentry stays off.
- **Accepts**: A DSN. Set the variable. Assigning the setting after `fairdm.setup()` does not start Sentry.

### `SENTRY_LOG_LEVEL`

- **Type**: `int`
- **Default**: `20` (`logging.INFO`), from `DJANGO_SENTRY_LOG_LEVEL`
- **What it does**: The lowest log level the Sentry logging integration records as a breadcrumb. Records at `ERROR` and above become events.
- **Accepts**: A Python logging level number. Set the variable, because `fairdm.setup()` reads it once.

## Settings for other packages

These settings configure packages that FairDM installs. A portal rarely changes them.

### `ACTSTREAM_SETTINGS`

- **Type**: `dict`
- **Default**: `{"USE_JSONFIELD": True}`
- **What it does**: FairDM defines it. No installed app reads it.
- **Accepts**: A dictionary, with no effect.

### `GET_SOLO_TEMPLATE_TAG_NAME`

- **Type**: `str`
- **Default**: `"site_config"`
- **What it does**: The name of the template tag that django-solo provides for reading single-row models such as the portal identity.
- **Accepts**: A tag name.

### `META_SITE_PROTOCOL`

- **Type**: `str`
- **Default**: `"https"`
- **What it does**: The scheme django-meta writes into the page's meta tags.
- **Accepts**: `"https"` or `"http"`.

### `META_USE_OG_PROPERTIES`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Writes Open Graph properties into the page's meta tags.
- **Accepts**: `True` or `False`.

### `META_USE_SITES`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Builds meta tag addresses from the sites framework.
- **Accepts**: `True` or `False`.

### `META_USE_TITLE_TAG`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Writes the page title into the meta tags.
- **Accepts**: `True` or `False`.

### `META_USE_TWITTER_PROPERTIES`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Writes Twitter card properties into the page's meta tags.
- **Accepts**: `True` or `False`.

### `SOLO_CACHE`

- **Type**: `str`
- **Default**: `"default"`
- **What it does**: The cache alias django-solo stores single-row models in.
- **Accepts**: A key of `CACHES`.

### `SOLO_CACHE_TIMEOUT`

- **Type**: `int`
- **Default**: `300`
- **What it does**: Seconds django-solo keeps a single-row model in the cache.
- **Accepts**: A number of seconds.

### `WAFFLE_CREATE_MISSING_FLAGS`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Makes django-waffle create a flag in the database the first time code asks for one that does not exist.
- **Accepts**: `True` or `False`.

### `WAFFLE_CREATE_MISSING_SAMPELS`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: FairDM defines it under this spelling. django-waffle reads `WAFFLE_CREATE_MISSING_SAMPLES`, with an E, so this setting has no effect.
- **Accepts**: `True` or `False`, with no effect.

### `WAFFLE_CREATE_MISSING_SWITCHES`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Makes django-waffle create a switch in the database the first time code asks for one that does not exist.
- **Accepts**: `True` or `False`.

## Environment variables

`fairdm.setup()` reads these variables through django-environ. A variable can be set in the process environment, in `stack.env`, in `stack.<environment>.env` or in the file named by `env_file`, in the order [Configuration](configuration.md#environment-files) gives. The [container images](container-images.md) set or read a few more variables of their own.

Three kinds of variable have no entry here. `DJANGO_ENV` and `SENTRY_DSN` are described above, because the variable and the setting share a name. The email variables `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_HOST_PASSWORD`, `EMAIL_HOST_USER`, `EMAIL_PORT` and `EMAIL_USE_TLS` are described under the [Email](#email) setting of the same name. `GDAL_LIBRARY_PATH` and `GEOS_LIBRARY_PATH` are described under [Database](#database) in the same way.

### `BACKUP_DIR`

- **Type**: `str`
- **Default**: `""`, which keeps backups in `BASE_DIR / "backups"`. The [container images](container-images.md) set it to `/var/lib/fairdm/backups`.
- **What it does**: The directory the local `dbbackup` storage in [`STORAGES`](#storages) writes backups to.
- **Accepts**: A directory path the portal can write to.

### `BACKUP_KEEP`

- **Type**: `int`
- **Default**: `4`
- **What it does**: Sets [`DBBACKUP_CLEANUP_KEEP`](#dbbackup_cleanup_keep) and [`DBBACKUP_CLEANUP_KEEP_MEDIA`](#dbbackup_cleanup_keep_media), the number of database backups and the number of media backups kept.
- **Accepts**: A whole number.

### `BACKUP_SERVER_NAME`

- **Type**: `str`
- **Default**: `"fairdm"`
- **What it does**: Sets [`DBBACKUP_HOSTNAME`](#dbbackup_hostname), the server name in the file name of a backup.
- **Accepts**: A name without spaces.

### `CONN_MAX_AGE`

- **Type**: `int`
- **Default**: `60`
- **What it does**: Sets `DATABASES["default"]["CONN_MAX_AGE"]`, the seconds a database connection stays open.
- **Accepts**: A number of seconds.

### `DATABASE_URL`

- **Type**: `str`
- **Default**: `""`. When it is empty, the `POSTGRES_*` variables form the connection.
- **What it does**: The database connection for [`DATABASES`](#databases).
- **Accepts**: A connection URL such as `"postgresql://user:password@host:5432/name"`. FairDM opens it with the PostGIS backend whatever the scheme says.

### `DJANGO_ADMIN_URL`

- **Type**: `str`
- **Default**: `"admin/"`
- **What it does**: Sets [`ADMIN_URL`](#admin_url).
- **Accepts**: A route that ends in a slash.

### `DJANGO_ALLOWED_HOSTS`

- **Type**: `list[str]`
- **Default**: `[]`
- **What it does**: Adds hosts to [`ALLOWED_HOSTS`](#allowed_hosts) beside `DJANGO_SITE_DOMAIN`.
- **Accepts**: A comma-separated list of host names.

### `DJANGO_DEBUG`

- **Type**: `bool`
- **Default**: `False`
- **What it does**: Sets [`DEBUG`](#debug) in production. The development override sets `DEBUG` on whatever the variable says.
- **Accepts**: `True` or `False`.

### `DJANGO_DEFAULT_FROM_EMAIL`

- **Type**: `str`
- **Default**: Unset, so the address is `noreply@<DJANGO_SITE_DOMAIN>`
- **What it does**: The address part of [`DEFAULT_FROM_EMAIL`](#default_from_email). The site name stays in front of it.
- **Accepts**: An email address.

### `DJANGO_ROOT_URLCONF`

- **Type**: `str`
- **Default**: `"config.urls"`
- **What it does**: Sets [`ROOT_URLCONF`](#root_urlconf).
- **Accepts**: A dotted module path.

### `DJANGO_SECRET_KEY`

- **Type**: `str`
- **Default**: `""`. Development uses an insecure fallback when it is unset.
- **What it does**: Sets [`SECRET_KEY`](#secret_key).
- **Accepts**: A private random string of 50 characters or more.

### `DJANGO_SECURE_CONTENT_TYPE_NOSNIFF`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Sets [`SECURE_CONTENT_TYPE_NOSNIFF`](#secure_content_type_nosniff).
- **Accepts**: `True` or `False`.

### `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Sets [`SECURE_HSTS_INCLUDE_SUBDOMAINS`](#secure_hsts_include_subdomains) in production.
- **Accepts**: `True` or `False`.

### `DJANGO_SECURE_HSTS_PRELOAD`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Sets [`SECURE_HSTS_PRELOAD`](#secure_hsts_preload) in production.
- **Accepts**: `True` or `False`.

### `DJANGO_SECURE_SSL_REDIRECT`

- **Type**: `bool`
- **Default**: `True`
- **What it does**: Sets [`SECURE_SSL_REDIRECT`](#secure_ssl_redirect) in production.
- **Accepts**: `True` or `False`.

### `DJANGO_SENTRY_LOG_LEVEL`

- **Type**: `int`
- **Default**: `20`
- **What it does**: Sets [`SENTRY_LOG_LEVEL`](#sentry_log_level).
- **Accepts**: A Python logging level number.

### `DJANGO_SERVER_EMAIL`

- **Type**: `str`
- **Default**: Unset, so the address is `server@<DJANGO_SITE_DOMAIN>`
- **What it does**: The address part of [`SERVER_EMAIL`](#server_email).
- **Accepts**: An email address.

### `DJANGO_SITE_DOMAIN`

- **Type**: `str`
- **Default**: `""`
- **What it does**: Sets [`SITE_DOMAIN`](#site_domain).
- **Accepts**: A host name.

### `DJANGO_SITE_ID`

- **Type**: `int`
- **Default**: `1`
- **What it does**: Sets [`SITE_ID`](#site_id).
- **Accepts**: A whole number.

### `DJANGO_SITE_NAME`

- **Type**: `str`
- **Default**: `"FairDM Demo"`
- **What it does**: Sets [`SITE_NAME`](#site_name).
- **Accepts**: Any string.

### `DJANGO_SUPERUSER_EMAIL`

- **Type**: `str`
- **Default**: `"super.user@example.com"`
- **What it does**: The email address of the first administrator account, and the address in [`ADMINS`](#admins).
- **Accepts**: An email address.

### `DJANGO_SUPERUSER_FIRSTNAME`

- **Type**: `str`
- **Default**: `"Super"`
- **What it does**: The first name given to the administrator account that [`DJANGO_SETUP_TOOLS`](#django_setup_tools) creates.
- **Accepts**: Any string.

### `DJANGO_SUPERUSER_LASTNAME`

- **Type**: `str`
- **Default**: `"User"`
- **What it does**: The last name given to the administrator account that [`DJANGO_SETUP_TOOLS`](#django_setup_tools) creates.
- **Accepts**: Any string.

### `DJANGO_SUPERUSER_PASSWORD`

- **Type**: `str`
- **Default**: `""`. FairDM ships no working password.
- **What it does**: The password that Django's `createsuperuser --no-input` reads for the administrator account.
- **Accepts**: A password. Keep it out of the repository.

### `DJANGO_TIME_ZONE`

- **Type**: `str`
- **Default**: `"UTC"`
- **What it does**: Sets [`TIME_ZONE`](#time_zone) and [`CELERY_TIMEZONE`](#celery_timezone).
- **Accepts**: A name from the IANA time zone database.

### `ORCID_BASE_DOMAIN`

- **Type**: `str`
- **Default**: `"orcid.org"`
- **What it does**: The ORCID domain that sign-in with ORCID uses, in [`SOCIALACCOUNT_PROVIDERS`](#socialaccount_providers).
- **Accepts**: `"orcid.org"` for the live service or `"sandbox.orcid.org"` for ORCID's sandbox.

### `POSTGRES_DB`

- **Type**: `str`
- **Default**: `""`
- **What it does**: The database name, used when `DATABASE_URL` is empty.
- **Accepts**: A database name.

### `POSTGRES_HOST`

- **Type**: `str`
- **Default**: `"postgres"`
- **What it does**: The database host, used when `DATABASE_URL` is empty.
- **Accepts**: A host name.

### `POSTGRES_PASSWORD`

- **Type**: `str`
- **Default**: `""`
- **What it does**: The database password, used when `DATABASE_URL` is empty. FairDM quotes it, so special characters are safe.
- **Accepts**: A password.

### `POSTGRES_PORT`

- **Type**: `int`
- **Default**: `5432`
- **What it does**: The database port, used when `DATABASE_URL` is empty.
- **Accepts**: A port number.

### `POSTGRES_USER`

- **Type**: `str`
- **Default**: `"postgres"`
- **What it does**: The database user, used when `DATABASE_URL` is empty.
- **Accepts**: A user name.

### `REDIS_URL`

- **Type**: `str`
- **Default**: `""`
- **What it does**: The Redis server for both caches in [`CACHES`](#caches) and for [`CELERY_BROKER_URL`](#celery_broker_url). In production it must be set. In development, leaving it unset holds every cache in memory and runs tasks in the calling process.
- **Accepts**: A Redis URL such as `"redis://redis:6379/0"`.

### `S3_ACCESS_KEY_ID`

- **Type**: `str`
- **Default**: `""`
- **What it does**: Sets [`AWS_ACCESS_KEY_ID`](#aws_access_key_id). Media storage moves to S3 when this, `S3_SECRET_ACCESS_KEY` and `S3_BUCKET_NAME` are all set.
- **Accepts**: An access key.

### `S3_BUCKET_NAME`

- **Type**: `str`
- **Default**: `""`
- **What it does**: Sets [`AWS_STORAGE_BUCKET_NAME`](#aws_storage_bucket_name).
- **Accepts**: A bucket name.

### `S3_REGION_NAME`

- **Type**: `str`
- **Default**: `""`
- **What it does**: Sets [`AWS_S3_REGION_NAME`](#aws_s3_region_name).
- **Accepts**: A region name.

### `S3_SECRET_ACCESS_KEY`

- **Type**: `str`
- **Default**: `""`
- **What it does**: Sets [`AWS_SECRET_ACCESS_KEY`](#aws_secret_access_key).
- **Accepts**: A secret key.

### `SENTRY_ENVIRONMENT`

- **Type**: `str`
- **Default**: `"production"`
- **What it does**: The environment name Sentry files events under. It applies only when [`SENTRY_DSN`](#sentry_dsn) is set.
- **Accepts**: Any string.

### `SENTRY_TRACES_SAMPLE_RATE`

- **Type**: `float`
- **Default**: `0.0`
- **What it does**: The share of requests Sentry traces. It applies only when [`SENTRY_DSN`](#sentry_dsn) is set.
- **Accepts**: A number from `0.0` to `1.0`.

### Variables FairDM declares and does not read

FairDM declares these variables when it builds the environment reader, and no setting is built from them. Setting them changes nothing.

- `DJANGO_CACHE`
- `DJANGO_READ_DOT_ENV_FILE`
- `DJANGO_SECURE`
- `DJANGO_SECURE_HSTS_SECONDS`
- `FAIRDM_ALLOW_PUBLIC_REGISTRATION`
- `USE_DOCKER`
