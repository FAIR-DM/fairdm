"""Application Stack Configuration

This module defines the complete Django application stack including:
- INSTALLED_APPS: All Django apps, third-party packages, and FairDM modules
- MIDDLEWARE: Request/response processing pipeline
- TEMPLATES: Template engine configuration
- Core Django settings: ROOT_URLCONF, SITE_ID, TIME_ZONE, etc.

This is the production baseline. Environment-specific overrides in local.py/staging.py.
"""

import socket

from django.contrib.messages import constants as messages
from fairdm.conf.environment import env

# Access environment variables via shared env instance
# env = globals()["env"]
BASE_DIR = globals()["BASE_DIR"]

# INSTALLED_APPS: Complete application stack
# Order matters for some apps (e.g., admin must come before certain apps)
INSTALLED_APPS = [
    # Admin apps (must come early)
    "adminactions",
    "admin_site_search",
    "admin_extra_buttons",
    "fairdm.contrib.admin.apps.FairDMAdminConfig",
    "dal",
    "dal_select2",
    # DJANGO CORE
    "fairdm.contrib.admin.apps.FairDMAdminSite",
    # "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "django.contrib.messages",
    # "django.contrib.gis",
    "django.contrib.humanize",
    "django_cleanup.apps.CleanupConfig",
    # FAIRDM CORE
    "fairdm.contrib.theme",
    "fairdm",
    "fairdm.core.project",
    "fairdm.core.dataset",
    "fairdm.core.sample",
    "fairdm.core.measurement",
    "fairdm.contrib.autocomplete",
    "fairdm.contrib.generic",
    "fairdm.contrib.collections",
    "fairdm.contrib.contributors",
    "fairdm.contrib.import_export",
    "fairdm.contrib.location",
    "fairdm.contrib.activity_stream",
    "fairdm.utils",
    "fairdm.contrib.identity",
    "actstream",
    # "configuration",
    "polymorphic",
    "parler",
    # AUTHENTICATION AND USERS
    "dac",
    "dac.addons.allauth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.orcid",
    "allauth.mfa",
    "allauth.usersessions",
    "invitations",
    # UTILITIES
    # "django_better_admin_arrayfield",
    "compressor",
    "dbbackup",
    # "django_celery_beat",  # celery based task manager
    "django_cotton",
    "cotton_bs5",
    "django_extensions",
    "django_setup_tools",
    "django_tables2",
    "easy_icons",
    "easy_thumbnails",
    "flex_menu",
    "jsonfield_toolkit",
    "meta",  # for seo optimization
    # OTHERS
    "solo",  # singleton model for storing dynamic global variables in the DB
    "django_contact_form",  # for contact forms
    "storages",  # for setting up backend storages
    # building nice looking forms and filters
    "django_filters",
    "crispy_forms",
    "crispy_bootstrap5",
    "widget_tweaks",
    "django_select2",
    # some other useful apps that are required by the default installation
    "django_social_share",  # easy links to social sharing sites
    "django_htmx",
    "literature",
    "licensing",
    # "laboratory",
    "research_vocabs",
    "ordered_model",
    "taggit",
    "import_export",
    "render_fields",
    "django_addanother",
    "waffle",
    "guardian",  # for object level permissions
    "django_countries",
    "martor",  # markdown editor
    "hijack",
    "hijack.contrib.admin",
    *globals().get("FAIRDM_APPS", []),
]

# MIDDLEWARE: Request/response processing pipeline
# Order is critical - security and whitenoise must come early
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "hijack.middleware.HijackUserMiddleware",
]

# TEMPLATES: Template engine configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.template.context_processors.csrf",
                "django.template.context_processors.tz",
                "django.template.context_processors.static",
                "fairdm.utils.context_processors.fairdm",
                "mvp.context_processors.mvp_config",
            ],
            "builtins": [
                "django.templatetags.i18n",
                "easy_icons.templatetags.easy_icons",
            ],
        },
    },
]

# CORE DJANGO SETTINGS
# These settings are required for Django to function properly

# URL configuration
ROOT_URLCONF = env("DJANGO_ROOT_URLCONF")

# WSGI application (set by portal projects)
WSGI_APPLICATION = None

# Site framework
SITE_ID = env("DJANGO_SITE_ID")
SITE_DOMAIN = env("DJANGO_SITE_DOMAIN")
SITE_NAME = META_SITE_NAME = env("DJANGO_SITE_NAME")

# Admin configuration
ADMIN_URL = f"{env('DJANGO_ADMIN_URL')}"
ADMINS = [("Super User", env("DJANGO_SUPERUSER_EMAIL"))]
MANAGERS = ADMINS

# Internationalization
TIME_ZONE = env("DJANGO_TIME_ZONE", default="UTC")
USE_TZ = True
LANGUAGE_CODE = "en"
USE_I18N = True
USE_L10N = True

# django-parler: Multi-language content
# https://django-parler.readthedocs.io/
PARLER_DEFAULT_LANGUAGE_CODE = "en"
PARLER_LANGUAGES = {
    1: (
        {"code": "en"},
        {"code": "fr"},
        {"code": "de"},
    ),
    "default": {
        "fallback": "en",
        "hide_untranslated": False,
    },
}

# Fixtures, Locales, and Static paths
FIXTURE_DIRS = (str(BASE_DIR / "fixtures"),)
LOCALE_PATHS = [str(BASE_DIR / "project" / "locale")]

# Messages framework - colored message tags for Bootstrap 5
MESSAGE_TAGS = {
    messages.DEBUG: "debug alert-secondary",
    messages.INFO: "info alert-info",
    messages.SUCCESS: "success alert-success",
    messages.WARNING: "warning alert-warning",
    messages.ERROR: "error alert-danger",
}

# Django Debug Toolbar - INTERNAL_IPS configuration
# Gets local network IPs for debug toolbar access
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

# THIRD-PARTY APP CONFIGURATIONS
# Settings specific to installed third-party packages

# django-crispy-forms: Bootstrap 5 form rendering
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# django-tables2: Table rendering template
DJANGO_TABLES2_TEMPLATE = "collections/table.html"

# django-accounts-center: Avatar URL retrieval
ACCOUNT_MANAGEMENT_GET_AVATAR_URL = "fairdm.contrib.contributors.utils.get_contributor_avatar"

# django-setup-tools: Deployment pipeline configuration
DJANGO_SETUP_TOOLS = {
    "": {
        "on_initial": [
            ("makemigrations", "--no-input"),
            ("migrate", "--no-input"),
            (
                "createsuperuser",
                "--no-input",
                "--first_name",
                env("DJANGO_SUPERUSER_FIRSTNAME", default="Super"),
                "--last_name",
                env("DJANGO_SUPERUSER_LASTNAME", default="User"),
            ),
            ("loaddata", "django-waffle"),
            ("loaddata", "groups"),
        ],
        "always_run": [
            ("migrate", "--no-input"),
            ("collectstatic", "--noinput"),
            ("preload",),  # django-research-vocabs
            "django_setup_tools.scripts.sync_site_id",
        ],
    },
    "development": {
        "merge": True,
        "on_initial": [
            ("loaddata", "myapp"),
        ],
        "always_run": [
            "django_setup_tools.scripts.some_extra_func",
        ],
    },
    "production": {
        "merge": True,
        "always_run": [
            ("compress",),
        ],
    },
}
