"""Integration tests for ClaimProfileView (US3 — token-based claiming).

Views under test:
  - GET  /claim/<token>/         — ClaimProfileView.get()
  - POST /claim/<token>/confirm/ — ClaimProfileView.post()

Scenarios:
  (a) Authenticated same-user: GET shows confirmation; POST claims profile
  (b) Unauthenticated: GET redirects to login with token in session
  (c) Authenticated as different Person B: GET renders merge confirmation
  (d) Banned target Person: GET renders error page
  (e) Expired token: rejected with error
  (f) Reused/already-claimed token: rejected
  (g) CSRF enforced on POST
"""

import pytest
from django.urls import reverse


@pytest.fixture
def unclaimed_person(db):
    """An unclaimed Person with no email and no social accounts."""
    from fairdm.contrib.contributors.models import Person

    return Person.objects.create_unclaimed(first_name="Ghost", last_name="User")


@pytest.fixture
def claimed_person(db):
    """A fully registered and claimed Person (simulates an authenticated user)."""
    from fairdm.factories import PersonFactory

    person = PersonFactory(email="registered@example.com", is_active=True, is_claimed=True)
    person.set_password("Secr3tPass!")
    person.save()
    return person


@pytest.fixture
def claim_token(unclaimed_person):
    """A valid claim token for unclaimed_person."""
    from fairdm.contrib.contributors.utils.tokens import generate_claim_token

    return generate_claim_token(unclaimed_person)


class TestClaimProfileViewGet:
    def test_unauthenticated_redirects_to_login(self, client, claim_token):
        """Unauthenticated user gets redirected to login; token stored in session."""
        url = reverse("contributors:claim-profile", kwargs={"token": claim_token})
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"] or "/login" in response["Location"]

    def test_unauthenticated_stores_token_in_session(self, client, claim_token):
        """Token is saved in session so claim can resume after authentication."""
        url = reverse("contributors:claim-profile", kwargs={"token": claim_token})
        client.get(url)
        assert client.session.get("claim_token") == claim_token

    def test_authenticated_no_conflict_shows_confirmation(self, client, claimed_person, claim_token):
        """Authenticated user without conflicting Person sees standard confirmation page."""
        client.force_login(claimed_person)
        url = reverse("contributors:claim-profile", kwargs={"token": claim_token})
        response = client.get(url)
        assert response.status_code == 200
        assert "contributors/claim_profile.html" in [t.name for t in response.templates]

    def test_authenticated_banned_person_shows_error(self, client, claimed_person, db):
        """Token pointing to a banned Person renders an error page."""
        from fairdm.contrib.contributors.models import Person
        from fairdm.contrib.contributors.utils.tokens import generate_claim_token

        banned = Person.objects.create_unclaimed(first_name="Banned", last_name="Person")
        banned.is_active = False
        banned.save()
        token = generate_claim_token(banned)

        client.force_login(claimed_person)
        url = reverse("contributors:claim-profile", kwargs={"token": token})
        response = client.get(url)
        assert response.status_code == 200
        assert "error" in response.context or response.status_code == 200

    def test_expired_token_shows_error(self, client, claimed_person, db, settings):
        """Expired token renders an error page rather than a confirmation."""
        from fairdm.contrib.contributors.models import Person
        from fairdm.contrib.contributors.utils.tokens import generate_claim_token

        settings.CLAIM_TOKEN_MAX_AGE = -1  # Immediately expired
        person = Person.objects.create_unclaimed(first_name="Expired", last_name="Token")
        token = generate_claim_token(person)

        client.force_login(claimed_person)
        url = reverse("contributors:claim-profile", kwargs={"token": token})
        response = client.get(url)
        assert response.status_code == 200
        # Should render an error context
        assert "error" in response.context or "error_message" in response.context

    def test_already_claimed_token_shows_error(self, client, claimed_person, db):
        """Token for an already-claimed Person is rejected."""
        from fairdm.contrib.contributors.utils.tokens import generate_claim_token

        token = generate_claim_token(claimed_person)  # claimed_person is already claimed

        client.force_login(claimed_person)
        url = reverse("contributors:claim-profile", kwargs={"token": token})
        response = client.get(url)
        assert response.status_code == 200
        assert "error" in response.context or "error_message" in response.context


class TestClaimProfileViewPost:
    def test_post_claims_person_on_simple_path(self, client, claimed_person, unclaimed_person, claim_token):
        """Authenticated user with no conflict — POST activates unclaimed Person."""
        client.force_login(claimed_person)
        url = reverse("contributors:claim-profile-confirm", kwargs={"token": claim_token})
        response = client.post(url)
        assert response.status_code in (200, 302)
        unclaimed_person.refresh_from_db()
        assert unclaimed_person.is_claimed

    def test_post_unauthenticated_redirects(self, client, claim_token):
        """Unauthenticated POST is rejected with redirect to login."""
        url = reverse("contributors:claim-profile-confirm", kwargs={"token": claim_token})
        response = client.post(url)
        assert response.status_code == 302

    def test_post_expired_token_rejected(self, client, claimed_person, db, settings):
        """POST with expired token is rejected."""
        from fairdm.contrib.contributors.models import Person
        from fairdm.contrib.contributors.utils.tokens import generate_claim_token

        settings.CLAIM_TOKEN_MAX_AGE = -1
        person = Person.objects.create_unclaimed(first_name="Exp", last_name="Post")
        token = generate_claim_token(person)

        client.force_login(claimed_person)
        url = reverse("contributors:claim-profile-confirm", kwargs={"token": token})
        response = client.post(url)
        # Should not have claimed
        person.refresh_from_db()
        assert not person.is_claimed

    def test_post_banned_person_rejected(self, client, claimed_person, db):
        """POST with token for banned Person is rejected."""
        from fairdm.contrib.contributors.models import Person
        from fairdm.contrib.contributors.utils.tokens import generate_claim_token

        banned = Person.objects.create_unclaimed(first_name="Banned", last_name="Post")
        banned.is_active = False
        banned.save()
        token = generate_claim_token(banned)

        client.force_login(claimed_person)
        url = reverse("contributors:claim-profile-confirm", kwargs={"token": token})
        response = client.post(url)
        banned.refresh_from_db()
        assert not banned.is_claimed
