"""Tests for the allauth signup forms."""

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialLogin
from django.contrib.sites.models import Site
from django.urls import reverse
from waffle.testutils import override_switch

from fairdm.contrib.contributors.models import ContributorIdentifier, Person
from fairdm.core.vocabularies import ORCID
from fairdm.factories import PersonFactory

ORCID_UID = "0000-0002-1111-2222"
SHARED_EMAIL = "listed@example.org"


def submit_orcid_signup(client):
    with override_switch("allow_signup", active=True):
        return client.post(
            reverse("socialaccount_signup"),
            {"email": SHARED_EMAIL, "first_name": "Someone", "last_name": "Else"},
        )


@pytest.fixture
def orcid_signup(client, db, settings):
    """Put a pending ORCID sign-up with no matching identifier in the session."""
    settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
    app = SocialApp.objects.create(
        provider="orcid", name="ORCID", client_id="id", secret="secret"
    )
    app.sites.add(Site.objects.get_current())
    account = SocialAccount(provider="orcid", uid=ORCID_UID)
    pending = SocialLogin(
        user=Person(first_name="Someone", last_name="Else"),
        account=account,
        provider=account.get_provider(),
    )
    session = client.session
    session["socialaccount_sociallogin"] = pending.serialize()
    session.save()
    return client


@pytest.mark.django_db
class TestSocialSignupForm:
    @pytest.mark.parametrize("is_claimed", [False, True])
    def test_an_inactive_accounts_address_meets_the_email_conflict_check(
        self, orcid_signup, is_claimed
    ):
        existing = PersonFactory(
            email=SHARED_EMAIL, is_active=False, is_claimed=is_claimed
        )
        people_before = Person.objects.count()

        response = submit_orcid_signup(orcid_signup)

        assert response.status_code == 302
        assert response.url == reverse("account_email_verification_sent")
        assert not SocialAccount.objects.exists()
        assert Person.objects.count() == people_before
        existing.refresh_from_db()
        assert existing.is_active is False
        assert existing.is_claimed is is_claimed

    def test_an_inactive_accounts_secondary_address_makes_no_second_account(
        self, orcid_signup
    ):
        existing = PersonFactory(email="primary@example.org", is_active=False)
        EmailAddress.objects.create(user=existing, email=SHARED_EMAIL)
        people_before = Person.objects.count()

        response = submit_orcid_signup(orcid_signup)

        assert response.url == reverse("account_email_verification_sent")
        assert not SocialAccount.objects.exists()
        assert Person.objects.count() == people_before

    def test_a_deactivated_profile_holding_the_identifier_stays_unconnected(
        self, orcid_signup
    ):
        existing = PersonFactory(email=SHARED_EMAIL, is_active=False, is_claimed=False)
        ContributorIdentifier.objects.create(
            related=existing, value=ORCID_UID, type_id=ORCID
        )

        response = submit_orcid_signup(orcid_signup)

        assert response.url == reverse("account_email_verification_sent")
        assert not SocialAccount.objects.exists()
