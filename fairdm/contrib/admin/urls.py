import adminactions.actions as actions
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import site
from django.urls import include, path

# register all adminactions

site.add_action(actions.export_as_fixture, "export_as_fixture")
site.add_action(actions.find_duplicates_action, "find_duplicates_action")
site.add_action(actions.merge, "merge_selected")

urlpatterns = [
    path("admin/", include("smuggler.urls")),  # before admin url patterns!
    path(settings.ADMIN_URL, admin.site.urls),
]
