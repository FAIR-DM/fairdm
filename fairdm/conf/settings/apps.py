INSTALLED_APPS = [
    # Admin apps
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
    # FAIRDM
    "fairdm",
    "fairdm.core.project",
    "fairdm.core.dataset",
    "fairdm.core.sample",
    "fairdm.core.measurement",
    "fairdm.contrib.generic",
    "fairdm.contrib.contributors",
    "fairdm.contrib.import_export",
    "fairdm.contrib.location",
    "fairdm.utils",
    "fairdm.contrib.identity",
    "actstream",
    # "configuration",
    "polymorphic",
    "treebeard",
    "parler",
    # AUTHENTICATION AND USERS
    "dac.themes.bs5",
    "dac",
    "dac.addons.allauth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.orcid",
    "allauth.mfa",
    "allauth.usersessions",
    "invitations",
    # DJANGO REST FRAMEWORK
    "corsheaders",
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
    "sekizai",
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
    "client_side_image_cropping",
    # some other useful apps that are required by the default installation
    "django_social_share",  # easy links to social sharing sites
    "django_htmx",
    "webpack_loader",
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
    *FAIRDM_APPS,
]
