"""Tests for the claiming service functions."""

from unittest.mock import MagicMock

import pytest

from fairdm.contrib.contributors.exceptions import ClaimingError
from fairdm.contrib.contributors.models import ClaimingAuditLog, Person


@pytest.fixture
def unclaimed_person(db):
    return Person.objects.create_unclaimed(first_name="Ghost", last_name="User")


@pytest.fixture
def claimed_person(db):
    from fairdm.factories import PersonFactory

    p = PersonFactory(email="claimed@example.com", is_active=True, is_claimed=True)
    p.set_password("testpass123")
    p.save()
    return p


@pytest.fixture
def banned_person(db):
    from fairdm.factories import PersonFactory

    p = PersonFactory(email=None, is_active=False, is_claimed=False)
    return p


@pytest.fixture
def mock_sociallogin(unclaimed_person):
    sl = MagicMock()
    sl.user = unclaimed_person
    sl.account.uid = "0000-0001-2345-6789"
    sl.account.provider = "orcid"
    return sl


class TestClaimViaOrcid:
    def test_happy_path_activates_and_claims_person(
        self, db, unclaimed_person, mock_sociallogin
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_orcid

        result = claim_via_orcid(unclaimed_person, mock_sociallogin)

        unclaimed_person.refresh_from_db()
        assert result.pk == unclaimed_person.pk
        assert unclaimed_person.is_claimed is True
        assert unclaimed_person.is_active is True

    def test_happy_path_connects_social_account(
        self, db, unclaimed_person, mock_sociallogin
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_orcid

        claim_via_orcid(unclaimed_person, mock_sociallogin)

        mock_sociallogin.connect.assert_called_once()

    def test_already_claimed_raises_claiming_error(
        self, db, claimed_person, mock_sociallogin
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_orcid

        with pytest.raises(ClaimingError):
            claim_via_orcid(claimed_person, mock_sociallogin)

    def test_banned_person_raises_claiming_error(
        self, db, banned_person, mock_sociallogin
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_orcid

        with pytest.raises(ClaimingError):
            claim_via_orcid(banned_person, mock_sociallogin)

    def test_audit_log_written_on_success(self, db, unclaimed_person, mock_sociallogin):
        from fairdm.contrib.contributors.services.claiming import claim_via_orcid

        before_count = ClaimingAuditLog.objects.count()
        claim_via_orcid(unclaimed_person, mock_sociallogin)

        assert ClaimingAuditLog.objects.count() == before_count + 1
        log = ClaimingAuditLog.objects.latest("timestamp")
        assert log.method == "orcid"
        assert log.success is True
        assert log.source_person_id == unclaimed_person.pk

    def test_failed_claim_logged_with_failure_reason(
        self, db, claimed_person, mock_sociallogin
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_orcid

        before_count = ClaimingAuditLog.objects.count()
        with pytest.raises(ClaimingError):
            claim_via_orcid(claimed_person, mock_sociallogin)

        assert ClaimingAuditLog.objects.count() == before_count + 1
        log = ClaimingAuditLog.objects.latest("timestamp")
        assert log.success is False
        assert log.failure_reason != ""


class TestClaimViaEmail:
    def test_happy_path_claims_person(self, db, unclaimed_person, settings):
        from fairdm.contrib.contributors.services.claiming import claim_via_email

        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        result = claim_via_email(unclaimed_person)

        unclaimed_person.refresh_from_db()
        assert result.pk == unclaimed_person.pk
        assert unclaimed_person.is_claimed is True
        assert unclaimed_person.is_active is True

    def test_mandatory_verification_guard_silent_noop(
        self, db, unclaimed_person, settings
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_email

        settings.ACCOUNT_EMAIL_VERIFICATION = "optional"

        result = claim_via_email(unclaimed_person)

        unclaimed_person.refresh_from_db()
        assert unclaimed_person.is_claimed is False
        assert result is None

    def test_already_claimed_raises_claiming_error(self, db, claimed_person, settings):
        from fairdm.contrib.contributors.services.claiming import claim_via_email

        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        with pytest.raises(ClaimingError):
            claim_via_email(claimed_person)

    def test_banned_person_raises_claiming_error(self, db, banned_person, settings):
        from fairdm.contrib.contributors.services.claiming import claim_via_email

        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        with pytest.raises(ClaimingError):
            claim_via_email(banned_person)

    def test_audit_log_written_on_success(self, db, unclaimed_person, settings):
        from fairdm.contrib.contributors.services.claiming import claim_via_email

        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        before_count = ClaimingAuditLog.objects.count()
        claim_via_email(unclaimed_person)

        assert ClaimingAuditLog.objects.count() == before_count + 1
        log = ClaimingAuditLog.objects.latest("timestamp")
        assert log.method == "email"
        assert log.success is True

    def test_failed_claim_logged_with_failure_reason(
        self, db, claimed_person, settings
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_email

        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        before_count = ClaimingAuditLog.objects.count()
        with pytest.raises(ClaimingError):
            claim_via_email(claimed_person)

        assert ClaimingAuditLog.objects.count() == before_count + 1
        log = ClaimingAuditLog.objects.latest("timestamp")
        assert log.success is False
        assert log.failure_reason != ""


class TestClaimViaToken:
    def test_valid_token_and_user_claims_person(
        self, db, unclaimed_person, claimed_person
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_token
        from fairdm.contrib.contributors.utils.tokens import generate_claim_token

        token = generate_claim_token(unclaimed_person)
        result = claim_via_token(token, claimed_person)

        unclaimed_person.refresh_from_db()
        assert result.pk == unclaimed_person.pk
        assert unclaimed_person.is_claimed is True
        assert unclaimed_person.is_active is True

    def test_already_claimed_token_raises_claiming_error(
        self, db, unclaimed_person, claimed_person
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_token
        from fairdm.contrib.contributors.utils.tokens import generate_claim_token

        token = generate_claim_token(unclaimed_person)
        claim_via_token(token, claimed_person)
        other_person = Person.objects.create_unclaimed(
            first_name="Other", last_name="User"
        )
        other_person.email = "other@example.com"
        other_person.is_claimed = True
        other_person.save()

        with pytest.raises(ClaimingError):
            claim_via_token(token, other_person)

    def test_expired_token_raises_claiming_error(
        self, db, unclaimed_person, claimed_person, settings
    ):
        import time

        from fairdm.contrib.contributors.services.claiming import claim_via_token
        from fairdm.contrib.contributors.utils.tokens import generate_claim_token

        settings.CLAIM_TOKEN_MAX_AGE = 0
        token = generate_claim_token(unclaimed_person)
        time.sleep(0.01)

        with pytest.raises(ClaimingError):
            claim_via_token(token, claimed_person)

    def test_tampered_token_raises_claiming_error(
        self, db, unclaimed_person, claimed_person
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_token

        with pytest.raises(ClaimingError):
            claim_via_token("this.is.not.a.valid.token", claimed_person)

    def test_banned_target_person_raises_claiming_error(
        self, db, banned_person, claimed_person
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_token
        from fairdm.contrib.contributors.utils.tokens import generate_claim_token

        token = generate_claim_token(banned_person)

        with pytest.raises(ClaimingError):
            claim_via_token(token, claimed_person)

    def test_failed_claim_logged_with_failure_reason(
        self, db, unclaimed_person, claimed_person
    ):
        from fairdm.contrib.contributors.services.claiming import claim_via_token

        before_count = ClaimingAuditLog.objects.count()
        with pytest.raises(ClaimingError):
            claim_via_token("tampered.token.string", claimed_person)

        assert ClaimingAuditLog.objects.count() == before_count + 1
        log = ClaimingAuditLog.objects.latest("timestamp")
        assert log.success is False
        assert log.failure_reason != ""
