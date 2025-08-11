import fairdm

fairdm.setup(apps=["example"])

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = False

INSTALLED_APPS += [
    "fairdm_discussions",
    "django_comments_xtd",
    "django_comments",
]
