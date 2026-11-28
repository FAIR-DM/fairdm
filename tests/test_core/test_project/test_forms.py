"""Tests for the project forms in ``fairdm.core.project.forms``."""

from types import SimpleNamespace

import pytest

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.choices import ProjectStatus
from fairdm.factories import ContributionFactory, UserFactory
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

    def test_the_create_form_preselects_public_visibility(self):
        from fairdm.core.project.forms import ProjectCreateForm

        form = ProjectCreateForm()

        assert form["visibility"].value() == Visibility.PUBLIC


@pytest.mark.django_db
class TestProjectUpdateForm:
    def test_the_form_offers_no_description_keyword_tag_contributor_or_funding_field(
        self,
    ):
        from fairdm.core.project.forms import ProjectForm

        form = ProjectForm()

        for name in ("description", "keyword", "tag", "contributor", "funding"):
            assert name not in form.fields

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

        manager = UserFactory()
        ContributionFactory(
            content_object=project, contributor=manager, level=ContributionLevel.MANAGE
        )
        form = ProjectForm(
            data=form_data, instance=project, request=SimpleNamespace(user=manager)
        )

        assert form.is_valid(), f"Form errors: {form.errors}"

        updated_project = form.save()
        assert updated_project.name == "Updated Project Name"
        assert updated_project.visibility == Visibility.PUBLIC


@pytest.mark.django_db
class TestProjectOwnerField:
    def test_the_chosen_owner_is_saved(self, in_request):
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.forms import ProjectForm
        from fairdm.core.project.models import Project

        owner = Organization.objects.create(name="Test Organization")
        manager = UserFactory()
        project = Project.objects.create(
            name="Owned", status=ProjectStatus.CONCEPT, visibility=Visibility.PRIVATE
        )
        ContributionFactory(
            content_object=project, contributor=manager, level=ContributionLevel.MANAGE
        )
        in_request(manager)
        form = ProjectForm(
            data={
                "name": "Owned",
                "status": ProjectStatus.CONCEPT,
                "visibility": Visibility.PRIVATE,
                "owner": owner.pk,
            },
            instance=project,
            request=SimpleNamespace(user=manager),
        )

        assert form.is_valid(), form.errors
        form.save()

        project.refresh_from_db()
        assert project.owner == owner
