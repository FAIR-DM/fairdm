"""Tests for the allauth signup forms."""

import pytest
from allauth.account.forms import default_token_generator
from allauth.account.models import EmailAddress
from allauth.account.utils import user_pk_to_url_str
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

    def test_a_sign_up_does_not_claim_a_deactivated_profile_holding_the_identifier(
        self, orcid_signup
    ):
        existing = PersonFactory(
            email="old@example.org", is_active=False, is_claimed=False
        )
        ContributorIdentifier.objects.create(
            related=existing, value=ORCID_UID, type_id=ORCID
        )

        submit_orcid_signup(orcid_signup)

        existing.refresh_from_db()
        assert existing.is_claimed is False

    @pytest.mark.parametrize("verification", ["none", "optional", "mandatory"])
    def test_a_person_a_sign_up_creates_is_claimed_from_the_start(
        self, orcid_signup, settings, rf, verification
    ):
        settings.ACCOUNT_EMAIL_VERIFICATION = verification
        request = rf.get("/")
        request.session = {}
        provider = SocialApp.objects.get().get_provider(request)
        pending = provider.sociallogin_from_response(
            request, {"orcid-identifier": {"path": ORCID_UID}}
        )
        session = orcid_signup.session
        session["socialaccount_sociallogin"] = pending.serialize()
        session.save()

        submit_orcid_signup(orcid_signup)

        person = Person.objects.get(email=SHARED_EMAIL)
        assert person.is_claimed is True
        assert person.identifiers.get(type_id=ORCID).value == ORCID_UID


class TestUserTokenForm:
    def follow_reset_link(self, client, person):
        url = reverse(
            "account_reset_password_from_key",
            kwargs={
                "uidb36": user_pk_to_url_str(person),
                "key": default_token_generator.make_token(person),
            },
        )
        response = client.get(url, follow=True)
        return client.post(
            response.redirect_chain[-1][0] if response.redirect_chain else url,
            {"password1": "a-new-Passw0rd!", "password2": "a-new-Passw0rd!"},
        )

    def test_invited_profile_gets_no_password_from_a_sent_link(self, client, db):
        person = PersonFactory(email="invited@example.com")

        response = self.follow_reset_link(client, person)

        person.refresh_from_db()
        assert person.has_usable_password() is False
        assert response.context["token_fail"] is True

    def test_claimed_account_sets_a_password_from_the_link(self, client, db):
        person = PersonFactory(email="claimed@example.com", is_claimed=True)

        response = self.follow_reset_link(client, person)

        person.refresh_from_db()
        assert response.url == reverse("account_reset_password_from_key_done")
        assert person.check_password("a-new-Passw0rd!") is True
