from environ import Env

env = Env(
    # FAIRDM SETTINGS
    FAIRDM_ALLOW_DISCUSSIONS=(bool, True),
    # when False, discussion tabs are hidden from the detail views
    FAIRDM_SHOW_DATA_TABLES=(bool, True),
    # when False, data tables are hidden from the UI (useful for portals that don't make use of Sample or Measurement models)
    FAIRDM_ALLOW_PUBLIC_REGISTRATION=(bool, True),
    # when False, registrations are only allowed by invitation
    # DJANGO
    DJANGO_ADMIN_URL=(str, "admin/"),
    DJANGO_SUPERUSER_EMAIL=(str, "super.user@example.com"),
    DJANGO_SUPERUSER_PASSWORD=(str, "admin"),
    DJANGO_ALLOWED_HOSTS=(list, []),
    DJANGO_CACHE=(bool, True),
    DJANGO_DEBUG=(bool, False),
    DJANGO_READ_DOT_ENV_FILE=(bool, False),
    DJANGO_SECRET_KEY=(str, "django-insecure-qQN1YqvsY7dQ1xtdhLavAeXn1mUEAI0Wu8vkDbodEqRKkJbHyMEQS5F"),
    DJANGO_SITE_DOMAIN=(str, "localhost:8000"),
    DJANGO_SITE_ID=(int, 1),
    DJANGO_SITE_NAME=(str, "FairDM Demo"),
    DJANGO_TIME_ZONE=(str, "UTC"),
    DJANGO_ROOT_URLCONF=(str, "config.urls"),
    # SECURITY
    DJANGO_SECURE=(bool, True),
    DJANGO_SECURE_HSTS_SECONDS=(int, 60),
    # DATABASE
    DATABASE_URL=(str, ""),
    POSTGRES_DB=(str, ""),
    POSTGRES_PASSWORD=(str, ""),
    POSTGRES_USER=(str, "postgres"),
    POSTGRES_HOST=(str, "postgres"),
    POSTGRES_PORT=(int, 5432),
    # EMAIL
    EMAIL_HOST=(str, ""),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    EMAIL_PORT=(int, 587),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_BACKEND=(str, "django.core.mail.backends.smtp.EmailBackend"),
    # STORAGE
    S3_REGION_NAME=(str, ""),
    S3_BUCKET_NAME=(str, ""),
    S3_ACCESS_KEY_ID=(str, ""),
    S3_SECRET_ACCESS_KEY=(str, ""),
    # MISCELLANEOUS
    REDIS_URL=(str, ""),
    # REDIS_URL=(str, "redis://redis:6379/0"),
    USE_DOCKER=(bool, False),
    SHOW_DEBUG_TOOLBAR=(bool, False),
)
