"""Tests for the project forms in ``fairdm.core.project.forms``."""

import pytest

from fairdm.core.choices import ProjectStatus
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestProjectCreateForm:
    def test_create_form_valid_with_required_fields(self):
        from fairdm.core.project.forms import ProjectCreateForm

        form_data = {
            "name": "Test Project",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
        }

        form = ProjectCreateForm(data=form_data)

        assert form.is_valid(), f"Form errors: {form.errors}"

        project = form.save()
        assert project.pk is not None
        assert project.name == "Test Project"
        assert project.status == ProjectStatus.CONCEPT
        assert project.visibility == Visibility.PRIVATE

    def test_create_form_invalid_without_name(self):
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.forms import ProjectCreateForm

        owner = Organization.objects.create(name="Test Organization")

        form_data = {
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
            "owner": owner.pk,
        }

        form = ProjectCreateForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors
        assert form.has_error("name", code="required")

    def test_create_form_accepts_optional_description(self):
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.forms import ProjectCreateForm

        owner = Organization.objects.create(name="Test Organization")

        form_data = {
            "name": "Test Project",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
            "owner": owner.pk,
            "description": "This is a test project description.",
        }

        form = ProjectCreateForm(data=form_data)

        assert form.is_valid(), f"Form errors: {form.errors}"


@pytest.mark.django_db
class TestProjectUpdateForm:
    def test_the_field_set_is_exactly_image_name_status_visibility_owner(self):
        from fairdm.core.project.forms import ProjectForm

        form = ProjectForm()

        assert set(form.fields) == {"image", "name", "status", "visibility", "owner"}

    def test_the_form_offers_no_description_keyword_tag_contributor_or_funding_field(
        self,
    ):
        from fairdm.core.project.forms import ProjectForm

        form = ProjectForm()

        for name in ("description", "keyword", "tag", "contributor", "funding"):
            assert name not in form.fields

    def test_image_field_renders_no_label_text(self):
        from fairdm.core.project.forms import ProjectForm

        form = ProjectForm()

        assert "False" not in form["image"].label_tag()

    def test_form_allows_concept_public_combination(self):
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.forms import ProjectForm
        from fairdm.core.project.models import Project

        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Concept Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )
        form_data = {
            "name": project.name,
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PUBLIC,
            "owner": owner.pk,
        }
        form = ProjectForm(data=form_data, instance=project)
        assert form.is_valid(), (
            f"Expected CONCEPT+PUBLIC to be valid, got errors: {form.errors}"
        )
        assert "visibility" not in form.errors
        assert "__all__" not in form.errors

    def test_edit_form_allows_all_fields_for_active_project(self):
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.forms import ProjectForm
        from fairdm.core.project.models import Project

        owner = Organization.objects.create(name="Test Organization")

        project = Project.objects.create(
            name="Active Project",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )

        form_data = {
            "name": "Updated Project Name",
            "status": ProjectStatus.IN_PROGRESS,
            "visibility": Visibility.PUBLIC,
            "owner": owner.pk,
        }

        form = ProjectForm(data=form_data, instance=project)

        assert form.is_valid(), f"Form errors: {form.errors}"

        updated_project = form.save()
        assert updated_project.name == "Updated Project Name"
        assert updated_project.visibility == Visibility.PUBLIC
