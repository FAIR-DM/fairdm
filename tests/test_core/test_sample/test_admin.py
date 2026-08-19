"""Integration tests for Sample admin interface.

Tests for User Story 2: Enhanced Admin Interface

This module tests the Django admin interface for Sample models including:
- Search functionality (name, local_id, uuid)
- Filtering (dataset, status, location)
- Inline metadata editing (descriptions, dates, identifiers, relationships)
- Polymorphic type handling

Based on tasks T031-T033 from Feature 007.
"""

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse

from fairdm.core.sample.admin import (
    SampleChildAdmin,
    SampleDateInline,
    SampleDescriptionInline,
    SampleIdentifierInline,
    SampleParentAdmin,
)
from fairdm.core.sample.models import (
    Sample,
    SampleDate,
    SampleDescription,
    SampleIdentifier,
    SampleRelation,
)
from fairdm.factories.core import DatasetFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility
from fairdm_demo.factories import RockSampleFactory, WaterSampleFactory
from fairdm_demo.models import RockSample, WaterSample

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create a superuser for admin access."""
    user = User.objects.create_superuser(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="admin123",
    )
    return user


@pytest.fixture
def sample_admin():
    """Create a SampleAdmin instance."""
    return SampleChildAdmin(Sample, AdminSite())


@pytest.fixture
def request_factory():
    """Create a RequestFactory instance."""
    return RequestFactory()


def _result_pks(response):
    """The primary keys the changelist actually matched - read off the `ChangeList`
    Django's admin builds, which is the result set itself, not the rendered markup.
    """
    return {obj.pk for obj in response.context["cl"].result_list}


@pytest.mark.django_db
class TestSampleAdminSearch:
    """T081/FR-039: each supported search term finds a matching specimen, asserted
    through the registered polymorphic parent's changelist rather than by calling
    `get_search_results()` against the model manager."""

    def test_search_by_name(self, admin_client):
        match = RockSampleFactory(name="Granite Sample")
        other = RockSampleFactory(name="Basalt Sample")

        url = reverse("admin:sample_sample_changelist")
        response = admin_client.get(url, {"q": "Granite"})

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks

    def test_search_by_local_id(self, admin_client):
        match = RockSampleFactory(local_id="SAMPLE-001")
        other = RockSampleFactory(local_id="SAMPLE-002")

        url = reverse("admin:sample_sample_changelist")
        response = admin_client.get(url, {"q": "SAMPLE-001"})

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks

    def test_search_by_uuid(self, admin_client):
        match = RockSampleFactory()
        other = RockSampleFactory()

        url = reverse("admin:sample_sample_changelist")
        response = admin_client.get(url, {"q": match.uuid})

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks

    def test_search_returns_empty_for_no_matches(self, admin_client):
        RockSampleFactory(name="Test Sample")

        url = reverse("admin:sample_sample_changelist")
        response = admin_client.get(url, {"q": "NonExistent"})

        assert response.status_code == 200
        assert _result_pks(response) == set()


@pytest.mark.django_db
class TestSampleAdminFilters:
    """T082/FR-039: each supported filter removes the specimens that do not match,
    asserted through the changelist's actual result set."""

    def test_filter_by_dataset(self, admin_client):
        dataset1 = DatasetFactory(name="Dataset A")
        dataset2 = DatasetFactory(name="Dataset B")

        match = RockSampleFactory(dataset=dataset1)
        other = RockSampleFactory(dataset=dataset2)

        url = reverse("admin:sample_sample_changelist")
        response = admin_client.get(url, {"dataset__id__exact": str(dataset1.pk)})

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks

    def test_filter_by_status(self, admin_client):
        match = RockSampleFactory()
        match.status = "available"
        match.save()
        other = RockSampleFactory()
        other.status = "stored"
        other.save()

        url = reverse("admin:sample_sample_changelist")
        response = admin_client.get(url, {"status__exact": "available"})

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks

    def test_multiple_filters_can_be_combined(self, admin_client):
        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()
        match = RockSampleFactory(dataset=dataset1)
        match.status = "available"
        match.save()
        # Same dataset, different status - excluded by the status half of the filter.
        same_dataset = RockSampleFactory(dataset=dataset1)
        same_dataset.status = "stored"
        same_dataset.save()
        # Same status, different dataset - excluded by the dataset half of the filter.
        RockSampleFactory(dataset=dataset2)

        url = reverse("admin:sample_sample_changelist")
        response = admin_client.get(
            url,
            {"dataset__id__exact": str(dataset1.pk), "status__exact": "available"},
        )

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert same_dataset.pk not in pks


@pytest.mark.django_db
class TestSampleDatasetListFilterOrdering:
    """F9 - `field_choices` calls `order_by(*ordering)`, and an empty `ordering` tuple - what
    `field_admin_ordering` returns when nothing declares admin-level ordering, the case here -
    *clears* `Dataset.Meta.ordering` (`order_by()` with no arguments is not a no-op) rather than
    leaving the model's own default ordering in place."""

    def test_falls_back_to_the_datasets_own_default_ordering(self):
        from fairdm.core.sample.admin import SampleDatasetListFilter

        early = DatasetFactory()
        late = DatasetFactory()

        field = Sample._meta.get_field("dataset")
        request = RequestFactory().get("/")
        model_admin = admin.site._registry[Sample]
        list_filter = SampleDatasetListFilter.__new__(SampleDatasetListFilter)

        choices = list_filter.field_choices(field, request, model_admin)
        pks_in_order = [pk for pk, _label in choices]

        # Dataset.Meta.ordering = ["-modified"]: the more recently modified/created "late"
        # dataset sorts first. An empty order_by() falls back to whatever the database happens
        # to return with no ORDER BY, which for two freshly-inserted rows is ascending pk -
        # "early" before "late" - the opposite of what is asserted here.
        assert pks_in_order.index(late.pk) < pks_in_order.index(early.pk)


@pytest.mark.django_db
class TestSampleAdminInlines:
    """T083/T089/FR-039: a description, a date, an identifier, a contribution and a
    provenance link can each be added from the specimen's own page - a real form
    submission through the *registered* admin, not `Model.objects.create()` and not
    `SampleChildAdmin` instantiated by hand.

    The dataset a specimen belongs to defaults to PRIVATE (D-019 in the dataset
    story), and `SampleChildAdmin`'s `dataset` field only offers the choices
    `Dataset`'s privacy-first default manager returns - the same restriction
    `DatasetAdmin.get_queryset()` works around for the dataset changelist itself, not
    fixed here since it is outside this story's named scope (see the completion
    report's `concerns`). Every fixture below uses a PUBLIC dataset so the base
    change form saves.
    """

    @staticmethod
    def _base_form_data(sample):
        return {
            "name": sample.name,
            "dataset": sample.dataset.pk,
            "local_id": sample.local_id or "",
            "status": "unknown",
            "rock_type": sample.rock_type,
            "collection_date": sample.collection_date,
            "descriptions-TOTAL_FORMS": "0",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            "dates-TOTAL_FORMS": "0",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "contributors-contribution-content_type-object_id-TOTAL_FORMS": "0",
            "contributors-contribution-content_type-object_id-INITIAL_FORMS": "0",
            "contributors-contribution-content_type-object_id-MIN_NUM_FORMS": "0",
            "contributors-contribution-content_type-object_id-MAX_NUM_FORMS": "1000",
            "related_samples-TOTAL_FORMS": "0",
            "related_samples-INITIAL_FORMS": "0",
            "related_samples-MIN_NUM_FORMS": "0",
            "related_samples-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

    def _change_url(self, sample):
        return reverse("admin:fairdm_demo_rocksample_change", args=[sample.pk])

    def test_description_can_be_added_from_the_specimens_own_page(self, admin_client):
        sample = RockSampleFactory(dataset=DatasetFactory(visibility=Visibility.PUBLIC))
        data = self._base_form_data(sample)
        data.update(
            {
                "descriptions-TOTAL_FORMS": "1",
                "descriptions-0-related": sample.pk,
                "descriptions-0-type": "SampleCollection",
                "descriptions-0-value": "Added inline.",
            }
        )

        response = admin_client.post(self._change_url(sample), data=data)

        assert response.status_code == 302, (
            "A 200 here means the formset rejected the submission - check "
            "the change form's error list."
        )
        assert SampleDescription.objects.filter(
            related=sample, type="SampleCollection", value="Added inline."
        ).exists()

    def test_date_can_be_added_from_the_specimens_own_page(self, admin_client):
        sample = RockSampleFactory(dataset=DatasetFactory(visibility=Visibility.PUBLIC))
        data = self._base_form_data(sample)
        data.update(
            {
                "dates-TOTAL_FORMS": "1",
                "dates-0-related": sample.pk,
                "dates-0-type": "Collected",
                "dates-0-value": "2024-01-15",
            }
        )

        response = admin_client.post(self._change_url(sample), data=data)

        assert response.status_code == 302, (
            "A 200 here means the formset rejected the submission - check "
            "the change form's error list."
        )
        assert SampleDate.objects.filter(related=sample, type="Collected").exists()

    def test_identifier_can_be_added_from_the_specimens_own_page(self, admin_client):
        sample = RockSampleFactory(dataset=DatasetFactory(visibility=Visibility.PUBLIC))
        data = self._base_form_data(sample)
        data.update(
            {
                "identifiers-TOTAL_FORMS": "1",
                "identifiers-0-related": sample.pk,
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1234/inline-test",
            }
        )

        response = admin_client.post(self._change_url(sample), data=data)

        assert response.status_code == 302, (
            "A 200 here means the formset rejected the submission - check "
            "the change form's error list."
        )
        assert SampleIdentifier.objects.filter(
            related=sample, type="DOI", value="10.1234/inline-test"
        ).exists()

    def test_contribution_can_be_added_from_the_specimens_own_page(
        self, admin_client
    ):
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.factories import PersonFactory
        from research_vocabs.models import Concept

        sample = RockSampleFactory(dataset=DatasetFactory(visibility=Visibility.PUBLIC))
        contributor = PersonFactory()
        role = Concept.objects.filter(
            vocabulary__name="fairdm-roles", name="Collection"
        ).first()
        assert role is not None

        data = self._base_form_data(sample)
        prefix = "contributors-contribution-content_type-object_id"
        data.update(
            {
                f"{prefix}-TOTAL_FORMS": "1",
                f"{prefix}-0-contributor": contributor.pk,
                f"{prefix}-0-roles": [role.pk],
            }
        )

        response = admin_client.post(self._change_url(sample), data=data)

        assert response.status_code == 302, (
            "A 200 here means the formset rejected the submission - check "
            "the change form's error list."
        )
        assert Contribution.objects.filter(
            object_id=str(sample.pk), contributor=contributor
        ).exists()

    def test_provenance_link_can_be_added_from_the_specimens_own_page(
        self, admin_client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        parent = RockSampleFactory(dataset=dataset, name="Parent Sample")
        child = RockSampleFactory(dataset=dataset, name="Child Sample")

        data = self._base_form_data(child)
        data.update(
            {
                "related_samples-TOTAL_FORMS": "1",
                "related_samples-0-source": child.pk,
                "related_samples-0-type": "child_of",
                "related_samples-0-target": parent.pk,
            }
        )

        response = admin_client.post(self._change_url(child), data=data)

        assert response.status_code == 302, (
            "A 200 here means the formset rejected the submission - check "
            "the change form's error list."
        )
        assert SampleRelation.objects.filter(source=child, target=parent).exists()

    def test_the_admin_registered_for_sample_is_the_polymorphic_parent(self):
        """T089: the entry `admin.site` actually holds for `Sample` is the
        polymorphic parent admin - it carries no inlines of its own; editing (and
        therefore the inlines) is delegated entirely to the registered specimen
        type's own admin, asserted next."""
        assert isinstance(admin.site._registry[Sample], SampleParentAdmin)

    def test_a_registered_specimen_types_admin_carries_the_inlines(self):
        """T089: the admin actually registered for a concrete specimen type -
        `admin.site._registry[RockSample]` - carries the inlines, not only the
        `SampleChildAdmin` class it inherits from."""
        registered_admin = admin.site._registry[RockSample]

        inline_names = {inline.__name__ for inline in registered_admin.inlines}

        assert inline_names == {
            "SampleDescriptionInline",
            "SampleDateInline",
            "SampleIdentifierInline",
            "SampleContributionInline",
            "SampleRelationInline",
        }


@pytest.mark.django_db
class TestSampleAdminInlineLimits:
    """T084/FR-039: the rows each inline editor offers are bounded by the number of
    types its vocabulary contains, and the bound moves when the vocabulary does."""

    def test_description_inline_max_num_matches_vocabulary_size(self, admin_user):
        vocabulary_size = len(SampleDescription.VOCABULARY.values)

        request = RequestFactory().get("/")
        request.user = admin_user
        inline = SampleDescriptionInline(Sample, AdminSite())
        formset = inline.get_formset(request)

        assert formset.max_num == vocabulary_size

    def test_date_inline_max_num_matches_vocabulary_size(self, admin_user):
        vocabulary_size = len(SampleDate.VOCABULARY.values)

        request = RequestFactory().get("/")
        request.user = admin_user
        inline = SampleDateInline(Sample, AdminSite())
        formset = inline.get_formset(request)

        assert formset.max_num == vocabulary_size

    def test_identifier_inline_max_num_matches_vocabulary_size(self, admin_user):
        vocabulary_size = len(SampleIdentifier.VOCABULARY.values)

        request = RequestFactory().get("/")
        request.user = admin_user
        inline = SampleIdentifierInline(Sample, AdminSite())
        formset = inline.get_formset(request)

        assert formset.max_num == vocabulary_size

    def test_description_inline_bound_moves_when_the_vocabulary_does(
        self, admin_user, monkeypatch
    ):
        request = RequestFactory().get("/")
        request.user = admin_user
        inline = SampleDescriptionInline(Sample, AdminSite())
        original_max_num = inline.get_formset(request).max_num

        monkeypatch.setattr(
            SampleDescription.VOCABULARY, "_choices", [("A", "A"), ("B", "B")]
        )

        shrunk_max_num = inline.get_formset(request).max_num

        assert shrunk_max_num == 2
        assert shrunk_max_num != original_max_num

    def test_date_inline_bound_moves_when_the_vocabulary_does(
        self, admin_user, monkeypatch
    ):
        request = RequestFactory().get("/")
        request.user = admin_user
        inline = SampleDateInline(Sample, AdminSite())
        original_max_num = inline.get_formset(request).max_num

        monkeypatch.setattr(SampleDate.VOCABULARY, "_choices", [("A", "A")])

        shrunk_max_num = inline.get_formset(request).max_num

        assert shrunk_max_num == 1
        assert shrunk_max_num != original_max_num

    def test_identifier_inline_bound_moves_when_the_vocabulary_does(
        self, admin_user, monkeypatch
    ):
        request = RequestFactory().get("/")
        request.user = admin_user
        inline = SampleIdentifierInline(Sample, AdminSite())
        original_max_num = inline.get_formset(request).max_num

        monkeypatch.setattr(
            SampleIdentifier.VOCABULARY,
            "_choices",
            [("A", "A"), ("B", "B"), ("C", "C")],
        )

        grown_max_num = inline.get_formset(request).max_num

        assert grown_max_num == 3
        assert grown_max_num != original_max_num


@pytest.mark.django_db
class TestSampleAdminTypeColumn:
    """T085/FR-039: the changelist names the specimen type of each row."""

    def test_the_changelist_names_each_rows_specimen_type(self, admin_client):
        RockSampleFactory(name="A Rock")
        WaterSampleFactory(name="A Water Sample")

        url = reverse("admin:sample_sample_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert str(RockSample._meta.verbose_name) in content
        assert str(WaterSample._meta.verbose_name) in content


@pytest.mark.django_db
class TestSampleAdminReadonly:
    """T086/FR-043: the generated identifier and the timestamps are presented as
    unchangeable, asserted through a rendered admin form's actual editable field set
    rather than by checking that a name appears in `readonly_fields` - for both the
    registered parent admin's change view and a registered specimen type's own."""

    def test_absent_from_editable_fields_through_a_registered_specimen_type(
        self, admin_client
    ):
        sample = RockSampleFactory()
        url = reverse("admin:fairdm_demo_rocksample_change", args=[sample.pk])

        response = admin_client.get(url)

        assert response.status_code == 200
        editable_fields = response.context["adminform"].form.fields
        assert "uuid" not in editable_fields
        assert "added" not in editable_fields
        assert "modified" not in editable_fields
        # Still displayed to the user, just not as an editable input.
        assert sample.uuid in response.content.decode()

    def test_absent_from_editable_fields_through_the_registered_parent_admin(
        self, admin_client
    ):
        sample = RockSampleFactory()
        url = reverse("admin:sample_sample_change", args=[sample.pk])

        response = admin_client.get(url)

        assert response.status_code == 200
        editable_fields = response.context["adminform"].form.fields
        assert "uuid" not in editable_fields
        assert "added" not in editable_fields
        assert "modified" not in editable_fields
        assert sample.uuid in response.content.decode()


@pytest.mark.django_db
class TestEveryTypeGetsTheInlines:
    """T087/FR-039: every registered specimen type offers the same inline editors."""

    def test_every_registered_specimen_type_carries_the_same_inlines(self):
        expected = {inline.__name__ for inline in SampleChildAdmin.inlines}

        for model in registry.samples:
            registered_admin = admin.site._registry[model]
            actual = {inline.__name__ for inline in registered_admin.inlines}
            assert actual == expected, model


@pytest.mark.django_db
class TestSampleAdminConfiguration:
    """Tests for general admin configuration."""

    def test_list_display_configured(self, sample_admin):
        """Test that list_display shows appropriate fields."""
        assert "name" in sample_admin.list_display
        assert "dataset" in sample_admin.list_display
        assert "status" in sample_admin.list_display
        assert "added" in sample_admin.list_display

    def test_search_fields_configured(self, sample_admin):
        """Test that search_fields includes name, local_id, uuid."""
        assert "name" in sample_admin.search_fields
        assert "local_id" in sample_admin.search_fields
        assert "uuid" in sample_admin.search_fields

    def test_readonly_fields_configured(self, sample_admin):
        """Test that readonly fields include uuid and timestamps."""
        assert "uuid" in sample_admin.readonly_fields
        assert "added" in sample_admin.readonly_fields
        assert "modified" in sample_admin.readonly_fields

    def test_fieldsets_configured(self, sample_admin):
        """Test that base_fieldsets are properly configured for polymorphic admin."""
        # Polymorphic admin uses base_fieldsets instead of fieldsets
        assert hasattr(sample_admin, "base_fieldsets")
        assert sample_admin.base_fieldsets is not None
        assert len(sample_admin.base_fieldsets) >= 2

    def test_sample_admin_is_configured_for_inheritance(self, sample_admin):
        """Test that SampleAdmin is designed for inheritance by custom classes."""
        # SampleAdmin should have inlines configured
        assert len(sample_admin.inlines) > 0
        # SampleAdmin should have search configured
        assert len(sample_admin.search_fields) > 0
        # SampleAdmin should have list display configured
        assert len(sample_admin.list_display) > 0


@pytest.mark.django_db
class TestSampleAdminReachesPrivateDatasets:
    """A specimen in a private dataset can be edited.

    The dataset field's choices come from the privacy-first default manager
    unless the admin says otherwise, so a specimen belonging to a private
    dataset could be opened and then refused on save — its own dataset was
    not among the choices. The administrative interface is where a portal is
    repaired, so it has to reach the records that need repairing.
    """

    def test_the_dataset_field_offers_a_private_dataset(self, rf, admin_user):
        from fairdm.factories import DatasetFactory
        from fairdm.utils.choices import Visibility
        from fairdm_demo.factories import RockSampleFactory

        private = DatasetFactory(visibility=Visibility.PRIVATE)
        sample = RockSampleFactory(dataset=private)

        request = rf.get("/")
        request.user = admin_user
        model_admin = admin.site._registry[type(sample)]
        form = model_admin.get_form(request, sample)()

        assert private in form.fields["dataset"].queryset

    def test_a_specimen_in_a_private_dataset_validates(self, rf, admin_user):
        from fairdm.factories import DatasetFactory
        from fairdm.utils.choices import Visibility
        from fairdm_demo.factories import RockSampleFactory

        private = DatasetFactory(visibility=Visibility.PRIVATE)
        sample = RockSampleFactory(dataset=private)

        request = rf.get("/")
        request.user = admin_user
        model_admin = admin.site._registry[type(sample)]
        form_class = model_admin.get_form(request, sample)
        form = form_class(
            data={
                "name": sample.name,
                "dataset": private.pk,
                "status": "unknown",
                "rock_type": sample.rock_type,
                "collection_date": sample.collection_date,
            },
            instance=sample,
        )

        assert "dataset" not in form.errors
