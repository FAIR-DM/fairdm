"""Integration tests for Sample admin interface."""

from datetime import timedelta

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from demo.factories import RockSampleFactory, WaterSampleFactory
from demo.models import RockSample, WaterSample
from fairdm.core.dataset.models import Dataset
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
from fairdm.core.vocabularies import (
    CONTRIBUTOR_ROLES,
    DATE_TYPES,
    DESCRIPTION_TYPES,
    IDENTIFIER_TYPES,
    SAMPLE_STATUS,
)
from fairdm.factories.core import DatasetFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility


def _result_pks(response):
    """The primary keys the changelist actually matched - read off the `ChangeList`."""
    return {obj.pk for obj in response.context["cl"].result_list}


@pytest.mark.django_db
class TestSampleAdminFilters:
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


@pytest.mark.django_db
class TestSampleDatasetListFilterOrdering:
    def test_falls_back_to_the_datasets_own_default_ordering(self):
        from fairdm.core.sample.admin import SampleDatasetListFilter

        early = DatasetFactory()
        late = DatasetFactory()
        # Set the timestamps the ordering reads, so two rows created back to back cannot tie.
        Dataset.objects.filter(pk=early.pk).update(
            modified=timezone.now() - timedelta(days=2)
        )
        Dataset.objects.filter(pk=late.pk).update(
            modified=timezone.now() - timedelta(days=1)
        )

        field = Sample._meta.get_field("dataset")
        request = RequestFactory().get("/")
        model_admin = admin.site._registry[Sample]
        list_filter = SampleDatasetListFilter.__new__(SampleDatasetListFilter)

        choices = list_filter.field_choices(field, request, model_admin)
        pks_in_order = [pk for pk, _label in choices]

        # Dataset.Meta.ordering = ["-modified"]: the more recently modified "late" dataset sorts
        # first. An empty order_by() would return ascending pk, "early" before "late".
        assert pks_in_order.index(late.pk) < pks_in_order.index(early.pk)


@pytest.mark.django_db
class TestSampleAdminInlines:
    @staticmethod
    def _base_form_data(sample):
        return {
            "name": sample.name,
            "dataset": sample.dataset.pk,
            "local_id": sample.local_id or "",
            "status": f"{SAMPLE_STATUS}/unknown",
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
        return reverse("admin:demo_rocksample_change", args=[sample.pk])

    def test_every_inline_can_be_saved_from_the_specimens_own_page(self, admin_client):
        from controlled_vocabularies.models import Record

        from fairdm.contrib.contributors.models import Contribution
        from fairdm.factories import PersonFactory

        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        sample = RockSampleFactory(dataset=dataset)
        parent = RockSampleFactory(dataset=dataset)
        contributor = PersonFactory(is_active=True)
        role = Record.objects.get(uri=f"{CONTRIBUTOR_ROLES}/collection")
        prefix = "contributors-contribution-content_type-object_id"

        data = self._base_form_data(sample)
        data.update(
            {
                "descriptions-TOTAL_FORMS": "1",
                "descriptions-0-related": sample.pk,
                "descriptions-0-type": f"{DESCRIPTION_TYPES}/sample-collection",
                "descriptions-0-value": "Added inline.",
                "dates-TOTAL_FORMS": "1",
                "dates-0-related": sample.pk,
                "dates-0-type": f"{DATE_TYPES}/collected",
                "dates-0-value": "2024-01-15",
                "identifiers-TOTAL_FORMS": "1",
                "identifiers-0-related": sample.pk,
                "identifiers-0-type": f"{IDENTIFIER_TYPES}/doi",
                "identifiers-0-value": "10.1234/inline-test",
                f"{prefix}-TOTAL_FORMS": "1",
                f"{prefix}-0-contributor": contributor.pk,
                f"{prefix}-0-roles": [role.uri],
                "related_samples-TOTAL_FORMS": "1",
                "related_samples-0-source": sample.pk,
                "related_samples-0-type": "child_of",
                "related_samples-0-target": parent.pk,
            }
        )

        response = admin_client.post(self._change_url(sample), data=data)

        assert response.status_code == 302, (
            "A 200 here means a formset rejected the submission - check "
            "the change form's error list."
        )
        assert sample.descriptions.filter(value="Added inline.").exists()
        assert sample.dates.filter(type_id=f"{DATE_TYPES}/collected").exists()
        assert sample.identifiers.filter(value="10.1234/inline-test").exists()
        assert Contribution.objects.filter(
            object_id=str(sample.pk), contributor=contributor
        ).exists()
        assert SampleRelation.objects.filter(source=sample, target=parent).exists()

    def test_the_admin_registered_for_sample_is_the_polymorphic_parent(self):
        assert isinstance(admin.site._registry[Sample], SampleParentAdmin)


@pytest.mark.django_db
class TestSampleContributionInlineRoleVocabulary:
    @staticmethod
    # An off-vocabulary role reaches the m2m_changed receiver, which refuses it
    # uncaught inside Django's atomic block, so the change request 500s.
    def _off_vocabulary_role():
        from controlled_vocabularies.models import ConceptScheme, Record

        vocabulary, _ = ConceptScheme.objects.get_or_create(
            uri="https://example.com/vocabularies/not-fairdm-roles",
            defaults={
                "default_language": "en",
                "data": {
                    "skos:prefLabel": [
                        {"@value": "Not FairDM Roles", "@language": "en"}
                    ]
                },
            },
        )
        concept, _ = Record.objects.get_or_create(
            uri="https://example.com/vocabularies/not-fairdm-roles#outsider",
            defaults={
                "scheme": vocabulary,
                "type": Record.Type.CONCEPT,
                "data": {"skos:prefLabel": [{"@value": "Outsider", "@language": "en"}]},
            },
        )
        return concept

    def test_posting_an_off_vocabulary_role_is_a_form_error_not_a_500(
        self, admin_client
    ):
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.factories import PersonFactory

        sample = RockSampleFactory(dataset=DatasetFactory(visibility=Visibility.PUBLIC))
        contributor = PersonFactory(is_active=True)
        contribution = sample.contributors.create(contributor=contributor)
        off_vocabulary_role = self._off_vocabulary_role()

        data = TestSampleAdminInlines._base_form_data(sample)
        prefix = "contributors-contribution-content_type-object_id"
        data.update(
            {
                f"{prefix}-TOTAL_FORMS": "1",
                f"{prefix}-INITIAL_FORMS": "1",
                f"{prefix}-0-id": contribution.pk,
                f"{prefix}-0-contributor": contributor.pk,
                f"{prefix}-0-roles": [off_vocabulary_role.pk],
            }
        )

        response = admin_client.post(
            reverse("admin:demo_rocksample_change", args=[sample.pk]),
            data=data,
        )

        assert response.status_code == 200, (
            "A redirect here means the off-vocabulary role was accepted; a 500 "
            "means the m2m_changed receiver raised uncaught instead of the "
            "admin field rejecting the choice."
        )
        contribution_formset = next(
            admin_formset.formset
            for admin_formset in response.context["inline_admin_formsets"]
            if admin_formset.formset.prefix == prefix
        )
        assert contribution_formset.errors and any(contribution_formset.errors), (
            contribution_formset.errors
        )
        assert not Contribution.objects.get(pk=contribution.pk).roles.exists()


@pytest.mark.django_db
class TestSampleAdminInlineLimits:
    def test_each_inlines_bound_matches_its_vocabulary_size(self, admin_user):
        request = RequestFactory().get("/")
        request.user = admin_user
        wrong = {}
        for inline_class, model in [
            (SampleDescriptionInline, SampleDescription),
            (SampleDateInline, SampleDate),
            (SampleIdentifierInline, SampleIdentifier),
        ]:
            inline = inline_class(Sample, AdminSite())
            expected = len(model.get_type_concepts())
            actual = inline.get_formset(request).max_num
            if actual != expected:
                wrong[inline_class.__name__] = (actual, expected)

        assert not wrong, wrong


@pytest.mark.django_db
class TestSampleAdminTypeColumn:
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
    def test_absent_from_editable_fields_through_a_registered_specimen_type(
        self, admin_client
    ):
        sample = RockSampleFactory()
        url = reverse("admin:demo_rocksample_change", args=[sample.pk])

        response = admin_client.get(url)

        assert response.status_code == 200
        editable_fields = response.context["adminform"].form.fields
        assert "uuid" not in editable_fields
        assert "added" not in editable_fields
        assert "modified" not in editable_fields
        # Still displayed to the user, just not as an editable input.
        assert sample.uuid in response.content.decode()


@pytest.mark.django_db
class TestEveryTypeGetsTheInlines:
    def test_every_registered_specimen_type_carries_the_same_inlines(self):
        expected = {inline.__name__ for inline in SampleChildAdmin.inlines}

        for model in registry.samples:
            registered_admin = admin.site._registry[model]
            actual = {inline.__name__ for inline in registered_admin.inlines}
            assert actual == expected, model


@pytest.mark.django_db
class TestSampleAdminReachesPrivateDatasets:
    # The dataset field's default manager hides private datasets, so a specimen in one
    # could be opened but not saved.
    def test_a_specimen_in_a_private_dataset_validates(self, rf, admin_user):
        from demo.factories import RockSampleFactory
        from fairdm.factories import DatasetFactory
        from fairdm.utils.choices import Visibility

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
                "status": f"{SAMPLE_STATUS}/unknown",
                "rock_type": sample.rock_type,
                "collection_date": sample.collection_date,
            },
            instance=sample,
        )

        assert "dataset" not in form.errors
