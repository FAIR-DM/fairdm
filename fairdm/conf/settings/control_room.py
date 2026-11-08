"""Control room settings: the Django Control Room dashboard and its Redis, cache and Celery panels.

Owns the control-room app list and the settings dict of every control-room package. Only
superusers can open any of it. The Redis panel reads the same ``REDIS_URL`` the cache uses and
leaves editing off, the URL panel sends no requests, and the agent interface stays off. A portal
changes a rule by assigning its own dict after ``setup()`` returns, and removes the dashboard by
removing these apps from ``INSTALLED_APPS``. The URL and signal panels are installed only by the
development settings, but their dicts live here so the access rule is kept in one place.
"""

INSTALLED_APPS = globals()["INSTALLED_APPS"]

CACHES = globals()["CACHES"]

# The hub comes after its panels, so it can unregister their placeholder admin entries.
INSTALLED_APPS += [
    "dj_control_room_base",
    "dj_redis_panel",
    "dj_cache_panel",
    "dj_celery_panel",
    "dj_control_room",
]

DJ_CONTROL_ROOM_SETTINGS = {"REQUIRE_SUPERUSER": True}

DJ_CONTROL_ROOM_BASE_SETTINGS = {"REQUIRE_SUPERUSER": True}

DJ_REDIS_PANEL_SETTINGS = {
    "REQUIRE_SUPERUSER": True,
    "INSTANCES": {"default": {"url": CACHES["default"]["LOCATION"]}},
}

DJ_CACHE_PANEL_SETTINGS = {"REQUIRE_SUPERUSER": True}

DJ_CELERY_PANEL_SETTINGS = {"REQUIRE_SUPERUSER": True}

DJ_URLS_PANEL_SETTINGS = {"REQUIRE_SUPERUSER": True, "ENABLE_TESTING": False}

DJ_SIGNALS_PANEL_SETTINGS = {"REQUIRE_SUPERUSER": True}
