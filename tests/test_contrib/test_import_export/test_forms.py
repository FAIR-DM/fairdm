"""Tests for fairdm/contrib/import_export/forms.py."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from fairdm.contrib.import_export.forms import ImportOptionsForm, UploadForm
from fairdm.contrib.import_export.models import ImportJob


def descriptions(form, name):
    """Return the description each choice of a card field is drawn with."""
    return [option.data.get("description") for option in form[name].subwidgets]


class TestImportOptionsForm:
    """What the file may do, and what an empty cell means."""

    def test_defaults_add_and_update_and_keep_the_stored_value(self):
        form = ImportOptionsForm()

        assert form["mode"].initial == ImportJob.Mode.BOTH
        assert form["empty"].initial == ImportJob.Empty.KEEP

    def test_the_choices_are_the_job_choices(self):
        form = ImportOptionsForm()

        assert [
            value for value, _ in form.fields["mode"].choices
        ] == ImportJob.Mode.values
        assert [value for value, _ in form.fields["empty"].choices] == (
            ImportJob.Empty.values
        )

    def test_each_choice_is_drawn_with_a_description(self):
        form = ImportOptionsForm()

        assert all(descriptions(form, "mode"))
        assert all(descriptions(form, "empty"))

    def test_brief_draws_each_choice_without_a_description(self):
        form = ImportOptionsForm(brief=True)

        assert not any(descriptions(form, "mode"))
        assert not any(descriptions(form, "empty"))

    def test_brief_leaves_the_next_form_with_its_descriptions(self):
        ImportOptionsForm(brief=True)

        assert all(descriptions(ImportOptionsForm(), "mode"))

    def test_chosen_returns_the_values_the_form_holds(self):
        form = ImportOptionsForm({"mode": "update", "empty": "clear"})

        assert form.chosen("both", "keep") == ("update", "clear")

    def test_chosen_returns_the_given_values_for_a_form_not_filled_in(self):
        form = ImportOptionsForm()

        assert form.chosen("add", "clear") == ("add", "clear")

    def test_chosen_returns_the_given_values_for_a_choice_that_does_not_exist(self):
        form = ImportOptionsForm({"mode": "delete", "empty": "erase"})

        assert form.chosen("add", "clear") == ("add", "clear")

    def test_a_choice_that_does_not_exist_is_an_error_on_its_field(self):
        form = ImportOptionsForm({"mode": "delete", "empty": "keep"})

        assert not form.is_valid()
        assert form.has_error("mode", code="invalid_choice")


class TestUploadForm:
    """The file field: its format and size are checked before a job is recorded."""

    @staticmethod
    def upload(name, content=b"name\nA\n"):
        """Return a form holding one uploaded file."""
        return UploadForm(files={"file": SimpleUploadedFile(name, content)})

    @pytest.mark.parametrize(
        "name", ["rocks.csv", "rocks.tsv", "rocks.xlsx", "rocks.ods"]
    )
    def test_a_file_of_a_read_format_is_accepted(self, name):
        assert self.upload(name).is_valid()

    def test_the_extension_is_read_in_any_case(self):
        assert self.upload("ROCKS.CSV").is_valid()

    @pytest.mark.parametrize("name", ["rocks.json", "rocks.txt", "rocks"])
    def test_a_file_of_another_format_is_refused(self, name):
        form = self.upload(name)

        assert not form.is_valid()
        assert form.has_error("file", code="format")

    def test_a_file_over_the_size_limit_is_refused(self):
        form = self.upload("rocks.csv", b"x" * (UploadForm.MAX_BYTES + 1))

        assert not form.is_valid()
        assert form.has_error("file", code="too_large")

    def test_a_file_at_the_size_limit_is_accepted(self):
        assert self.upload("rocks.csv", b"x" * UploadForm.MAX_BYTES).is_valid()

    def test_a_form_with_no_file_is_refused(self):
        form = UploadForm(files={})

        assert not form.is_valid()
        assert form.has_error("file", code="required")
