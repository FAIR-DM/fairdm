# admin_forms.py
# admin_views.py
# admin_views.py
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
    return user_passes_test(lambda u: u.is_active and u.is_superuser)(view_func)


class FixtureUploadForm(forms.Form):
    fixture_file = forms.FileField(label="Select a fixture file")


def get_full_extension(filename):
    base, ext = os.path.splitext(filename)
    if ext in (".gz", ".zip"):  # Look for compound extensions
        _, ext2 = os.path.splitext(base)
        return ext2 + ext if ext2 else ext
    return ext


@method_decorator(superuser_required, name="dispatch")
class FixtureUploadView(View):
    template_name = "admin/fixture_upload_form.html"

    def get(self, request):
        form = FixtureUploadForm()
        return render(request, self.template_name, {"form": form, "title": "Upload Fixture File"})

    def post(self, request):
        form = FixtureUploadForm(request.POST, request.FILES)
        if form.is_valid():
            fixture_file = request.FILES["fixture_file"]
            upload_ext = get_full_extension(fixture_file.name)
            with tempfile.NamedTemporaryFile(delete=False, suffix=upload_ext) as tmp_file:
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
        return render(request, self.template_name, {"form": form, "title": "Upload Fixture File"})
