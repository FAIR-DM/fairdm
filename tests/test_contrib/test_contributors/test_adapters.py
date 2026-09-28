"""Integration tests for the ORCID social adapter — pre_social_login and save_user."""

import contextlib
from unittest.mock import MagicMock

import pytest
from allauth.core.exceptions import ImmediateHttpResponse
from waffle.testutils import override_switch

from fairdm.contrib.contributors.adapters import AccountAdapter, SocialAccountAdapter
from fairdm.contrib.contributors.models import ContributorIdentifier, Person

ORCID_UID = "0000-0002-9999-0001"


@pytest.fixture
def adapter():
    return SocialAccountAdapter()


@pytest.fixture
def account_adapter():
    return AccountAdapter()


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
    person = Person.objects.create_unclaimed(first_name="Jim", last_name="Unclaimed")
    ContributorIdentifier.objects.create(related=person, value=ORCID_UID, type="ORCID")
    return person


@pytest.fixture
def claimed_person_with_orcid(db):
    from fairdm.factories import PersonFactory

    person = PersonFactory(
        email="claimed_orcid@example.com", is_active=True, is_claimed=True
    )
    ContributorIdentifier.objects.create(related=person, value=ORCID_UID, type="ORCID")
    return person


class TestPreSocialLoginORCID:
    def test_unclaimed_person_gets_claimed_on_orcid_login(
        self, db, adapter, request_mock, unclaimed_person_with_orcid
    ):
        sl = _make_sociallogin(ORCID_UID, request_mock)

        with pytest.raises(ImmediateHttpResponse):
            adapter.pre_social_login(request_mock, sl)

        unclaimed_person_with_orcid.refresh_from_db()
        assert unclaimed_person_with_orcid.is_claimed is True
        assert unclaimed_person_with_orcid.is_active is True

    def test_no_duplicate_person_created_for_unclaimed_orcid(
        self, db, adapter, request_mock, unclaimed_person_with_orcid
    ):
        sl = _make_sociallogin(ORCID_UID, request_mock)
        count_before = Person.objects.filter(
            identifiers__value=ORCID_UID, identifiers__type="ORCID"
        ).count()

        with contextlib.suppress(ImmediateHttpResponse):
            adapter.pre_social_login(request_mock, sl)

        count_after = Person.objects.filter(
            identifiers__value=ORCID_UID, identifiers__type="ORCID"
        ).count()
        assert count_after == count_before

    def test_claimed_person_is_not_signed_in_via_identifier_row(
        self, db, adapter, request_mock, claimed_person_with_orcid
    ):
        sl = _make_sociallogin(ORCID_UID, request_mock)
        original_user = sl.user

        result = adapter.pre_social_login(request_mock, sl)

        assert result is None
        assert sl.user is original_user
        sl.connect.assert_not_called()

        claimed_person_with_orcid.refresh_from_db()
        assert claimed_person_with_orcid.is_claimed is True
        assert claimed_person_with_orcid.is_active is True

    def test_new_orcid_with_no_matching_person_falls_through(
        self, db, adapter, request_mock
    ):
        sl = _make_sociallogin("0000-0009-9999-9999", request_mock)

        result = adapter.pre_social_login(request_mock, sl)
        assert result is None


@pytest.fixture
def deactivated_unclaimed_person_with_orcid(db):
    person = Person.objects.create_unclaimed(first_name="Dana", last_name="Deactivated")
    person.is_active = False
    person.save(update_fields=["is_active"])
    ContributorIdentifier.objects.create(related=person, value=ORCID_UID, type="ORCID")
    return person


def _patch_super_save_user(monkeypatch):
    """Stub out DefaultSocialAccountAdapter.save_user."""

    def fake_save_user(self, request, sociallogin, form=None):
        sociallogin.user.save()
        return sociallogin.user

    monkeypatch.setattr(
        "fairdm.contrib.contributors.adapters.DefaultSocialAccountAdapter.save_user",
        fake_save_user,
    )


class TestSaveUserORCID:
    def test_deactivated_person_is_not_reactivated(
        self,
        db,
        adapter,
        request_mock,
        deactivated_unclaimed_person_with_orcid,
        monkeypatch,
    ):
        _patch_super_save_user(monkeypatch)
        sl = _make_sociallogin(ORCID_UID, request_mock)
        sl.user = MagicMock()

        adapter.save_user(request_mock, sl)

        deactivated_unclaimed_person_with_orcid.refresh_from_db()
        assert deactivated_unclaimed_person_with_orcid.is_active is False

    def test_unclaimed_person_is_still_adopted(
        self, db, adapter, request_mock, unclaimed_person_with_orcid, monkeypatch
    ):
        _patch_super_save_user(monkeypatch)
        sl = _make_sociallogin(ORCID_UID, request_mock)
        sl.user = MagicMock()

        adapter.save_user(request_mock, sl)

        assert sl.user == unclaimed_person_with_orcid

    def test_claimed_person_is_not_adopted(
        self, db, adapter, request_mock, claimed_person_with_orcid, monkeypatch
    ):
        _patch_super_save_user(monkeypatch)
        sl = _make_sociallogin(ORCID_UID, request_mock)
        new_user = MagicMock()
        sl.user = new_user

        adapter.save_user(request_mock, sl)

        assert sl.user is new_user
        assert sl.user != claimed_person_with_orcid

        claimed_person_with_orcid.refresh_from_db()
        assert claimed_person_with_orcid.is_claimed is True
        assert claimed_person_with_orcid.is_active is True

    def test_claimed_persons_orcid_is_not_duplicated_onto_the_new_account(
        self, db, adapter, request_mock, claimed_person_with_orcid, monkeypatch
    ):
        _patch_super_save_user(monkeypatch)
        sl = _make_sociallogin(ORCID_UID, request_mock)
        sl.user = Person(name="New Signup", first_name="New", last_name="Signup")

        user = adapter.save_user(request_mock, sl)

        assert user.pk is not None
        assert user != claimed_person_with_orcid
        assert not user.identifiers.filter(type="ORCID").exists()
        assert (
            ContributorIdentifier.objects.filter(value=ORCID_UID, type="ORCID").count()
            == 1
        )


class TestIsOpenForSignup:
    def test_signup_open_when_switch_active_and_not_invitation_only(
        self, db, settings, account_adapter, request_mock
    ):
        settings.FAIRDM_INVITATION_ONLY_SIGNUP = False
        with override_switch("allow_signup", active=True):
            assert account_adapter.is_open_for_signup(request_mock) is True

    def test_signup_closed_when_invitation_only_even_if_switch_active(
        self, db, settings, account_adapter, request_mock
    ):
        settings.FAIRDM_INVITATION_ONLY_SIGNUP = True
        with override_switch("allow_signup", active=True):
            assert account_adapter.is_open_for_signup(request_mock) is False

    def test_signup_closed_when_switch_inactive_even_if_not_invitation_only(
        self, db, settings, account_adapter, request_mock
    ):
        settings.FAIRDM_INVITATION_ONLY_SIGNUP = False
        with override_switch("allow_signup", active=False):
            assert account_adapter.is_open_for_signup(request_mock) is False

    def test_session_verified_email_bypasses_invitation_only(
        self, db, settings, account_adapter, request_mock
    ):
        settings.FAIRDM_INVITATION_ONLY_SIGNUP = True
        request_mock.session = {"account_verified_email": "person@example.com"}
        with override_switch("allow_signup", active=True):
            assert account_adapter.is_open_for_signup(request_mock) is True
