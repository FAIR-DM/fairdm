"""URL configuration for the admin site."""

import adminactions.actions as actions
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import site
from django.urls import path

site.add_action(actions.export_as_fixture, "export_as_fixture")

urlpatterns = [
    path(getattr(settings, "ADMIN_URL", "admin/"), admin.site.urls),
]
