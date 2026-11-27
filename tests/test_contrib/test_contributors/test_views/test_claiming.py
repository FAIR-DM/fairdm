"""Tests for the pages a profile claim link opens."""

from urllib.parse import parse_qs, urlsplit

import pytest
from django.conf import settings
from django.shortcuts import resolve_url
from django.urls import reverse

from fairdm.contrib.contributors.utils.tokens import generate_claim_token
from fairdm.factories import PersonFactory


@pytest.fixture
def claim_token(unclaimed_person):
    return generate_claim_token(unclaimed_person)


@pytest.fixture
def signed_in(client):
    client.force_login(PersonFactory(email="claimant@example.org", is_active=True))
    return client


@pytest.mark.django_db
class TestClaimProfilePage:
    def test_a_visitor_who_is_not_signed_in_is_sent_to_sign_in_and_back(
        self, client, claim_token
    ):
        claim_url = reverse("contributors:claim-profile", kwargs={"token": claim_token})

        response = client.get(claim_url)

        sign_in = urlsplit(response.url)
        assert response.status_code == 302
        assert sign_in.path == resolve_url(settings.LOGIN_URL)
        assert parse_qs(sign_in.query)["next"] == [claim_url]

    def test_a_signed_in_person_sees_the_profile_and_claims_nothing(
        self, signed_in, claim_token, unclaimed_person
    ):
        response = signed_in.get(
            reverse("contributors:claim-profile", kwargs={"token": claim_token})
        )

        unclaimed_person.refresh_from_db()
        assert response.status_code == 200
        assert response.context["unclaimed_person"] == unclaimed_person
        assert unclaimed_person.is_claimed is False

    def test_an_altered_link_shows_an_error(self, signed_in, claim_token):
        response = signed_in.get(
            reverse("contributors:claim-profile", kwargs={"token": claim_token + "x"})
        )

        assert response.status_code == 200
        assert response.context["error"] is True
        assert "unclaimed_person" not in response.context

    def test_a_deactivated_profile_cannot_be_claimed(
        self, signed_in, claim_token, unclaimed_person
    ):
        unclaimed_person.is_active = False
        unclaimed_person.save(update_fields=["is_active"])

        response = signed_in.get(
            reverse("contributors:claim-profile", kwargs={"token": claim_token})
        )

        assert response.context["error"] is True
        assert "unclaimed_person" not in response.context


@pytest.mark.django_db
class TestConfirmClaim:
    def test_a_visitor_who_is_not_signed_in_claims_nothing(
        self, client, claim_token, unclaimed_person
    ):
        response = client.post(
            reverse("contributors:claim-profile-confirm", kwargs={"token": claim_token})
        )

        unclaimed_person.refresh_from_db()
        assert response.status_code == 302
        assert urlsplit(response.url).path == resolve_url(settings.LOGIN_URL)
        assert unclaimed_person.is_claimed is False

    def test_confirming_marks_the_profile_claimed_and_leaves_the_page(
        self, signed_in, claim_token, unclaimed_person
    ):
        response = signed_in.post(
            reverse("contributors:claim-profile-confirm", kwargs={"token": claim_token})
        )

        unclaimed_person.refresh_from_db()
        assert response.status_code == 302
        assert unclaimed_person.is_claimed is True

    def test_an_altered_link_claims_nothing_and_shows_an_error(
        self, signed_in, claim_token, unclaimed_person
    ):
        response = signed_in.post(
            reverse(
                "contributors:claim-profile-confirm",
                kwargs={"token": claim_token + "x"},
            )
        )

        unclaimed_person.refresh_from_db()
        assert response.status_code == 200
        assert response.context["error"] is True
        assert unclaimed_person.is_claimed is False
