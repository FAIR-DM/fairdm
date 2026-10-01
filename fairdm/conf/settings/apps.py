"""Application stack settings: INSTALLED_APPS, MIDDLEWARE, TEMPLATES and core Django settings.

Owns INSTALLED_APPS, MIDDLEWARE, TEMPLATES and core Django settings such as ROOT_URLCONF,
SITE_ID and TIME_ZONE. A portal's ``apps=[...]`` are registered ahead of FairDM's own apps
and the third-party set, so its templates and static files win at the same path. They stay
behind the Django contrib apps, which must load first. A portal adds its own middleware and
template context processors after ``setup()`` returns.
"""

import socket

from fairdm.conf.environment import env

BASE_DIR = globals()["BASE_DIR"]

# Order matters: the admin apps must come early.
INSTALLED_APPS = [
    "adminactions",
    "admin_extra_buttons",
    "fairdm.contrib.admin.apps.FairDMAdminConfig",
    "dal",
    "dal_select2",
    "fairdm.contrib.admin.apps.FairDMAdminSite",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "django.contrib.messages",
    "django.contrib.humanize",
    "django_cleanup.apps.CleanupConfig",
    # Ahead of FairDM's own apps so a portal's template or static file at the same path wins.
    *globals().get("FAIRDM_APPS", []),
    "fairdm",
    "fairdm.contrib.plugins",
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
    "fairdm.utils",
    "fairdm.contrib.identity",
    "fairdm.contrib.theme",
    "mvp",
    "mvp_charts",
    "polymorphic",
    "parler",
    "dac",
    "dac.allauth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.orcid",
    "allauth.mfa",
    "allauth.usersessions",
    "compressor",
    "dbbackup",
    "django_celery_beat",
    "django_cotton",
    "django_extensions",
    "django_setup_tools",
    "django_tables2",
    "easy_icons",
    "easy_thumbnails",
    "flex_menu",
    "meta",
    "solo",
    "django_contact_form",
    "storages",
    "django_filters",
    "crispy_forms",
    "crispy_tailwind",
    "widget_tweaks",
    "django_select2",
    "django_social_share",
    "django_htmx",
    "orbit",
    "literature",
    "licensing",
    "research_vocabs",
    "ordered_model",
    "taggit",
    "import_export",
    "django_addanother",
    "waffle",
    "guardian",
    "django_countries",
    "markdownx",
    "hijack",
    "hijack.contrib.admin",
    "fairdm.api",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "corsheaders",
    "dj_rest_auth",
]

# Order is critical: security and whitenoise must come early.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Wraps the app stack to record requests, queries and exceptions.
    "orbit.middleware.OrbitMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "hijack.middleware.HijackUserMiddleware",
]

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

ROOT_URLCONF = env("DJANGO_ROOT_URLCONF")

# Set by portal projects.
WSGI_APPLICATION = None

SITE_ID = env("DJANGO_SITE_ID")
SITE_DOMAIN = env("DJANGO_SITE_DOMAIN")
SITE_NAME = META_SITE_NAME = env("DJANGO_SITE_NAME")

ADMIN_URL = f"{env('DJANGO_ADMIN_URL')}"
ADMINS = [("Super User", env("DJANGO_SUPERUSER_EMAIL"))]
MANAGERS = ADMINS

TIME_ZONE = env("DJANGO_TIME_ZONE", default="UTC")
USE_TZ = True
LANGUAGE_CODE = "en"
USE_I18N = True
USE_L10N = True

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

FIXTURE_DIRS = (str(BASE_DIR / "fixtures"),)
LOCALE_PATHS = [str(BASE_DIR / "project" / "locale")]

# The gateway address of each local network, for the debug toolbar.
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap5-mvp.html"
ACCOUNT_MANAGEMENT_GET_AVATAR_URL = (
    "fairdm.contrib.contributors.utils.get_contributor_avatar"
)

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
        ],
        "always_run": [
            ("migrate", "--no-input"),
            ("collectstatic", "--noinput"),
            ("preload",),
            ("seed_licenses",),
            "django_setup_tools.scripts.sync_site_id",
        ],
    },
    "production": {
        "merge": True,
        "always_run": [
            ("compress",),
        ],
    },
}
