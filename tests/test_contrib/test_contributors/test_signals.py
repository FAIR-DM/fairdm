"""Tests for the email_confirmed signal handler."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def unclaimed_person_with_email(db):
    from fairdm.contrib.contributors.models import Person

    person = Person.objects.create_unclaimed(first_name="Signal", last_name="Test")
    person.email = "signal_test@example.com"
    person.save()
    return person


class TestHandleEmailConfirmed:
    def test_email_confirmed_triggers_claim_when_mandatory(
        self, db, unclaimed_person_with_email, settings
    ):
        from allauth.account.models import EmailAddress
        from allauth.account.signals import email_confirmed

        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"

        email_address = MagicMock(spec=EmailAddress)
        email_address.email = "signal_test@example.com"

        with patch("fairdm.contrib.contributors.signals.claim_via_email") as mock_claim:
            mock_claim.return_value = unclaimed_person_with_email
            email_confirmed.send(
                sender=EmailAddress,
                request=MagicMock(),
                email_address=email_address,
            )
            mock_claim.assert_called_once_with(unclaimed_person_with_email)

    def test_email_confirmed_no_op_when_not_mandatory(
        self, db, unclaimed_person_with_email, settings
    ):
        from allauth.account.models import EmailAddress
        from allauth.account.signals import email_confirmed

        settings.ACCOUNT_EMAIL_VERIFICATION = "optional"

        email_address = MagicMock(spec=EmailAddress)
        email_address.email = "signal_test@example.com"

        with patch("fairdm.contrib.contributors.signals.claim_via_email") as mock_claim:
            email_confirmed.send(
                sender=EmailAddress,
                request=MagicMock(),
                email_address=email_address,
            )
            mock_claim.assert_not_called()

    def test_email_confirmed_no_op_when_no_matching_unclaimed_person(
        self, db, settings
    ):
        from allauth.account.models import EmailAddress
        from allauth.account.signals import email_confirmed

        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"

        email_address = MagicMock(spec=EmailAddress)
        email_address.email = "no_such_person@example.com"

        with patch("fairdm.contrib.contributors.signals.claim_via_email") as mock_claim:
            email_confirmed.send(
                sender=EmailAddress,
                request=MagicMock(),
                email_address=email_address,
            )
            mock_claim.assert_not_called()
