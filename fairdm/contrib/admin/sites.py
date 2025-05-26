from admin_site_search.views import AdminSiteSearchView
from django.contrib import admin


class CustomAdminSite(AdminSiteSearchView, admin.AdminSite):
    site_header = "FairDM Admin"
    site_title = "FairDM Admin"
    index_title = "Welcome to the FairDM Admin Portal"
