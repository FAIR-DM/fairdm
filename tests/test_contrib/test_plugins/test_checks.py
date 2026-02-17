"""Tests for Django system checks in plugin system."""

import pytest

from fairdm import plugins
from fairdm.contrib.plugins import Plugin, PluginGroup
from fairdm.contrib.plugins.checks import (
    check_duplicate_plugin_names,
    check_permission_strings,
    check_plugin_attributes,
    check_plugin_group_plugin_classes,
    check_plugin_group_plugins,
    check_plugin_group_url_conflicts,
    check_template_names,
    check_url_path_characters,
    check_url_path_conflicts,
)
from fairdm.core.sample.models import Sample

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("clear_registry")]


class TestCheckPluginAttributes:
    """Tests for check_plugin_attributes (E001)."""

    def test_valid_plugin_passes(self):
        """Plugin with valid attributes should pass all checks."""

        @plugins.register(Sample)
        class ValidPlugin(Plugin):
            name = "valid-plugin"
            menu = {"label": "Valid Plugin", "icon": "check", "order": 0}
            template_name = "valid.html"

        errors = check_plugin_attributes(None)

        assert len(errors) == 0

    def test_plugin_with_empty_name_falls_back_to_class_name(self):
        """Plugin with empty name should use class name as fallback (no error)."""

        @plugins.register(Sample)
        class EmptyNamePlugin(Plugin):
            name = ""  # Empty, but get_name() will use slugified class name
            menu = {"label": "Test", "order": 0}
            template_name = "test.html"

        errors = check_plugin_attributes(None)

        # No error expected - empty name triggers fallback to class name
        assert len(errors) == 0

    def test_plugin_with_invalid_menu_type_fails(self):
        """Plugin with non-dict menu should trigger E001 error."""

        @plugins.register(Sample)
        class InvalidMenuTypePlugin(Plugin):
            name = "test"
            menu = "not a dict"
            template_name = "test.html"

        errors = check_plugin_attributes(None)

        assert len(errors) == 1
        assert errors[0].id == "plugins.E001"
        assert "invalid menu attribute" in errors[0].msg.lower()

    def test_plugin_with_menu_missing_label_fails(self):
        """Plugin menu without 'label' key should trigger E001 error."""

        @plugins.register(Sample)
        class NoLabelMenuPlugin(Plugin):
            name = "test"
            menu = {"icon": "test", "order": 0}  # Missing 'label'
            template_name = "test.html"

        errors = check_plugin_attributes(None)

        assert len(errors) == 1
        assert errors[0].id == "plugins.E001"
        assert "missing required 'label' key" in errors[0].msg.lower()

    def test_plugin_without_menu_passes(self):
        """Plugin without menu attribute should pass."""

        @plugins.register(Sample)
        class NoMenuPlugin(Plugin):
            name = "test"
            template_name = "test.html"

        errors = check_plugin_attributes(None)

        assert len(errors) == 0


class TestCheckDuplicatePluginNames:
    """Tests for check_duplicate_plugin_names (E002)."""

    def test_unique_plugin_names_pass(self):
        """Plugins with unique names should pass."""

        @plugins.register(Sample)
        class PluginOne(Plugin):
            name = "plugin-one"
            menu = {"label": "One", "order": 0}
            template_name = "one.html"

        @plugins.register(Sample)
        class PluginTwo(Plugin):
            name = "plugin-two"
            menu = {"label": "Two", "order": 1}
            template_name = "two.html"

        errors = check_duplicate_plugin_names(None)

        assert len(errors) == 0

    def test_duplicate_plugin_names_fail(self):
        """Two plugins with same name for same model should trigger E002."""

        @plugins.register(Sample)
        class PluginOne(Plugin):
            name = "duplicate-name"
            menu = {"label": "One", "order": 0}
            template_name = "one.html"

        @plugins.register(Sample)
        class PluginTwo(Plugin):
            name = "duplicate-name"
            menu = {"label": "Two", "order": 1}
            template_name = "two.html"

        errors = check_duplicate_plugin_names(None)

        assert len(errors) == 1
        assert errors[0].id == "plugins.E002"
        assert "Duplicate plugin name 'duplicate-name'" in errors[0].msg


class TestCheckUrlPathConflicts:
    """Tests for check_url_path_conflicts (E003)."""

    def test_unique_url_paths_pass(self):
        """Plugins with unique URL paths should pass."""

        @plugins.register(Sample)
        class PluginOne(Plugin):
            name = "plugin-one"
            url_path = "path-one"
            menu = {"label": "One", "order": 0}
            template_name = "one.html"

        @plugins.register(Sample)
        class PluginTwo(Plugin):
            name = "plugin-two"
            url_path = "path-two"
            menu = {"label": "Two", "order": 1}
            template_name = "two.html"

        errors = check_url_path_conflicts(None)

        assert len(errors) == 0

    def test_duplicate_url_paths_fail(self):
        """Two plugins with same URL path for same model should trigger E003."""

        @plugins.register(Sample)
        class PluginOne(Plugin):
            name = "plugin-one"
            url_path = "same-path"
            menu = {"label": "One", "order": 0}
            template_name = "one.html"

        @plugins.register(Sample)
        class PluginTwo(Plugin):
            name = "plugin-two"
            url_path = "same-path"
            menu = {"label": "Two", "order": 1}
            template_name = "two.html"

        errors = check_url_path_conflicts(None)

        assert len(errors) == 1
        assert errors[0].id == "plugins.E003"
        assert "Duplicate URL path 'same-path'" in errors[0].msg


class TestCheckPluginGroupPlugins:
    """Tests for check_plugin_group_plugins (E005)."""

    def test_plugin_group_with_plugins_passes(self):
        """PluginGroup with non-empty plugins list should pass."""

        class InnerPlugin(Plugin):
            name = "inner"
            menu = {"label": "Inner", "order": 0}
            template_name = "inner.html"

        @plugins.register(Sample)
        class TestGroup(PluginGroup):
            name = "test-group"
            plugins = [InnerPlugin]
            menu = {"label": "Group", "order": 0}

        errors = check_plugin_group_plugins(None)

        assert len(errors) == 0

    def test_plugin_group_with_empty_plugins_fails(self):
        """PluginGroup with empty plugins list should trigger E005."""

        @plugins.register(Sample)
        class EmptyGroup(PluginGroup):
            name = "empty-group"
            plugins = []
            menu = {"label": "Empty", "order": 0}

        errors = check_plugin_group_plugins(None)

        assert len(errors) == 1
        assert errors[0].id == "plugins.E005"
        assert "empty plugins list" in errors[0].msg.lower()


class TestCheckPluginGroupPluginClasses:
    """Tests for check_plugin_group_plugin_classes (E006)."""

    def test_plugin_group_with_valid_plugin_classes_passes(self):
        """PluginGroup with valid Plugin subclasses should pass."""

        class ValidInnerPlugin(Plugin):
            name = "valid-inner"
            menu = {"label": "Valid", "order": 0}
            template_name = "valid.html"

        @plugins.register(Sample)
        class ValidGroup(PluginGroup):
            name = "valid-group"
            plugins = [ValidInnerPlugin]
            menu = {"label": "Valid Group", "order": 0}

        errors = check_plugin_group_plugin_classes(None)

        assert len(errors) == 0

    def test_plugin_group_with_non_class_fails(self):
        """PluginGroup with non-class entry should trigger E006."""

        @plugins.register(Sample)
        class InvalidGroup(PluginGroup):
            name = "invalid-group"
            plugins = ["not a class"]  # Invalid: string instead of class
            menu = {"label": "Invalid", "order": 0}

        errors = check_plugin_group_plugin_classes(None)

        assert len(errors) == 1
        assert errors[0].id == "plugins.E006"
        assert "is not a class" in errors[0].msg.lower()

    def test_plugin_group_with_non_plugin_subclass_fails(self):
        """PluginGroup with non-Plugin class should trigger E006."""

        class NotAPlugin:
            """Not a Plugin subclass."""

            pass

        @plugins.register(Sample)
        class InvalidGroup(PluginGroup):
            name = "invalid-group"
            plugins = [NotAPlugin]  # Invalid: not a Plugin subclass
            menu = {"label": "Invalid", "order": 0}

        errors = check_plugin_group_plugin_classes(None)

        assert len(errors) == 1
        assert errors[0].id == "plugins.E006"
        assert "not a plugin subclass" in errors[0].msg.lower()  # lowercase comparison


class TestCheckPluginGroupUrlConflicts:
    """Tests for check_plugin_group_url_conflicts (E007)."""

    def test_plugin_group_with_unique_plugin_paths_passes(self):
        """PluginGroup with unique plugin URL paths should pass."""

        class PluginA(Plugin):
            name = "plugin-a"
            url_path = "path-a"
            menu = {"label": "A", "order": 0}
            template_name = "a.html"

        class PluginB(Plugin):
            name = "plugin-b"
            url_path = "path-b"
            menu = {"label": "B", "order": 1}
            template_name = "b.html"

        @plugins.register(Sample)
        class UniquePathsGroup(PluginGroup):
            name = "unique-group"
            plugins = [PluginA, PluginB]
            menu = {"label": "Unique", "order": 0}

        errors = check_plugin_group_url_conflicts(None)

        assert len(errors) == 0

    def test_plugin_group_with_duplicate_plugin_paths_fails(self):
        """PluginGroup with duplicate plugin URL paths should trigger E007."""

        class PluginA(Plugin):
            name = "plugin-a"
            url_path = "same-path"
            menu = {"label": "A", "order": 0}
            template_name = "a.html"

        class PluginB(Plugin):
            name = "plugin-b"
            url_path = "same-path"  # Duplicate path
            menu = {"label": "B", "order": 1}
            template_name = "b.html"

        @plugins.register(Sample)
        class ConflictGroup(PluginGroup):
            name = "conflict-group"
            plugins = [PluginA, PluginB]
            menu = {"label": "Conflict", "order": 0}

        errors = check_plugin_group_url_conflicts(None)

        assert len(errors) == 1
        assert errors[0].id == "plugins.E007"
        assert "URL conflict" in errors[0].msg


class TestCheckPermissionStrings:
    """Tests for check_permission_strings (W001)."""

    def test_valid_permission_format_passes(self):
        """Plugin with valid permission format should pass."""

        @plugins.register(Sample)
        class ValidPermPlugin(Plugin):
            name = "valid-perm"
            permission = "fairdm.view_sample"
            menu = {"label": "Valid", "order": 0}
            template_name = "valid.html"

        warnings = check_permission_strings(None)

        # May have warnings about non-existent permission, but format is valid
        # so if there are warnings, they should be about existence not format
        for warning in warnings:
            assert "invalid permission format" not in warning.msg.lower()

    def test_invalid_permission_format_warns(self):
        """Plugin with invalid permission format should trigger W001."""

        @plugins.register(Sample)
        class InvalidPermPlugin(Plugin):
            name = "invalid-perm"
            permission = "invalid_format_no_dot"  # Missing app_label.
            menu = {"label": "Invalid", "order": 0}
            template_name = "invalid.html"

        warnings = check_permission_strings(None)

        assert len(warnings) >= 1
        w001_warnings = [w for w in warnings if w.id == "plugins.W001"]
        assert len(w001_warnings) == 1
        assert "invalid permission format" in w001_warnings[0].msg.lower()

    def test_plugin_without_permission_passes(self):
        """Plugin without permission attribute should pass."""

        @plugins.register(Sample)
        class NoPermPlugin(Plugin):
            name = "no-perm"
            menu = {"label": "No Perm", "order": 0}
            template_name = "no-perm.html"

        warnings = check_permission_strings(None)

        # Should not produce W001 warnings for this plugin
        assert len(warnings) == 0


class TestCheckTemplateNames:
    """Tests for check_template_names (E004/W002)."""

    def test_valid_template_name_passes(self):
        """Plugin with valid template_name should pass."""

        @plugins.register(Sample)
        class ValidTemplatePlugin(Plugin):
            name = "valid-template"
            template_name = "valid/template.html"
            menu = {"label": "Valid", "order": 0}

        errors = check_template_names(None)

        assert len(errors) == 0

    def test_non_string_template_name_fails(self):
        """Plugin with non-string template_name should trigger E004."""

        @plugins.register(Sample)
        class InvalidTypePlugin(Plugin):
            name = "invalid-type"
            template_name = 123  # Invalid: not a string
            menu = {"label": "Invalid", "order": 0}

        errors = check_template_names(None)

        e004_errors = [e for e in errors if e.id == "plugins.E004"]
        assert len(e004_errors) == 1
        assert "invalid template_name type" in e004_errors[0].msg.lower()

    def test_empty_template_name_fails(self):
        """Plugin with empty template_name should trigger E004."""

        @plugins.register(Sample)
        class EmptyTemplatePlugin(Plugin):
            name = "empty-template"
            template_name = "   "  # Empty after strip
            menu = {"label": "Empty", "order": 0}

        errors = check_template_names(None)

        e004_errors = [e for e in errors if e.id == "plugins.E004"]
        assert len(e004_errors) == 1
        assert "empty template_name" in e004_errors[0].msg.lower()

    def test_template_name_without_html_extension_warns(self):
        """Plugin template without .html extension should trigger W002."""

        @plugins.register(Sample)
        class NoHtmlExtPlugin(Plugin):
            name = "no-html"
            template_name = "template.txt"  # Not .html
            menu = {"label": "No HTML", "order": 0}

        errors = check_template_names(None)

        w002_warnings = [e for e in errors if e.id == "plugins.W002"]
        assert len(w002_warnings) == 1
        assert "doesn't end with .html" in w002_warnings[0].msg.lower()

    def test_plugin_without_template_name_passes(self):
        """Plugin without explicit template_name should pass (auto-resolution)."""

        @plugins.register(Sample)
        class NoTemplateNamePlugin(Plugin):
            name = "no-template-name"
            menu = {"label": "No Template", "order": 0}

        errors = check_template_names(None)

        assert len(errors) == 0


class TestCheckUrlPathCharacters:
    """Tests for check_url_path_characters (W003)."""

    def test_valid_url_path_passes(self):
        """Plugin with valid URL path characters should pass."""

        @plugins.register(Sample)
        class ValidPathPlugin(Plugin):
            name = "valid-path"
            url_path = "valid-path-123"
            menu = {"label": "Valid", "order": 0}
            template_name = "valid.html"

        warnings = check_url_path_characters(None)

        assert len(warnings) == 0

    def test_url_path_with_invalid_characters_warns(self):
        """Plugin with invalid URL path characters should trigger W003."""

        @plugins.register(Sample)
        class InvalidCharsPlugin(Plugin):
            name = "invalid-chars"
            url_path = "invalid/path with spaces"  # Invalid chars
            menu = {"label": "Invalid", "order": 0}
            template_name = "invalid.html"

        warnings = check_url_path_characters(None)

        assert len(warnings) >= 1
        w003_warnings = [w for w in warnings if w.id == "plugins.W003"]
        assert len(w003_warnings) >= 1
        assert any("invalid characters" in w.msg.lower() for w in w003_warnings)

    def test_url_path_with_leading_slash_warns(self):
        """Plugin URL path with leading slash should trigger W003."""

        @plugins.register(Sample)
        class LeadingSlashPlugin(Plugin):
            name = "leading-slash"
            url_path = "/bad-path"  # Leading slash
            menu = {"label": "Leading", "order": 0}
            template_name = "leading.html"

        warnings = check_url_path_characters(None)

        assert len(warnings) >= 1
        w003_warnings = [w for w in warnings if w.id == "plugins.W003"]
        assert len(w003_warnings) >= 1
        assert any("should not start or end with slashes" in w.msg.lower() for w in w003_warnings)

    def test_url_path_with_trailing_slash_warns(self):
        """Plugin URL path with trailing slash should trigger W003."""

        @plugins.register(Sample)
        class TrailingSlashPlugin(Plugin):
            name = "trailing-slash"
            url_path = "bad-path/"  # Trailing slash
            menu = {"label": "Trailing", "order": 0}
            template_name = "trailing.html"

        warnings = check_url_path_characters(None)

        assert len(warnings) >= 1
        w003_warnings = [w for w in warnings if w.id == "plugins.W003"]
        assert len(w003_warnings) >= 1
        assert any("should not start or end with slashes" in w.msg.lower() for w in w003_warnings)

    def test_non_string_url_path_warns(self):
        """Plugin with non-string url_path should trigger W003."""

        @plugins.register(Sample)
        class NonStringPathPlugin(Plugin):
            name = "non-string-path"
            url_path = 123  # Not a string
            menu = {"label": "Non-String", "order": 0}
            template_name = "non-string.html"

        warnings = check_url_path_characters(None)

        assert len(warnings) >= 1
        w003_warnings = [w for w in warnings if w.id == "plugins.W003"]
        assert len(w003_warnings) >= 1
        assert any("non-string url_path" in w.msg.lower() for w in w003_warnings)

    def test_plugin_without_url_path_passes(self):
        """Plugin without explicit url_path should pass (auto-generated)."""

        @plugins.register(Sample)
        class NoUrlPathPlugin(Plugin):
            name = "no-url-path"
            menu = {"label": "No Path", "order": 0}
            template_name = "no-path.html"

        warnings = check_url_path_characters(None)

        assert len(warnings) == 0
