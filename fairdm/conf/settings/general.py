import socket

from django.contrib.messages import constants as messages

env = globals()["env"]

# GIS_ENABLED = False

# with suppress(ImproperlyConfigured):
#     import django.contrib.gis.db.models

#     GIS_ENABLED = True


FAIRDM = globals().get("FAIRDM", {})

ADMIN_URL = f"{env('DJANGO_ADMIN_URL')}"
ADMINS = [("Super User", env("DJANGO_SUPERUSER_EMAIL"))]
# ADMINS = [(admin["name"], admin["email"]) for admin in FAIRDM["application"]["developers"]]
ALLOWED_HOSTS = [env("DJANGO_SITE_DOMAIN")] + env("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = [f"https://{domain}" for domain in globals().get("ALLOWED_HOSTS", [])]
MANAGERS = ADMINS
ROOT_URLCONF = env("DJANGO_ROOT_URLCONF")
SECRET_KEY = env("DJANGO_SECRET_KEY")
SITE_DOMAIN = env("DJANGO_SITE_DOMAIN")
SITE_ID = env("DJANGO_SITE_ID")
SITE_NAME = META_SITE_NAME = env("DJANGO_SITE_NAME")
TIME_ZONE = env("DJANGO_TIME_ZONE", default="UTC")
USE_TZ = True
WSGI_APPLICATION = None

# Coloured Messages
MESSAGE_TAGS = {
    messages.DEBUG: "debug alert-secondary",
    messages.INFO: "info alert-info",
    messages.SUCCESS: "success alert-success",
    messages.WARNING: "warning alert-warning",
    messages.ERROR: "error alert-danger",
}


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
                "sekizai.context_processors.sekizai",
                "django.template.context_processors.static",
                "fairdm.utils.context_processors.fairdm",
            ],
            "builtins": [
                "django.templatetags.i18n",
                "easy_icons.templatetags.easy_icons",
            ],
        },
    },
]


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
]


# for django debug toolbar
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]


# Direct Django to the following directories to search for project fixtures,
# staticfiles and locales
# --------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(BASE_DIR / "fixtures"),)


# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(BASE_DIR / "project" / "locale")]


# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap5-responsive.html"
DJANGO_TABLES2_TEMPLATE = "fairdm/table.html"

ACCOUNT_MANAGEMENT_GET_AVATAR_URL = "fairdm.contrib.contributors.utils.get_contributor_avatar"  # This line connects the avatar_url template tag to the function that retrieves the contributor's avatar URL.

# DEPLOYMENT_PIPELINE = {}
DJANGO_SETUP_TOOLS = {
    # "default": {},
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
            # ("loaddata", "creativecommons"),
            ("loaddata", "django-waffle"),
            ("loaddata", "groups"),
        ],
        "always_run": [
            ("migrate", "--no-input"),
            ("collectstatic", "--noinput"),
            ("preload",),  # used to preload vocabulary concepts (django-research-vocabs)
            "django_setup_tools.scripts.sync_site_id",
        ],
    },
    "development": {
        "merge": True,  # merge with the default commands
        "on_initial": [
            ("loaddata", "myapp"),
        ],
        "always_run": [
            "django_setup_tools.scripts.some_extra_func",
        ],
    },
    "production": {
        "merge": True,  # merge with the default commands
        "always_run": [
            ("compress",),
        ],
    },
}


SHELL_PLUS_MODEL_ALIASES = {
    "waffle": {"Sample": "waffle_sample"},
}
