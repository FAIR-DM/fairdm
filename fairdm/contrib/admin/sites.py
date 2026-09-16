import os
import tempfile

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.translation import gettext as _

from fairdm.portal_roles import PortalRoles

from .views import FixtureUploadView


class FixtureUploadForm(forms.Form):
    fixture_file = forms.FileField(label="Select a fixture file")


def _holds_a_rights_carrying_role(user) -> bool:
    """Whether ``user`` belongs to at least one role that carries permissions.

    Access is derived from role membership, never stored on the person (research R3):
    nothing here sets ``is_staff``.
    """
    return user.groups.filter(name__in=PortalRoles.rights_carrying()).exists()


class PortalAdminAuthenticationForm(AdminAuthenticationForm):
    """Accepts a holder of a rights-carrying role, not only an ``is_staff`` account.

    ``AdminAuthenticationForm.confirm_login_allowed`` refuses a non-staff user before
    ``CustomAdminSite.has_permission`` is ever consulted (research R3), so both must change
    together or a role holder can only reach the interface while already signed in.
    """

    def confirm_login_allowed(self, user):
        super(AdminAuthenticationForm, self).confirm_login_allowed(user)
        if not (user.is_staff or _holds_a_rights_carrying_role(user)):
            raise ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
                params={"username": self.username_field.verbose_name},
            )


class CustomAdminSite(admin.AdminSite):
    site_header = _("Portal Administration")
    site_title = _("Portal Administration")
    index_title = _("Portal Administration")
    login_form = PortalAdminAuthenticationForm

    def has_permission(self, request):
        """Accept a holder of a rights-carrying role, not only an ``is_staff`` account
        (research R3). Nothing is stored on the person to grant this."""
        user = request.user
        return user.is_active and (user.is_staff or _holds_a_rights_carrying_role(user))

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "upload-fixture/",
                self.admin_view(FixtureUploadView.as_view()),
                name="upload_fixture",
            ),
        ]
        return custom_urls + urls

    def upload_fixture_view(self, request):
        if request.method == "POST":
            form = FixtureUploadForm(request.POST, request.FILES)
            if form.is_valid():
                fixture_file = request.FILES["fixture_file"]
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".json"
                ) as tmp_file:
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
