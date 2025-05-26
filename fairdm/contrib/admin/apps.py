# from adminactions import actions
from django.apps import AppConfig
from django.contrib.admin import apps


class FairDMAdminConfig(AppConfig):
    # default_site = "fairdm.contrib.admin.sites.CustomAdminSite"
    name = "fairdm.contrib.admin"
    label = "fairdm_admin"


class FairDMAdminSite(apps.AdminConfig):
    default_site = "fairdm.contrib.admin.sites.CustomAdminSite"

    # def ready(self):
    #     super().ready()
    #     from django.contrib.admin import site

    #     site.add_action(actions.export_as_fixture, "export_as_fixture")
    #     site.add_action(actions.find_duplicates_action, "find_duplicates_action")
    #     site.add_action(actions.merge, "merge_selected")
