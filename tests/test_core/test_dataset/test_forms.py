"""Tests for the dataset forms in ``fairdm.core.dataset.forms``."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from licensing.models import License

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.forms import DatasetCreateForm, DatasetForm
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    LiteratureItemFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestCreateFormProjectFieldForAnonymousRequest:
    # `DatasetCreateView` refuses anonymous visitors before rendering, so the form is
    # used directly.
    def test_the_project_field_offers_no_projects_for_an_anonymous_request(self):
        ProjectFactory()
        factory = RequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()

        form = DatasetCreateForm(request=request)

        assert form.fields["project"].queryset.count() == 0


@pytest.mark.django_db
class TestProjectChoicesNeedTheEditLevel:
    @staticmethod
    def request_for(user):
        request = RequestFactory().get("/")
        request.user = user
        return request

    @staticmethod
    def project_at(user, level):
        project = ProjectFactory()
        ContributionFactory(content_object=project, contributor=user, level=level)
        return project

    def test_the_create_form_offers_a_project_at_edit_and_not_one_at_view(self):
        user = PersonFactory(is_active=True, is_claimed=True)
        editable = self.project_at(user, ContributionLevel.EDIT)
        viewable = self.project_at(user, ContributionLevel.VIEW)

        form = DatasetCreateForm(request=self.request_for(user))

        choices = form.fields["project"].queryset
        assert editable in choices
        assert viewable not in choices

    def test_a_post_naming_a_project_held_at_view_is_refused(self):
        user = PersonFactory(is_active=True, is_claimed=True)
        viewable = self.project_at(user, ContributionLevel.VIEW)

        form = DatasetCreateForm(
            request=self.request_for(user),
            data={
                "name": "New",
                "project": viewable.pk,
                "license": License.objects.get(name="CC BY 4.0").pk,
                "visibility": Visibility.PRIVATE,
            },
        )

        assert not form.is_valid()
        assert form.has_error("project", code="invalid_choice")

    def test_the_update_form_offers_the_same_projects_to_a_manager(self):
        user = PersonFactory(is_active=True, is_claimed=True)
        editable = self.project_at(user, ContributionLevel.EDIT)
        viewable = self.project_at(user, ContributionLevel.VIEW)
        dataset = DatasetFactory(project=editable)
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )

        form = DatasetForm(request=self.request_for(user), instance=dataset)

        choices = form.fields["project"].queryset
        assert editable in choices
        assert viewable not in choices


@pytest.mark.django_db
class TestLicenseDefault:
    def test_license_defaults_to_cc_by_4_0(self):
        cc_by_license = License.objects.get(name="CC BY 4.0")

        form = DatasetForm()

        assert form.fields["license"].initial == cc_by_license


@pytest.mark.django_db
class TestFormValidation:
    def test_form_validates_with_all_required_fields(self):
        license = License.objects.get(name="CC BY 4.0")
        project = ProjectFactory()

        form = DatasetForm(
            data={
                "name": "Valid Dataset",
                "project": project.pk,
                "license": license.pk,
                "visibility": Visibility.PUBLIC,
            }
        )

        assert form.is_valid()


@pytest.mark.django_db
class TestPublicationField:
    def test_a_dataset_saved_through_the_form_holds_the_chosen_publication(self):
        user = UserFactory()
        request = RequestFactory().get("/")
        request.user = user
        publication = LiteratureItemFactory()
        license = License.objects.get(name="CC BY 4.0")

        form = DatasetForm(
            request=request,
            data={
                "name": "New dataset",
                "license": license.pk,
                "reference": publication.pk,
                "visibility": Visibility.PRIVATE,
            },
        )

        assert form.is_valid(), form.errors
        assert form.save().reference == publication


@pytest.mark.django_db
class TestPublishedFieldNotExposed:
    # `published` is settable in the Django admin only.
    def test_update_form_excludes_published(self):
        assert "published" not in DatasetForm().fields

    def test_create_form_excludes_published(self):
        assert "published" not in DatasetCreateForm().fields
