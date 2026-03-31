"""
T046 — ClaimingAuditLog model and admin registration tests.

Tests immutability, manager filter methods, and admin view loading.
"""

import pytest


@pytest.fixture
def person_a(db):
    from fairdm.factories import PersonFactory

    return PersonFactory()


@pytest.fixture
def person_b(db):
    from fairdm.factories import PersonFactory

    return PersonFactory()


@pytest.fixture
def audit_log_entry(db, person_a, person_b):
    from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod

    return ClaimingAuditLog.objects.create(
        method=ClaimMethod.TOKEN,
        source_person=person_a,
        target_person=person_b,
        success=True,
    )


class TestClaimingAuditLogImmutability:
    """Verify that ClaimingAuditLog records cannot be modified after creation."""

    def test_create_succeeds(self, db, person_a, person_b):
        from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod

        entry = ClaimingAuditLog.objects.create(
            method=ClaimMethod.ORCID,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        assert entry.pk is not None

    def test_update_raises_value_error(self, db, audit_log_entry):
        """Calling save() on an existing record should raise ValueError."""
        from fairdm.contrib.contributors.models import ClaimingAuditLog

        audit_log_entry.failure_reason = "tampered"
        with pytest.raises(ValueError, match="immutable"):
            audit_log_entry.save()

    def test_record_not_modified_on_failed_save(self, db, audit_log_entry):
        """DB record should be unchanged after a rejected save()."""
        from fairdm.contrib.contributors.models import ClaimingAuditLog

        original_reason = audit_log_entry.failure_reason
        try:
            audit_log_entry.failure_reason = "tampered"
            audit_log_entry.save()
        except ValueError:
            pass
        fresh = ClaimingAuditLog.objects.get(pk=audit_log_entry.pk)
        assert fresh.failure_reason == original_reason


class TestClaimingAuditLogManager:
    """Tests for ClaimingAuditLogManager filter methods."""

    def test_for_person_returns_related_entries(self, db, person_a, person_b):
        from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod

        entry = ClaimingAuditLog.objects.create(
            method=ClaimMethod.EMAIL,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        assert ClaimingAuditLog.objects.for_person(person_a.pk).filter(pk=entry.pk).exists()
        assert ClaimingAuditLog.objects.for_person(person_b.pk).filter(pk=entry.pk).exists()

    def test_for_person_excludes_unrelated_entries(self, db, person_a, person_b):
        from fairdm.factories import PersonFactory
        from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod

        unrelated = PersonFactory()
        entry = ClaimingAuditLog.objects.create(
            method=ClaimMethod.EMAIL,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        assert not ClaimingAuditLog.objects.for_person(unrelated.pk).filter(pk=entry.pk).exists()

    def test_failures_filter(self, db, person_a, person_b):
        from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod

        failed = ClaimingAuditLog.objects.create(
            method=ClaimMethod.TOKEN,
            source_person=person_a,
            target_person=person_b,
            success=False,
            failure_reason="expired",
        )
        succeeded = ClaimingAuditLog.objects.create(
            method=ClaimMethod.TOKEN,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        failures = ClaimingAuditLog.objects.failures()
        assert failures.filter(pk=failed.pk).exists()
        assert not failures.filter(pk=succeeded.pk).exists()

    def test_by_method_filter(self, db, person_a, person_b):
        from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod

        orcid_entry = ClaimingAuditLog.objects.create(
            method=ClaimMethod.ORCID,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        email_entry = ClaimingAuditLog.objects.create(
            method=ClaimMethod.EMAIL,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        orcid_qs = ClaimingAuditLog.objects.by_method(ClaimMethod.ORCID)
        assert orcid_qs.filter(pk=orcid_entry.pk).exists()
        assert not orcid_qs.filter(pk=email_entry.pk).exists()


class TestClaimingAuditLogAdminView:
    """Verify that the admin changelist view for ClaimingAuditLog loads correctly."""

    def test_changelist_view_returns_200(self, db, admin_client, audit_log_entry):
        from django.urls import reverse

        url = reverse("admin:contributors_claimingauditlog_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_admin_has_no_add_permission(self, db, admin_client):
        """Add URL should return 403 since we disabled add permission."""
        from django.urls import reverse

        url = reverse("admin:contributors_claimingauditlog_add")
        response = admin_client.get(url)
        assert response.status_code == 403

    def test_admin_has_no_change_permission(self, db, admin_client, audit_log_entry):
        """Change URL should return 403 since we disabled change permission."""
        from django.urls import reverse

        url = reverse("admin:contributors_claimingauditlog_change", args=[audit_log_entry.pk])
        response = admin_client.get(url)
        assert response.status_code == 403
