"""URL configuration for the admin site."""

import adminactions.actions as actions
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import site
from django.urls import include, path

site.add_action(actions.export_as_fixture, "export_as_fixture")

admin_url = getattr(settings, "ADMIN_URL", "admin/")

# Control-room panels, each mounted only while its app is installed. Ahead of the admin's own
# pattern, which would otherwise answer every address under the admin prefix.
CONTROL_ROOM_PANELS = (
    ("dj_redis_panel", "dj-redis-panel"),
    ("dj_cache_panel", "dj-cache-panel"),
    ("dj_celery_panel", "dj-celery-panel"),
    ("dj_urls_panel", "dj-urls-panel"),
    ("dj_signals_panel", "dj-signals-panel"),
    ("dj_control_room", "dj-control-room"),
)

urlpatterns = [
    path(f"{admin_url}{prefix}/", include(f"{label}.urls"))
    for label, prefix in CONTROL_ROOM_PANELS
    if apps.is_installed(label)
]

urlpatterns.append(path(admin_url, admin.site.urls))
