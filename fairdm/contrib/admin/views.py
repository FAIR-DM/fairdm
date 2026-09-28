"""Superuser-only admin views, including fixture upload."""

import os
import tempfile

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View


def superuser_required(view_func):
    """Restrict a view to active superusers.

    Args:
        view_func: The view to protect.

    Returns:
        The view wrapped so other users are sent to the login page.
    """
    return user_passes_test(lambda u: u.is_active and u.is_superuser)(view_func)


class FixtureUploadForm(forms.Form):
    """Form with a single field for the fixture file to load."""

    fixture_file = forms.FileField(label="Select a fixture file")


def get_full_extension(filename):
    """Return a filename's extension, keeping a compression suffix with the one before it.

    Args:
        filename: The uploaded file's name.

    Returns:
        The extension, for example ``.json.gz`` for ``data.json.gz``.
    """
    base, ext = os.path.splitext(filename)
    if ext in (".gz", ".zip"):
        _, ext2 = os.path.splitext(base)
        return ext2 + ext if ext2 else ext
    return ext


@method_decorator(superuser_required, name="dispatch")
class FixtureUploadView(View):
    """Upload a fixture file and load it with ``loaddata``."""

    template_name = "admin/fixture_upload_form.html"

    def get(self, request):
        """Render the empty upload form."""
        form = FixtureUploadForm()
        return render(
            request, self.template_name, {"form": form, "title": "Upload Fixture File"}
        )

    def post(self, request):
        """Load the uploaded fixture and report success or the load error."""
        form = FixtureUploadForm(request.POST, request.FILES)
        if form.is_valid():
            fixture_file = request.FILES["fixture_file"]
            upload_ext = get_full_extension(fixture_file.name)
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=upload_ext
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
        return render(
            request, self.template_name, {"form": form, "title": "Upload Fixture File"}
        )
