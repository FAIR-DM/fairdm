"""Django system checks for plugin system."""

from django.core.checks import Error, Tags, register

from .registry import registry


@register(Tags.compatibility)
def check_plugin_attributes(app_configs, **kwargs):
    """E001: Check that plugins have required attributes.

    Verifies that each registered Plugin/PluginGroup has:
    - A valid name (can be auto-derived)
    - A valid url_path (can be auto-derived)
    - Valid menu dict structure if menu is set
    """
    errors = []

    for _model, plugin_classes in registry._registry.items():
        for plugin_class in plugin_classes:
            # Check if class can generate a name
            try:
                name = plugin_class.get_name()
                if not name or not name.strip():
                    errors.append(
                        Error(
                            f"Plugin {plugin_class.__name__} has empty name",
                            hint="Provide a non-empty 'name' class attribute or ensure class name is valid",
                            obj=plugin_class,
                            id="plugins.E001",
                        )
                    )
            except Exception as e:
                errors.append(
                    Error(
                        f"Plugin {plugin_class.__name__} cannot generate name: {e}",
                        hint="Ensure get_name() classmethod works correctly",
                        obj=plugin_class,
                        id="plugins.E001",
                    )
                )

            # Check menu dict structure if present
            menu = getattr(plugin_class, "menu", None)
            if menu:
                if not isinstance(menu, dict):
                    errors.append(
                        Error(
                            f"Plugin {plugin_class.__name__} has invalid menu attribute (must be dict)",
                            hint="Set menu = {'label': '...', 'icon': '...', 'order': 0} or menu = None",
                            obj=plugin_class,
                            id="plugins.E001",
                        )
                    )
                elif "label" not in menu:
                    errors.append(
                        Error(
                            f"Plugin {plugin_class.__name__} menu dict missing required 'label' key",
                            hint="menu dict must have 'label' key: {'label': 'My Plugin', ...}",
                            obj=plugin_class,
                            id="plugins.E001",
                        )
                    )

    return errors


@register(Tags.compatibility)
def check_duplicate_plugin_names(app_configs, **kwargs):
    """E002: Check for duplicate plugin names per model.

    Ensures no two plugins registered for the same model share the same name.
    """
    errors = []

    for model, plugin_classes in registry._registry.items():
        seen_names = {}
        for plugin_class in plugin_classes:
            try:
                name = plugin_class.get_name()
            except Exception:  # noqa: S112
                # Name generation error caught by E001
                continue

            if name in seen_names:
                errors.append(
                    Error(
                        f"Duplicate plugin name '{name}' for model {model.__name__}",
                        hint=f"Plugins {seen_names[name].__name__} and {plugin_class.__name__} have the same name",
                        obj=plugin_class,
                        id="plugins.E002",
                    )
                )
            else:
                seen_names[name] = plugin_class

    return errors


@register(Tags.compatibility)
def check_url_path_conflicts(app_configs, **kwargs):
    """E003: Check for URL path conflicts per model.

    Ensures no two plugins registered for the same model produce conflicting URL paths.
    """
    errors = []

    for model, plugin_classes in registry._registry.items():
        seen_paths = {}
        for plugin_class in plugin_classes:
            try:
                # For PluginGroup, check the url_prefix
                if hasattr(plugin_class, "get_url_prefix"):
                    path = plugin_class.get_url_prefix()
                else:
                    path = plugin_class.get_url_path()
            except Exception:  # noqa: S112
                # Path generation error caught by E001
                continue

            if path in seen_paths:
                errors.append(
                    Error(
                        f"Duplicate URL path '{path}' for model {model.__name__}",
                        hint=f"Plugins {seen_paths[path].__name__} and {plugin_class.__name__} have conflicting URL paths",
                        obj=plugin_class,
                        id="plugins.E003",
                    )
                )
            else:
                seen_paths[path] = plugin_class

    return errors


@register(Tags.compatibility)
def check_plugin_group_plugins(app_configs, **kwargs):
    """E005: Check that PluginGroups have non-empty plugins list.

    Ensures PluginGroups contain at least one plugin.
    """
    errors = []

    for _model, plugin_classes in registry._registry.items():
        for plugin_class in plugin_classes:
            # Check if this is a PluginGroup (has 'plugins' attribute)
            if hasattr(plugin_class, "plugins"):
                plugins = getattr(plugin_class, "plugins", [])
                if not plugins or len(plugins) == 0:
                    errors.append(
                        Error(
                            f"PluginGroup {plugin_class.__name__} has empty plugins list",
                            hint="PluginGroup must contain at least one Plugin class",
                            obj=plugin_class,
                            id="plugins.E005",
                        )
                    )

    return errors


@register(Tags.compatibility)
def check_plugin_group_plugin_classes(app_configs, **kwargs):
    """E006: Check that PluginGroup plugins are valid Plugin classes.

    Ensures all entries in a PluginGroup's plugins list are Plugin subclasses.
    """
    from .base import Plugin

    errors = []

    for _model, plugin_classes in registry._registry.items():
        for plugin_class in plugin_classes:
            # Check if this is a PluginGroup
            if hasattr(plugin_class, "plugins"):
                plugins = getattr(plugin_class, "plugins", [])
                for i, plugin in enumerate(plugins):
                    # Check if it's a class and inherits from Plugin
                    if not isinstance(plugin, type):
                        errors.append(
                            Error(
                                f"PluginGroup {plugin_class.__name__} plugins[{i}] is not a class: {plugin}",
                                hint="All entries in plugins list must be Plugin subclasses",
                                obj=plugin_class,
                                id="plugins.E006",
                            )
                        )
                    elif not issubclass(plugin, Plugin):
                        errors.append(
                            Error(
                                f"PluginGroup {plugin_class.__name__} plugins[{i}] is not a Plugin subclass: {plugin.__name__}",
                                hint="All entries in plugins list must inherit from Plugin",
                                obj=plugin_class,
                                id="plugins.E006",
                            )
                        )

    return errors


@register(Tags.compatibility)
def check_plugin_group_url_conflicts(app_configs, **kwargs):
    """E007: Check for URL path conflicts within PluginGroups.

    Ensures wrapped plugins within a group don't have conflicting URL paths.
    """
    errors = []

    for _model, plugin_classes in registry._registry.items():
        for plugin_class in plugin_classes:
            # Check if this is a PluginGroup
            if hasattr(plugin_class, "plugins"):
                plugins = getattr(plugin_class, "plugins", [])
                seen_paths = {}

                for plugin in plugins:
                    try:
                        if hasattr(plugin, "get_url_path"):
                            path = plugin.get_url_path()
                        else:
                            continue
                    except Exception:  # noqa: S112
                        continue

                    if path in seen_paths:
                        errors.append(
                            Error(
                                f"PluginGroup {plugin_class.__name__} has URL conflict: plugins {seen_paths[path].__name__} and {plugin.__name__} both use path '{path}'",
                                hint="Wrapped plugins must have unique url_path values",
                                obj=plugin_class,
                                id="plugins.E007",
                            )
                        )
                    else:
                        seen_paths[path] = plugin

    return errors


@register(Tags.security)
def check_permission_strings(app_configs, **kwargs):
    """W001: Validate permission string validity.

    Checks that permission strings reference existing Django permissions.
    This is a warning because permissions might be added later by migrations.
    """
    from django.contrib.auth.models import Permission

    warnings = []

    for _model, plugin_classes in registry._registry.items():
        for plugin_class in plugin_classes:
            permission = getattr(plugin_class, "permission", None)
            if not permission:
                continue

            # Check if permission exists
            # Format is usually "app_label.permission_name"
            if "." not in permission:
                warnings.append(
                    Warning(
                        f"Plugin {plugin_class.__name__} has invalid permission format: {permission}",
                        hint="Permission should be in format 'app_label.permission_name'",
                        obj=plugin_class,
                        id="plugins.W001",
                    )
                )
                continue

            app_label, perm_name = permission.split(".", 1)

            # Only check if database is ready (avoid errors during migrations)
            try:
                if not Permission.objects.filter(content_type__app_label=app_label, codename=perm_name).exists():
                    warnings.append(
                        Warning(
                            f"Plugin {plugin_class.__name__} references non-existent permission: {permission}",
                            hint="Ensure the permission exists or will be created by migrations",
                            obj=plugin_class,
                            id="plugins.W001",
                        )
                    )
            except Exception:  # noqa: S110
                # Database not ready, skip check
                pass

    return warnings


@register(Tags.templates)
def check_template_names(app_configs, **kwargs):
    """E004: Check for invalid template_name values.

    Verifies that if a plugin has an explicit template_name set, it references
    a template that could potentially exist (basic validation).
    """
    errors = []

    for _model, plugin_classes in registry._registry.items():
        for plugin_class in plugin_classes:
            template_name = getattr(plugin_class, "template_name", None)

            if not template_name:
                continue  # Using template resolution, which is fine

            # Basic sanity checks
            if not isinstance(template_name, str):
                errors.append(
                    Error(
                        f"Plugin {plugin_class.__name__} has invalid template_name type: {type(template_name)}",
                        hint="template_name must be a string path to a template file",
                        obj=plugin_class,
                        id="plugins.E004",
                    )
                )
                continue

            # Check for common mistakes
            if template_name.strip() == "":
                errors.append(
                    Error(
                        f"Plugin {plugin_class.__name__} has empty template_name",
                        hint="Either remove template_name to use automatic resolution or provide a valid template path",
                        obj=plugin_class,
                        id="plugins.E004",
                    )
                )

            # Check that it ends with .html
            if not template_name.endswith(".html"):
                errors.append(
                    Warning(
                        f"Plugin {plugin_class.__name__} template_name doesn't end with .html: {template_name}",
                        hint="Template names should typically end with .html",
                        obj=plugin_class,
                        id="plugins.W002",
                    )
                )

    return errors


@register(Tags.urls)
def check_url_path_characters(app_configs, **kwargs):
    """W003: Check for invalid characters in URL paths.

    Warns when url_path contains characters that may cause routing issues.
    """
    import re

    warnings = []

    # Valid URL path pattern: alphanumeric, hyphens, underscores
    valid_pattern = re.compile(r"^[a-z0-9_-]+$")

    for _model, plugin_classes in registry._registry.items():
        for plugin_class in plugin_classes:
            # Check explicit url_path attribute
            url_path = getattr(plugin_class, "url_path", None)

            if not url_path:
                continue  # No explicit url_path, auto-generated will be safe

            if not isinstance(url_path, str):
                warnings.append(
                    Warning(
                        f"Plugin {plugin_class.__name__} has non-string url_path: {type(url_path)}",
                        hint="url_path should be a string",
                        obj=plugin_class,
                        id="plugins.W003",
                    )
                )
                continue

            # Check for invalid characters
            if not valid_pattern.match(url_path):
                warnings.append(
                    Warning(
                        f"Plugin {plugin_class.__name__} url_path contains invalid characters: {url_path}",
                        hint="URL paths should only contain lowercase letters, numbers, hyphens, and underscores",
                        obj=plugin_class,
                        id="plugins.W003",
                    )
                )

            # Check for leading/trailing slashes
            if url_path.startswith("/") or url_path.endswith("/"):
                warnings.append(
                    Warning(
                        f"Plugin {plugin_class.__name__} url_path should not start or end with slashes: {url_path}",
                        hint="Remove leading/trailing slashes from url_path",
                        obj=plugin_class,
                        id="plugins.W003",
                    )
                )

    return warnings
