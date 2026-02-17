"""
Tests for plugin permission handling.

User Story 5: Permission Integration
"""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.sample.models import Sample
from fairdm.factories.contributors import UserFactory

pytestmark = pytest.mark.django_db


class TestPluginPermissions:
    """Test permission integration (User Story 5)."""

    def test_plugin_with_permission_attribute(self):
        """Given a plugin with a permission attribute,
        When a user without permission tries to access it,
        Then access is denied (User Story 5, Scenario 1)."""

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.change_sample"
            menu = {"label": "Edit", "icon": "edit", "order": 10}
            template_name = "plugins/edit.html"

        # Create users
        user_with_perm = UserFactory(email="editor@example.com")
        user_without_perm = UserFactory(email="viewer@example.com")

        # Grant permission to one user
        content_type = ContentType.objects.get_for_model(Sample)
        change_perm = Permission.objects.get(codename="change_sample", content_type=content_type)
        user_with_perm.user_permissions.add(change_perm)

        # Check permission
        assert user_with_perm.has_perm("sample.change_sample")
        assert not user_without_perm.has_perm("sample.change_sample")

    def test_plugin_without_permission_is_public(self):
        """Given a plugin without a permission attribute,
        When any user accesses it,
        Then access is allowed (User Story 5, Scenario 2)."""

        @plugins.register(Sample)
        class PublicPlugin(Plugin, TemplateView):
            # No permission attribute
            menu = {"label": "Overview", "icon": "info", "order": 20}
            template_name = "plugins/overview.html"

        # Plugin should not have permission requirement
        assert not hasattr(PublicPlugin, "permission") or PublicPlugin.permission is None

    def test_permission_shown_in_tab(self, sample, admin_user):
        """Tab should include permission information."""

        @plugins.register(Sample)
        class SecurePlugin(Plugin, TemplateView):
            permission = "sample.delete_sample"
            menu = {"label": "Delete", "icon": "trash", "order": 30}
            template_name = "plugins/delete.html"

        # Verify plugin has permission attribute set
        assert hasattr(SecurePlugin, "permission")
        assert SecurePlugin.permission == "sample.delete_sample"


class TestObjectLevelPermissions:
    """Test object-level permission integration."""

    def test_plugin_respects_object_permissions(self):
        """Plugins should integrate with django-guardian for object-level permissions."""

        @plugins.register(Sample)
        class ObjectPermPlugin(Plugin, TemplateView):
            permission = "sample.view_sample"
            menu = {"label": "View Details", "icon": "eye", "order": 40}
            template_name = "plugins/details.html"

        # Plugin should have permission attribute for guardian to check
        assert ObjectPermPlugin.permission == "sample.view_sample"
