"""Tests for the email_confirmed signal handler."""

import pytest
from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed

from fairdm.contrib.contributors.models import Person

EMAIL = "signal_test@example.com"


@pytest.fixture
def unclaimed_person_with_email(db):
    person = Person.objects.create_unclaimed(first_name="Signal", last_name="Test")
    person.email = EMAIL
    person.save()
    return person


def confirm(email):
    address = EmailAddress(email=email)
    email_confirmed.send(sender=EmailAddress, request=None, email_address=address)


class TestHandleEmailConfirmed:
    def test_confirming_an_unclaimed_persons_email_claims_them(
        self, unclaimed_person_with_email, settings
    ):
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"

        confirm(EMAIL)

        unclaimed_person_with_email.refresh_from_db()
        assert unclaimed_person_with_email.is_claimed is True

    def test_confirming_an_email_claims_nobody_when_verification_is_not_mandatory(
        self, unclaimed_person_with_email, settings
    ):
        settings.ACCOUNT_EMAIL_VERIFICATION = "optional"

        confirm(EMAIL)

        unclaimed_person_with_email.refresh_from_db()
        assert unclaimed_person_with_email.is_claimed is False

    def test_confirming_an_unknown_email_leaves_other_people_unclaimed(
        self, unclaimed_person_with_email, settings
    ):
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"

        confirm("no_such_person@example.com")

        unclaimed_person_with_email.refresh_from_db()
        assert unclaimed_person_with_email.is_claimed is False

    def test_a_claim_that_fails_is_swallowed_and_leaves_the_person_unclaimed(
        self, unclaimed_person_with_email, settings
    ):
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        Person.objects.filter(pk=unclaimed_person_with_email.pk).update(is_active=False)

        confirm(EMAIL)

        unclaimed_person_with_email.refresh_from_db()
        assert unclaimed_person_with_email.is_claimed is False
