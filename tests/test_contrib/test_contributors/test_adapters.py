"""Integration tests for the ORCID social adapter — pre_social_login and save_user.

Tests verify that:
  - An existing unclaimed Person with a matching ORCID ContributorIdentifier
    gets automatically claimed on ORCID login (no duplicate Person created).
  - An existing claimed/active Person is NOT signed into by the strength of a
    ContributorIdentifier row alone — that row is not proof of identity, and
    only allauth's ordinary (email-verified) flow may reach a claimed account.
  - A deactivated (banned) Person is never reactivated by an ORCID sign-in.
  - A new ORCID sign-in (no matching Person in DB) falls through to the
    normal allauth signup flow.
"""

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
    """Unclaimed Person pre-loaded with an ORCID ContributorIdentifier."""
    person = Person.objects.create_unclaimed(first_name="Jim", last_name="Unclaimed")
    ContributorIdentifier.objects.create(related=person, value=ORCID_UID, type="ORCID")
    return person


@pytest.fixture
def claimed_person_with_orcid(db):
    """Already-claimed Person with an ORCID ContributorIdentifier."""
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

        with contextlib.suppress(ImmediateHttpResponse):
            adapter.pre_social_login(request_mock, sl)

        count_after = Person.objects.filter(
            identifiers__value=ORCID_UID, identifiers__type="ORCID"
        ).count()
        assert count_after == count_before

    def test_claimed_person_is_not_signed_in_via_identifier_row(
        self, db, adapter, request_mock, claimed_person_with_orcid
    ):
        """An already-claimed Person is never signed into by an ORCID identifier row.

        Previously this branch swapped ``sociallogin.user`` to the existing,
        already-claimed Person and connected them — treating a
        ``ContributorIdentifier`` row (writable by an administrator or a bulk
        import) as proof of identity. That is account takeover: the row buys
        no more than skipping allauth's "Account Already Exists" email, at the
        cost of letting anyone who can write an identifier row sign in as the
        person it names. The fix leaves a claimed match untouched and falls
        through to allauth's ordinary, email-verified flow.
        """
        sl = _make_sociallogin(ORCID_UID, request_mock)
        original_user = sl.user

        # Should NOT raise, and should NOT connect or hijack the sociallogin.
        result = adapter.pre_social_login(request_mock, sl)

        assert result is None
        assert sl.user is original_user
        sl.connect.assert_not_called()

        # The claimed person themselves is untouched.
        claimed_person_with_orcid.refresh_from_db()
        assert claimed_person_with_orcid.is_claimed is True
        assert claimed_person_with_orcid.is_active is True

    def test_new_orcid_with_no_matching_person_falls_through(
        self, db, adapter, request_mock
    ):
        """An ORCID not known to the system falls through to normal allauth signup."""
        sl = _make_sociallogin("0000-0009-9999-9999", request_mock)

        # Should not raise — no matching Person, normal flow
        result = adapter.pre_social_login(request_mock, sl)
        assert result is None


# ── save_user ────────────────────────────────────────────────────────────────


@pytest.fixture
def deactivated_unclaimed_person_with_orcid(db):
    """A deactivated (banned), unclaimed Person with an ORCID ContributorIdentifier."""
    person = Person.objects.create_unclaimed(first_name="Dana", last_name="Deactivated")
    person.is_active = False
    person.save(update_fields=["is_active"])
    ContributorIdentifier.objects.create(related=person, value=ORCID_UID, type="ORCID")
    return person


def _patch_super_save_user(monkeypatch):
    """Stub out DefaultSocialAccountAdapter.save_user.

    The real implementation goes on to persist ``sociallogin.user`` via
    ``sociallogin.save(request)``, which needs a fully-formed allauth
    SocialLogin/session and is exercised elsewhere (allauth's own test suite,
    and the app's login views). These tests are only about the adapter's own
    decision of *which* Person ``sociallogin.user`` ends up pointing at and
    what is set on it before that persistence step — so the stub keeps the
    one part that matters for a reactivation check (saving whatever is on
    ``sociallogin.user`` at that point) without the rest of the real signup
    machinery.
    """

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
        """A deactivated Person found by ORCID is adopted (still unclaimed) but
        save_user no longer un-bans them by forcing is_active back to True.
        """
        _patch_super_save_user(monkeypatch)
        sl = _make_sociallogin(ORCID_UID, request_mock)
        sl.user = MagicMock()

        adapter.save_user(request_mock, sl)

        deactivated_unclaimed_person_with_orcid.refresh_from_db()
        assert deactivated_unclaimed_person_with_orcid.is_active is False

    def test_unclaimed_person_is_still_adopted(
        self, db, adapter, request_mock, unclaimed_person_with_orcid, monkeypatch
    ):
        """An unclaimed Person found by ORCID is still adopted by save_user."""
        _patch_super_save_user(monkeypatch)
        sl = _make_sociallogin(ORCID_UID, request_mock)
        sl.user = MagicMock()

        adapter.save_user(request_mock, sl)

        assert sl.user == unclaimed_person_with_orcid

    def test_claimed_person_is_not_adopted(
        self, db, adapter, request_mock, claimed_person_with_orcid, monkeypatch
    ):
        """A claimed Person found by ORCID is left alone — save_user does not
        adopt it, so signup proceeds as a genuinely new account rather than
        silently taking over the claimed one.
        """
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
        """An ORCID identifies at most one person. ``AbstractIdentifier.value`` carries
        a database-level uniqueness constraint (``fairdm/core/abstract.py``), so the old
        unconditional ``user.identifiers.create(value=orcid_id, ...)`` did not actually
        succeed in duplicating the value — it raised an uncaught ``IntegrityError`` and
        crashed the signup instead, because ``claimed_person_with_orcid`` already holds
        a ``ContributorIdentifier`` row for this exact value. Either way is wrong: the
        new, genuinely-new-account signup must complete, and it must not attempt to
        write a second identifier row for a value that already belongs to somebody
        else.

        This test uses a real, saved ``Person`` for ``sociallogin.user`` (not a
        ``MagicMock`` like ``test_claimed_person_is_not_adopted`` above) specifically so
        ``user.identifiers.create(...)`` is real, unmocked ORM code hitting the real
        unique constraint — a MagicMock's ``.identifiers.create(...)`` is itself a mock
        call and would never demonstrate this at all.
        """
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


# ── is_open_for_signup ──────────────────────────────────────────────────────


class TestIsOpenForSignup:
    """FAIRDM_INVITATION_ONLY_SIGNUP (issue #266) replaces django-invitations'
    INVITATIONS_INVITATION_ONLY as the signup gate, alongside the pre-existing
    allow_signup waffle switch."""

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
        """A session already carrying a verified email (e.g. mid social-signup
        flow) is let through regardless of the invitation-only gate, as long
        as signup is switched on at all."""
        settings.FAIRDM_INVITATION_ONLY_SIGNUP = True
        request_mock.session = {"account_verified_email": "person@example.com"}
        with override_switch("allow_signup", active=True):
            assert account_adapter.is_open_for_signup(request_mock) is True
