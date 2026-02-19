"""
Tests for Privacy Controls (Phase 11).

This module tests privacy-aware field visibility based on viewer type
and claim status.

Tests correspond to tasks T111-T114.
"""

import pytest

from fairdm.contrib.contributors.models import Person

# ── T111: Privacy for unclaimed persons ──────────────────────────────────────


class TestUnclaimedPersonPrivacy:
    """Test privacy controls for unclaimed persons."""

    @pytest.mark.django_db
    def test_unclaimed_person_all_fields_public(self, unclaimed_person):
        """Unclaimed persons should have all fields public by default."""
        # Unclaimed persons default to all public for provenance
        visible = unclaimed_person.get_visible_fields(viewer=None)

        # Should include always-public fields
        assert "name" in visible
        assert "uuid" in visible
        assert "alternative_names" in visible
        assert "added" in visible

        # Email should be included (toggleable, but defaults to public for unclaimed)
        assert "email" in visible

    @pytest.mark.django_db
    def test_unclaimed_person_visible_to_anonymous(self, unclaimed_person):
        """Unclaimed person fields visible to anonymous users."""
        # Anonymous viewer (None)
        visible = unclaimed_person.get_visible_fields(viewer=None)

        # Should include core fields
        assert "name" in visible
        assert visible["name"] == unclaimed_person.name


# ── T112: Privacy for claimed persons ────────────────────────────────────────


class TestClaimedPersonPrivacy:
    """Test privacy controls for claimed persons."""

    @pytest.mark.django_db
    def test_claimed_person_email_private_by_default(self, person):
        """Claimed persons should have email marked private by default."""
        # Claimed persons default to email=private
        # Check privacy settings
        assert person.privacy_settings is not None
        assert person.privacy_settings.get("email") == "private"

    @pytest.mark.django_db
    def test_claimed_person_email_hidden_from_anonymous(self, person):
        """Claimed person email not visible to anonymous users."""
        # Anonymous viewer
        visible = person.get_visible_fields(viewer=None)

        # Email should not be included for anonymous viewers
        assert "email" not in visible or visible.get("email") is None

    @pytest.mark.django_db
    def test_claimed_person_public_fields_visible(self, person):
        """Claimed person public fields visible to all viewers."""
        # Anonymous viewer
        visible = person.get_visible_fields(viewer=None)

        # Public fields should always be visible
        assert "name" in visible
        assert visible["name"] == person.name


# ── T113: get_visible_fields for anonymous viewers ───────────────────────────


class TestGetVisibleFieldsAnonymous:
    """Test get_visible_fields() with anonymous (None) viewer."""

    @pytest.mark.django_db
    def test_public_fields_always_visible(self, person):
        """Public fields visible to anonymous viewers."""
        visible = person.get_visible_fields(viewer=None)

        # Core always-public fields should be visible
        assert "name" in visible
        assert "uuid" in visible
        assert "alternative_names" in visible
        assert "added" in visible
        assert "modified" in visible

    @pytest.mark.django_db
    def test_private_fields_hidden_from_anonymous(self, person):
        """Private fields hidden from anonymous viewers."""
        # Set email as private
        person.privacy_settings = {"email": "private"}
        person.save()

        visible = person.get_visible_fields(viewer=None)

        # Email should not be visible
        assert "email" not in visible or visible.get("email") is None

    @pytest.mark.django_db
    def test_authenticated_only_fields_hidden_from_anonymous(self, person):
        """Fields marked 'authenticated' hidden from anonymous viewers."""
        # Set a toggleable field as authenticated-only
        person.privacy_settings = {"email": "authenticated"}
        person.save()

        visible = person.get_visible_fields(viewer=None)

        # Email should not be visible to anonymous
        assert "email" not in visible or visible.get("email") is None


# ── T114: get_visible_fields for authenticated viewers ───────────────────────


class TestGetVisibleFieldsAuthenticated:
    """Test get_visible_fields() with authenticated viewer."""

    @pytest.mark.django_db
    def test_public_fields_visible_to_authenticated(self, person):
        """Public fields visible to authenticated viewers."""
        # Create an authenticated viewer
        viewer = Person.objects.create(
            email="viewer@example.com",
            first_name="Test",
            last_name="Viewer",
            is_active=True,
        )
        viewer.set_password("testpass123")
        viewer.save()

        visible = person.get_visible_fields(viewer=viewer)

        # Public fields should be visible
        assert "name" in visible
        assert visible["name"] == person.name

    @pytest.mark.django_db
    def test_authenticated_fields_visible_to_authenticated(self, person):
        """Fields marked 'authenticated' visible to authenticated viewers."""
        # Create an authenticated viewer
        viewer = Person.objects.create(
            email="viewer@example.com",
            first_name="Test",
            last_name="Viewer",
            is_active=True,
        )
        viewer.set_password("testpass123")
        viewer.save()

        # Set a toggleable field as authenticated-only
        person.privacy_settings = {"profile": "authenticated"}
        person.profile = "This is a profile"
        person.save()

        visible = person.get_visible_fields(viewer=viewer)

        # Profile should be visible to authenticated user
        assert "profile" in visible
        assert visible["profile"] == person.profile

    @pytest.mark.django_db
    def test_private_fields_hidden_from_others(self, person):
        """Private fields hidden from other authenticated users."""
        # Create an authenticated viewer (not the owner)
        viewer = Person.objects.create(
            email="viewer@example.com",
            first_name="Test",
            last_name="Viewer",
            is_active=True,
        )
        viewer.set_password("testpass123")
        viewer.save()

        # Set email as private
        person.privacy_settings = {"email": "private"}
        person.save()

        visible = person.get_visible_fields(viewer=viewer)

        # Private email should not be visible to other users
        assert "email" not in visible or visible.get("email") is None

    @pytest.mark.django_db
    def test_viewer_can_see_own_private_fields(self, person):
        """User viewing their own profile can see all fields."""
        # Set email as private
        person.privacy_settings = {"email": "private"}
        person.save()

        # Viewer is the person themselves
        visible = person.get_visible_fields(viewer=person)

        # Should see their own email even if private
        assert "email" in visible
        assert visible["email"] == person.email
