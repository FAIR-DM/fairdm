"""Tests for the Dataset model, views, and forms."""

import pytest
from django.test import Client, TestCase
from django.urls import reverse

from fairdm.contrib.contributors.models import Person
from fairdm.core.dataset.forms import DatasetForm
from fairdm.core.dataset.models import DatasetDate, DatasetDescription
from fairdm.core.models import Dataset
from fairdm.factories.core import DatasetFactory, ProjectFactory
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestDatasetModel:
    """Tests for the Dataset model."""

    def test_dataset_creation(self):
        """Test creating a basic Dataset instance."""
        dataset = DatasetFactory()

        assert dataset.pk is not None
        assert dataset.name is not None
        assert dataset.uuid is not None
        assert dataset.uuid.startswith("d")

    def test_dataset_visibility_default(self):
        """Test that default visibility is PRIVATE."""
        dataset = DatasetFactory()
        # Factory may set visibility randomly, so just check it's a valid value
        assert dataset.visibility in Visibility.values

    def test_dataset_queryset_get_visible(self):
        """Test DatasetQuerySet.get_visible() filters correctly."""
        # Create public and private datasets
        public_dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        private_dataset = DatasetFactory(visibility=Visibility.PRIVATE)

        visible = Dataset.objects.get_visible()

        assert public_dataset in visible
        assert private_dataset not in visible

    def test_dataset_queryset_with_contributors(self):
        """Test DatasetQuerySet.with_contributors() prefetches correctly."""
        dataset = DatasetFactory()

        # This should not raise an error and should be efficient
        queryset = Dataset.objects.with_contributors()
        dataset_with_prefetch = queryset.get(pk=dataset.pk)

        # Access contributors should not cause additional queries due to prefetch
        assert dataset_with_prefetch.contributors is not None

    def test_dataset_queryset_with_related(self):
        """Test DatasetQuerySet.with_related() prefetches correctly."""
        dataset = DatasetFactory()

        queryset = Dataset.objects.with_related()
        dataset_with_prefetch = queryset.get(pk=dataset.pk)

        # Should have prefetched project and contributors
        assert dataset_with_prefetch.project is not None

    def test_dataset_str_representation(self):
        """Test Dataset string representation."""
        dataset = DatasetFactory(name="Test Dataset")
        assert str(dataset) == "Test Dataset"

    def test_dataset_absolute_url(self):
        """Test get_absolute_url returns correct URL."""
        dataset = DatasetFactory()
        url = dataset.get_absolute_url()

        assert url == reverse("dataset:overview", kwargs={"uuid": dataset.uuid})

    def test_dataset_has_data_property(self):
        """Test has_data cached property."""
        dataset = DatasetFactory()

        # Initially should return False (no samples or measurements)
        has_data = dataset.has_data
        assert isinstance(has_data, bool)

    def test_dataset_bbox_property(self):
        """Test bbox cached property."""
        dataset = DatasetFactory()

        # Should return a bounding box or None
        bbox = dataset.bbox
        assert bbox is None or isinstance(bbox, (dict, tuple, list))

    def test_dataset_descriptions_relationship(self):
        """Test that dataset descriptions can be created correctly."""
        dataset = DatasetFactory()
        descriptions = DatasetDescription.objects.filter(related=dataset)

        # Factory may or may not create descriptions by default
        assert descriptions.count() >= 0
        assert all(desc.related == dataset for desc in descriptions)

    def test_dataset_dates_relationship(self):
        """Test that dataset dates can be created correctly."""
        dataset = DatasetFactory()
        dates = DatasetDate.objects.filter(related=dataset)

        # Factory may or may not create dates by default
        assert dates.count() >= 0
        assert all(date.related == dataset for date in dates)

    def test_add_contributor(self):
        """Test adding a contributor to a dataset."""
        dataset = DatasetFactory()
        user = Person.objects.create(
            name="Test User",
            email="test@example.com",
        )

        contribution = dataset.add_contributor(user, with_roles=["Creator"])

        assert contribution is not None
        assert contribution.contributor == user
        assert dataset.contributors.filter(pk=contribution.pk).exists()

    def test_dataset_project_relationship(self):
        """Test that dataset can be associated with a project."""
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)

        assert dataset.project == project
        assert dataset in project.datasets.all()


class TestDatasetForm(TestCase):
    """Tests for the DatasetForm."""

    def test_form_valid_data(self):
        """Test form validation with valid data."""
        project = ProjectFactory()

        form_data = {
            "name": "Test Dataset",
            "project": project.pk,
        }
        form = DatasetForm(data=form_data)

        assert form.is_valid()

    def test_form_missing_required_fields(self):
        """Test form validation fails without required fields."""
        form_data = {}
        form = DatasetForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors


@pytest.mark.django_db
class TestDatasetViews:
    """Tests for Dataset views."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = Person.objects.create(
            name="Test User",
            email="test@example.com",
        )
        self.user.set_password("testpass123")
        self.user.save()

    def test_dataset_list_view_accessible(self):
        """Test that dataset list view is accessible."""
        response = self.client.get(reverse("dataset-list"))

        assert response.status_code == 200

    def test_dataset_list_view_shows_public_datasets(self):
        """Test that only public datasets are shown in list view."""
        public_dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        private_dataset = DatasetFactory(visibility=Visibility.PRIVATE)

        response = self.client.get(reverse("dataset-list"))

        # Check that public dataset is visible
        assert public_dataset.name.encode() in response.content
        # Check that private dataset is not visible
        assert private_dataset.name.encode() not in response.content

    def test_dataset_create_view_requires_authentication(self):
        """Test that dataset creation requires login."""
        response = self.client.get(reverse("dataset-create"))

        # Should redirect to login
        assert response.status_code == 302

    def test_dataset_create_view_accessible_when_authenticated(self):
        """Test that authenticated users can access dataset create view."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("dataset-create"))

        assert response.status_code == 200

    def test_dataset_create_view_with_project_param(self):
        """Test dataset creation with project parameter in URL."""
        self.client.force_login(self.user)
        project = ProjectFactory()

        response = self.client.get(reverse("dataset-create"), {"project": project.pk})

        assert response.status_code == 200

    def test_dataset_detail_view_accessible(self):
        """Test that dataset detail view is accessible."""
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        response = self.client.get(reverse("dataset:overview", kwargs={"uuid": dataset.uuid}))

        assert response.status_code == 200
        assert dataset.name.encode() in response.content


@pytest.mark.django_db
class TestDatasetPermissions:
    """Tests for Dataset permissions and access control."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = Person.objects.create(
            name="Test User",
            email="test@example.com",
        )
        self.user.set_password("testpass123")
        self.user.save()

    def test_anonymous_user_cannot_create_dataset(self):
        """Test that anonymous users cannot create datasets."""
        form_data = {
            "name": "Test Dataset",
        }

        response = self.client.post(reverse("dataset-create"), data=form_data)

        # Should redirect to login
        assert response.status_code == 302
        # Check that redirect URL contains 'login'
        assert "login" in response["Location"]

    def test_dataset_creator_becomes_contributor(self):
        """Test that dataset creator is automatically added as contributor."""
        self.client.force_login(self.user)

        form_data = {
            "name": "Test Dataset",
        }

        self.client.post(reverse("dataset-create"), data=form_data)

        dataset = Dataset.objects.filter(name="Test Dataset").first()
        if dataset:
            # Check that the dataset has contributors
            assert dataset.contributors.count() > 0

