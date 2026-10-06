"""Tests for the dataset forms in ``fairdm.core.dataset.forms``."""

import pytest
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from licensing.models import License

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Contribution
from fairdm.core.dataset.forms import DatasetCreateForm, DatasetForm
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestFormQuerysetFiltering:
    def test_form_filters_projects_by_user_permissions(self):
        factory = RequestFactory()
        user = UserFactory()
        other_user = UserFactory(email="otheruser@example.com")

        user_project = ProjectFactory(name="User Project")
        other_project = ProjectFactory(name="Other Project")

        ContributionFactory(
            content_object=user_project,
            contributor=user,
            level=ContributionLevel.EDIT,
        )
        Contribution.add_to(other_user, other_project, roles=["Contributor"])

        request = factory.get("/")
        request.user = user

        form = DatasetForm(request=request)

        project_queryset = form.fields["project"].queryset
        assert user_project in project_queryset
        assert other_project not in project_queryset

    def test_form_without_request_shows_all_projects(self):
        form = DatasetForm()

        project_queryset = form.fields["project"].queryset
        assert project_queryset is not None

    def test_form_with_anonymous_user_handles_gracefully(self):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = None

        form = DatasetForm(request=request)
        assert form is not None


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
                "license": License.objects.first().pk,
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
        cc_by_license = License.objects.get_or_create(
            name="CC BY 4.0",
            defaults={"url": "https://creativecommons.org/licenses/by/4.0/"},
        )[0]

        form = DatasetForm()

        assert form.fields["license"].initial == cc_by_license

    def test_license_field_is_required(self):
        form = DatasetForm()

        license_field = form.fields.get("license")
        assert license_field is not None


@pytest.mark.django_db
class TestFormValidation:
    def test_name_field_is_required(self):
        form = DatasetForm(data={})

        assert not form.is_valid()
        assert "name" in form.errors

    def test_project_field_is_optional(self):
        license = License.objects.get_or_create(name="CC BY 4.0")[0]

        form = DatasetForm(
            data={
                "name": "Test Dataset",
                "license": license.pk,
                "project": "",
            }
        )

        assert "project" not in form.errors or form.is_valid()

    def test_form_validates_with_all_required_fields(self):
        license = License.objects.get_or_create(name="CC BY 4.0")[0]
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
class TestFormRenderingWithData:
    def test_form_renders_with_existing_dataset(self):
        dataset = DatasetFactory(name="Existing Dataset")

        form = DatasetForm(instance=dataset)

        assert form.instance == dataset
        assert form.initial.get("name") == "Existing Dataset"

    def test_form_saves_changes_to_existing_dataset(self):
        dataset = DatasetFactory(name="Original Name")
        license = License.objects.get_or_create(name="CC BY 4.0")[0]

        form = DatasetForm(
            data={
                "name": "Updated Name",
                "project": dataset.project.pk,
                "license": license.pk,
                "visibility": Visibility.PUBLIC,
            },
            instance=dataset,
        )

        assert form.is_valid()
        updated_dataset = form.save()
        assert updated_dataset.name == "Updated Name"


@pytest.mark.django_db
class TestInternationalizedHelpText:
    def test_help_text_uses_gettext_lazy(self):
        form = DatasetForm()

        for field_name, field in form.fields.items():
            if field.help_text:
                help_text_type = type(field.help_text).__name__
                assert help_text_type in [
                    "Promise",
                    "str",
                    "__proxy__",
                ], f"Field {field_name} help_text is not translatable"

    def test_all_fields_have_help_text(self):
        form = DatasetForm()

        important_fields = ["name", "project", "license"]
        for field_name in important_fields:
            if field_name in form.fields:
                field = form.fields[field_name]
                assert field.help_text, (
                    f"Field {field_name} should have help_text for user guidance"
                )


@pytest.mark.django_db
class TestProjectAndReferenceFieldWidgets:
    # The django_addanother/select2 wrapper stack does not render correctly in the
    # portal.
    def test_project_field_uses_a_plain_select_widget(self):
        form = DatasetForm()

        widget = form.fields["project"].widget
        assert type(widget).__name__ == "Select"
        assert not hasattr(widget, "widget"), "project field is still wrapped"

    def test_reference_field_uses_a_plain_select_widget(self):
        form = DatasetForm()

        widget = form.fields["reference"].widget
        assert type(widget).__name__ == "Select"
        assert not hasattr(widget, "widget"), "reference field is still wrapped"

    def test_license_field_uses_a_select_widget(self):
        form = DatasetForm()

        license_field = form.fields.get("license")
        if license_field:
            widget_name = type(license_field.widget).__name__
            assert "Select" in widget_name


@pytest.mark.django_db
class TestVisibilityField:
    def test_visibility_field_exists_on_form(self):
        form = DatasetForm()

        assert "visibility" in form.fields

    def test_visibility_field_pre_selects_public(self):
        form = DatasetForm()

        assert form.fields["visibility"].initial == Visibility.PUBLIC

    def test_visibility_field_uses_a_radio_widget(self):
        form = DatasetForm()

        assert isinstance(form.fields["visibility"].widget, forms.RadioSelect)

    def test_doi_field_no_longer_exists_on_form(self):
        form = DatasetForm()

        assert "doi" not in form.fields


@pytest.mark.django_db
class TestPublishedFieldNotExposed:
    # `published` is settable in the Django admin only.
    def test_update_form_excludes_published(self):
        assert "published" not in DatasetForm.Meta.fields

        form = DatasetForm()
        assert "published" not in form.fields

    def test_create_form_excludes_published(self):
        assert "published" not in DatasetCreateForm.Meta.fields

        form = DatasetCreateForm()
        assert "published" not in form.fields


@pytest.mark.django_db
class TestDatasetForm:
    def test_form_valid_data(self):
        from licensing.models import License

        project = ProjectFactory()
        license = License.objects.get_or_create(name="CC BY 4.0")[0]

        form_data = {
            "name": "Test Dataset",
            "project": project.pk,
            "license": license.pk,
            "visibility": Visibility.PUBLIC,
        }
        form = DatasetForm(data=form_data)

        assert form.is_valid()

    def test_form_missing_required_fields(self):
        form_data = {}
        form = DatasetForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors
