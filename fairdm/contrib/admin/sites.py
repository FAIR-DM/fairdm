import os
import tempfile

from admin_site_search.views import AdminSiteSearchView
from django import forms
from django.contrib import admin
from django.urls import path

from .views import FixtureUploadView


class FixtureUploadForm(forms.Form):
    fixture_file = forms.FileField(label="Select a fixture file")


from django.contrib import messages
from django.core.management import call_command
from django.shortcuts import redirect, render


class CustomAdminSite(AdminSiteSearchView, admin.AdminSite):
    site_header = "FairDM Admin"
    site_title = "FairDM Admin"
    index_title = "Welcome to the FairDM Admin Portal"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("upload-fixture/", self.admin_view(FixtureUploadView.as_view()), name="upload_fixture"),
        ]
        return custom_urls + urls

    def upload_fixture_view(self, request):
        if request.method == "POST":
            form = FixtureUploadForm(request.POST, request.FILES)
            if form.is_valid():
                fixture_file = request.FILES["fixture_file"]
                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
                    for chunk in fixture_file.chunks():
                        tmp_file.write(chunk)
                    tmp_file_path = tmp_file.name

                try:
                    call_command("loaddata", tmp_file_path)
                    messages.success(request, "Fixture loaded successfully.")
                except Exception as e:
                    messages.error(request, f"Error loading fixture: {e}")
                finally:
                    os.remove(tmp_file_path)

                return redirect("admin:index")
        else:
            form = FixtureUploadForm()

        context = {
            "form": form,
            "title": "Upload Fixture File",
        }
        return render(request, "admin/fixture_upload_form.html", context)
