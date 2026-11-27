"""Integration tests for Measurement admin interface."""

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import reverse

from fairdm.core.measurement.admin import MeasurementChildAdmin, MeasurementParentAdmin
from fairdm.core.measurement.models import (
    Measurement,
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.factories import PersonFactory
from fairdm.registry import registry
from tests.registry_models.models import ConcreteMeasurement

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="admin123",
    )


@pytest.fixture
def measurement_admin():
    return MeasurementChildAdmin(Measurement, AdminSite())


@pytest.fixture
def measurement_parent_admin():
    return MeasurementParentAdmin(Measurement, AdminSite())


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.mark.django_db
class TestMeasurementContributionInlineRoleVocabulary:
    @staticmethod
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
        self, admin_client, sample
    ):
        from demo.models import XRFMeasurement
        from fairdm.contrib.contributors.models import Contribution

        xrf = XRFMeasurement.objects.create(
            name="XRF Test",
            sample=sample,
            dataset=sample.dataset,
            element="Si",
            concentration_ppm=250000.0,
        )
        contributor = PersonFactory(is_active=True)
        contribution = xrf.contributors.create(contributor=contributor)
        off_vocabulary_role = self._off_vocabulary_role()

        prefix = "contributors-contribution-content_type-object_id"
        data = {
            "element": "Si",
            "concentration_ppm": "250000.00",
            "detection_limit_ppm": "",
            "instrument_model": "",
            "measurement_conditions": "",
            "descriptions-TOTAL_FORMS": "0",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "4",
            "dates-TOTAL_FORMS": "0",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "2",
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1",
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "1",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-id": contribution.pk,
            f"{prefix}-0-contributor": contributor.pk,
            f"{prefix}-0-roles": [off_vocabulary_role.pk],
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(
            reverse("admin:demo_xrfmeasurement_change", args=[xrf.pk]),
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

    def test_the_roles_field_does_not_offer_the_off_vocabulary_concept(
        self, admin_user, sample
    ):
        from demo.models import XRFMeasurement

        xrf = XRFMeasurement.objects.create(
            name="XRF Test",
            sample=sample,
            dataset=sample.dataset,
            element="Si",
            concentration_ppm=250000.0,
        )
        off_vocabulary_role = self._off_vocabulary_role()

        request = RequestFactory().get("/")
        request.user = admin_user
        model_admin = admin.site._registry[type(xrf)]
        contribution_inline = next(
            inline
            for inline in model_admin.get_inline_instances(request, xrf)
            if inline.__class__.__name__ == "MeasurementContributionInline"
        )
        formset_class = contribution_inline.get_formset(request, xrf)

        roles = formset_class.form().fields["roles"]
        with pytest.raises(ValidationError):
            roles.clean([off_vocabulary_role.uri])


@pytest.mark.django_db
class TestMeasurementAdminInlineRowCaps:
    def test_description_inline_row_cap_matches_vocabulary(self):
        from fairdm.core.measurement.admin import MeasurementDescriptionInline

        assert MeasurementDescriptionInline(Measurement, admin.site).get_max_num(
            None
        ) == len(
            [concept.uri for concept in MeasurementDescription.get_type_concepts()]
        )

    def test_date_inline_row_cap_matches_vocabulary(self):
        from fairdm.core.measurement.admin import MeasurementDateInline

        assert MeasurementDateInline(Measurement, admin.site).get_max_num(None) == len(
            [concept.uri for concept in MeasurementDate.get_type_concepts()]
        )

    def test_identifier_inline_row_cap_matches_vocabulary(self):
        from fairdm.core.measurement.admin import MeasurementIdentifierInline

        assert MeasurementIdentifierInline(Measurement, admin.site).get_max_num(
            None
        ) == len([concept.uri for concept in MeasurementIdentifier.get_type_concepts()])

    def test_contribution_inline_is_not_row_capped(self):
        from fairdm.core.measurement.admin import MeasurementContributionInline

        assert MeasurementContributionInline.max_num is None


@pytest.mark.django_db
class TestMeasurementAdminTypeColumn:
    def test_measurement_type_column_names_the_real_type(
        self, measurement_admin, xrf_measurement, icp_ms_measurement
    ):
        assert (
            measurement_admin.measurement_type(xrf_measurement)
            == type(xrf_measurement)._meta.verbose_name
        )
        assert (
            measurement_admin.measurement_type(icp_ms_measurement)
            == type(icp_ms_measurement)._meta.verbose_name
        )
        assert measurement_admin.measurement_type(
            xrf_measurement
        ) != measurement_admin.measurement_type(icp_ms_measurement)


class TestChildModelDiscoveryReadsTheRegistry:
    def test_child_models_reads_the_registry(
        self, measurement_parent_admin, monkeypatch
    ):
        sentinel = [ConcreteMeasurement]
        monkeypatch.setattr(
            type(registry), "measurements", property(lambda self: sentinel)
        )

        assert measurement_parent_admin.get_child_models() == sentinel


@pytest.mark.django_db
class TestAdminRefusesTheBaseMeasurement:
    def test_admin_refuses_the_base_content_type(self, admin_client):
        ct = ContentType.objects.get_for_model(Measurement)
        response = admin_client.get(
            reverse("admin:measurement_measurement_add"), {"ct_id": ct.pk}
        )

        assert response.status_code == 403
