"""Integration tests for the ORCID social adapter — pre_social_login hook.

Tests verify that:
  - An existing unclaimed Person with a matching ORCID ContributorIdentifier
    gets automatically claimed on ORCID login (no duplicate Person created).
  - An existing claimed/active Person simply gets the account connected.
  - A new ORCID sign-in (no matching Person in DB) falls through to the
    normal allauth signup flow.
"""

import pytest
from unittest.mock import MagicMock, patch

from allauth.core.exceptions import ImmediateHttpResponse

from fairdm.contrib.contributors.adapters import SocialAccountAdapter
from fairdm.contrib.contributors.models import ContributorIdentifier, Person


ORCID_UID = "0000-0002-9999-0001"


@pytest.fixture
def adapter():
    return SocialAccountAdapter()


@pytest.fixture
def request_mock():
    req = MagicMock()
    req.session = {}
    return req


def _make_sociallogin(uid: str, request=None) -> MagicMock:
    sl = MagicMock()
    sl.account.uid = uid
    sl.account.provider = "orcid"
    sl.request = request
    return sl


@pytest.fixture
def unclaimed_person_with_orcid(db):
    """Unclaimed Person pre-loaded with an ORCID ContributorIdentifier."""
    person = Person.objects.create_unclaimed(first_name="Jim", last_name="Unclaimed")
    ContributorIdentifier.objects.create(related=person, value=ORCID_UID, type="ORCID")
    return person


@pytest.fixture
def claimed_person_with_orcid(db):
    """Already-claimed Person with an ORCID ContributorIdentifier."""
    from fairdm.factories import PersonFactory

    person = PersonFactory(email="claimed_orcid@example.com", is_active=True, is_claimed=True)
    ContributorIdentifier.objects.create(related=person, value=ORCID_UID, type="ORCID")
    return person


class TestPreSocialLoginORCID:
    def test_unclaimed_person_gets_claimed_on_orcid_login(
        self, db, adapter, request_mock, unclaimed_person_with_orcid
    ):
        """When an unclaimed Person has a matching ORCID, pre_social_login claims them."""
        sl = _make_sociallogin(ORCID_UID, request_mock)

        # pre_social_login raises ImmediateHttpResponse to redirect after claiming
        with pytest.raises(ImmediateHttpResponse):
            adapter.pre_social_login(request_mock, sl)

        unclaimed_person_with_orcid.refresh_from_db()
        assert unclaimed_person_with_orcid.is_claimed is True
        assert unclaimed_person_with_orcid.is_active is True

    def test_no_duplicate_person_created_for_unclaimed_orcid(
        self, db, adapter, request_mock, unclaimed_person_with_orcid
    ):
        """After ORCID claiming, still only one Person row exists in the DB."""
        sl = _make_sociallogin(ORCID_UID, request_mock)
        count_before = Person.objects.filter(
            identifiers__value=ORCID_UID, identifiers__type="ORCID"
        ).count()

        try:
            adapter.pre_social_login(request_mock, sl)
        except ImmediateHttpResponse:
            pass

        count_after = Person.objects.filter(
            identifiers__value=ORCID_UID, identifiers__type="ORCID"
        ).count()
        assert count_after == count_before

    def test_claimed_person_gets_account_connected(
        self, db, adapter, request_mock, claimed_person_with_orcid
    ):
        """An already-claimed Person with ORCID simply gets the social account connected."""
        sl = _make_sociallogin(ORCID_UID, request_mock)

        # Should NOT raise — falls through without exception
        adapter.pre_social_login(request_mock, sl)

        # sociallogin.user should be swapped to the existing person
        assert sl.user == claimed_person_with_orcid
        sl.connect.assert_called_once()

    def test_new_orcid_with_no_matching_person_falls_through(self, db, adapter, request_mock):
        """An ORCID not known to the system falls through to normal allauth signup."""
        sl = _make_sociallogin("0000-0009-9999-9999", request_mock)

        # Should not raise — no matching Person, normal flow
        result = adapter.pre_social_login(request_mock, sl)
        assert result is None
