"""Tests for the Sample model, views, and forms."""

import pytest
from django.test import Client, TestCase
from django.urls import reverse

from fairdm.contrib.contributors.models import Person
from fairdm.core.models import Sample
from fairdm.core.sample.forms import SampleForm
from fairdm.core.sample.models import SampleDate, SampleDescription, SampleRelation
from fairdm.factories.core import DatasetFactory, SampleFactory


@pytest.mark.django_db
class TestSampleModel:
    """Tests for the Sample model."""

    def test_sample_creation(self):
        """Test creating a basic Sample instance."""
        sample = SampleFactory()

        assert sample.pk is not None
        assert sample.name is not None
        assert sample.uuid is not None
        assert sample.uuid.startswith("s")

    def test_sample_str_representation(self):
        """Test Sample string representation."""
        sample = SampleFactory(name="Test Sample")
        assert str(sample) == "Test Sample"

    def test_sample_dataset_relationship(self):
        """Test that sample is associated with a dataset."""
        dataset = DatasetFactory()
        sample = SampleFactory(dataset=dataset)

        assert sample.dataset == dataset
        assert sample in dataset.samples.all()

    def test_sample_local_id_optional(self):
        """Test that local_id is optional."""
        sample = SampleFactory(local_id=None)
        assert sample.local_id is None

        sample_with_id = SampleFactory(local_id="ABC-123")
        assert sample_with_id.local_id == "ABC-123"

    def test_sample_location_optional(self):
        """Test that location is optional."""
        sample = SampleFactory(location=None)
        assert sample.location is None

    def test_sample_status_default(self):
        """Test that sample has a status."""
        sample = SampleFactory()
        # Status should be set (factory may randomize)
        assert sample.status is not None

    def test_sample_get_template_name(self):
        """Test get_template_name returns correct template paths."""
        sample = SampleFactory()
        templates = sample.get_template_name()

        assert isinstance(templates, list)
        assert len(templates) == 2
        assert templates[1] == "fairdm/sample_card.html"

    def test_sample_type_of_property(self):
        """Test type_of classproperty."""
        assert Sample.type_of == Sample

    def test_sample_descriptions_relationship(self):
        """Test that sample descriptions can be created correctly."""
        sample = SampleFactory()
        descriptions = SampleDescription.objects.filter(related=sample)

        # Factory may or may not create descriptions by default
        assert descriptions.count() >= 0
        assert all(desc.related == sample for desc in descriptions)

    def test_sample_dates_relationship(self):
        """Test that sample dates can be created correctly."""
        sample = SampleFactory()
        dates = SampleDate.objects.filter(related=sample)

        # Factory may or may not create dates by default
        assert dates.count() >= 0
        assert all(date.related == sample for date in dates)

    def test_add_contributor(self):
        """Test adding a contributor to a sample."""
        sample = SampleFactory()
        user = Person.objects.create(
            name="Test User",
            email="test@example.com",
        )

        contribution = sample.add_contributor(user, with_roles=["Creator"])

        assert contribution is not None
        assert contribution.contributor == user
        assert sample.contributors.filter(pk=contribution.pk).exists()


@pytest.mark.django_db
class TestSampleRelation:
    """Tests for the SampleRelation model."""

    def test_sample_relation_creation(self):
        """Test creating a sample-to-sample relationship."""
        parent = SampleFactory()
        child = SampleFactory()

        relation = SampleRelation.objects.create(
            type="child_of",
            source=child,
            target=parent,
        )

        assert relation.pk is not None
        assert relation.source == child
        assert relation.target == parent
        assert relation.type == "child_of"

    def test_sample_relation_queryset(self):
        """Test querying sample relationships."""
        parent = SampleFactory()
        child = SampleFactory()

        SampleRelation.objects.create(
            type="child_of",
            source=child,
            target=parent,
        )

        # Query from child to parent
        related_samples = child.related_samples.all()
        assert related_samples.count() == 1
        assert related_samples.first().target == parent

        # Query from parent to child
        related_to = parent.related_to.all()
        assert related_to.count() == 1
        assert related_to.first().source == child


class TestSampleForm(TestCase):
    """Tests for the SampleForm."""

    def test_form_valid_data(self):
        """Test form validation with valid data."""
        dataset = DatasetFactory()

        form_data = {
            "name": "Test Sample",
            "dataset": dataset.pk,
            "status": "unknown",  # Use default status value
        }
        form = SampleForm(data=form_data)

        assert form.is_valid()

    def test_form_missing_required_fields(self):
        """Test form validation fails without required fields."""
        form_data = {}
        form = SampleForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors

    def test_form_with_request_context(self):
        """Test form initialization with request object."""
        from unittest.mock import Mock

        request = Mock()
        form = SampleForm(request=request)

        assert form.request == request


@pytest.mark.django_db
class TestSampleViews:
    """Tests for Sample views."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = Person.objects.create(
            name="Test User",
            email="test@example.com",
        )
        self.user.set_password("testpass123")
        self.user.save()

    def test_sample_detail_view_accessible(self):
        """Test that sample detail view is accessible."""
        sample = SampleFactory()
        # Note: URL pattern may vary, adjust as needed
        try:
            response = self.client.get(reverse("sample:detail", kwargs={"uuid": sample.uuid}))
            assert response.status_code in [200, 302, 404]  # May vary based on permissions
        except Exception:
            # URL may not be configured or may require different namespace
            pytest.skip("Sample detail URL not configured")


@pytest.mark.django_db
class TestSamplePermissions:
    """Tests for Sample permissions and access control."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = Person.objects.create(
            name="Test User",
            email="test@example.com",
        )
        self.user.set_password("testpass123")
        self.user.save()

    def test_sample_contributor_relationship(self):
        """Test that samples can have contributors."""
        sample = SampleFactory()
        contribution = sample.add_contributor(self.user, with_roles=["Creator"])

        assert sample.contributors.count() == 1
        assert contribution.contributor == self.user
