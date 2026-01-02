# FairDM Theme Migration Guide

## Overview

As of FairDM version 2014.1, all theme-related assets (templates, static files, templatetags, and configuration) have been moved to a new reusable app: `fairdm.contrib.theme`.

This change allows the FairDM theme to be:
- More easily maintained and updated
- Reused in other Django projects
- Overridden and customized without modifying core FairDM files
- Eventually extracted as a standalone third-party package

## What Changed

### File Locations

**Before:**
- Templates: `fairdm/templates/`
- Static files: `fairdm/static/`
- Template tags: `fairdm/templatetags/fairdm.py`
- Theme config: `fairdm/conf/settings/theme_options.py` (directly defined)

**After:**
- Templates: `fairdm/contrib/theme/templates/`
- Static files: `fairdm/contrib/theme/static/`
- Template tags: `fairdm/contrib/theme/templatetags/fairdm_theme.py`
- Theme config: `fairdm/contrib/theme/settings.py` (imported by `fairdm/conf/settings/theme_options.py`)

### Configuration

Theme configuration is now centralized in `fairdm.contrib.theme.settings` with default values:

```python
# fairdm/contrib/theme/settings.py
HOME_PAGE_CONFIG = {...}
PORTAL_DESCRIPTION = "..."
FAIRDM_CONFIG = {...}
```

## Migration Steps for Existing Projects

### 1. Update INSTALLED_APPS (Automatic)

The theme app is automatically added to `INSTALLED_APPS` when you use `fairdm.setup()`. No action needed.

**Important:** `fairdm.contrib.theme` is placed **before** `fairdm` in `INSTALLED_APPS` to ensure proper template/static file precedence.

### 2. Update Custom Theme Settings (If Applicable)

If your project previously overrode theme settings in `config/settings.py`, these should continue to work as-is:

```python
# config/settings.py
# These still work - they override the theme app defaults
HOME_PAGE_CONFIG = {
    "logo": False,
    "title": "My Custom Title",
}

FAIRDM_CONFIG = {
    "colors": {
        "primary": "#custom-color",
    }
}
```

### 3. Update Template Tag Loads (If Needed)

The original `fairdm` template tag library still exists in `fairdm/templatetags/fairdm.py`. 

If you want to use the new theme-specific tags:

**Before:**
```django
{% load fairdm %}
```

**After (Optional):**
```django
{% load fairdm_theme %}
```

**Note:** For backward compatibility, both work the same way currently.

### 4. Update Custom Template Overrides

If your project overrides FairDM templates, no changes are needed! Django's template loader will still find your custom templates first.

Example structure remains the same:
```
your_project/
└── templates/
    └── base.html           # Still overrides theme's base.html
    └── fairdm/
        └── list_view.html  # Still overrides theme's fairdm/list_view.html
```

### 5. Update Static File References

Static file paths remain the same since the files maintain their relative paths within the `static/` directory:

```django
{% static 'fairdm/fairdm.scss' %}      {# Still works #}
{% static 'js/navbar.js' %}            {# Still works #}
{% static 'img/brand/fairdm.svg' %}    {# Still works #}
```

## Benefits of the Migration

1. **Cleaner separation**: Theme assets are separated from core framework logic
2. **Better reusability**: Theme can be used in other Django projects
3. **Easier customization**: Clear location for all theme-related files
4. **Future-proof**: Prepares for eventual extraction as standalone package
5. **Improved maintainability**: Theme updates won't affect core framework code

## Troubleshooting

### Templates Not Found

If templates are not found after the migration:

1. Verify `fairdm.contrib.theme` is in `INSTALLED_APPS`
2. Verify it's listed **before** `fairdm` in `INSTALLED_APPS`
3. Run `python manage.py collectstatic` to collect static files

### Static Files Not Loading

1. Ensure `fairdm.contrib.theme` is in `INSTALLED_APPS`
2. Run `python manage.py collectstatic`
3. Check that `STATIC_ROOT` and `STATIC_URL` are properly configured

### Settings Not Loading

If theme configuration is not being applied:

1. Check that `fairdm/conf/settings/theme_options.py` is being loaded
2. Verify your custom settings override the theme defaults correctly
3. Ensure `fairdm.setup()` is called in your main settings file

## Development Workflow

For developers working on the theme itself:

1. **Editing templates**: Edit files in `fairdm/contrib/theme/templates/`
2. **Editing styles**: Edit SCSS files in `fairdm/contrib/theme/static/fairdm/`
3. **Editing JavaScript**: Edit JS files in `fairdm/contrib/theme/static/js/`
4. **Editing template tags**: Edit `fairdm/contrib/theme/templatetags/fairdm_theme.py`
5. **Editing config**: Edit `fairdm/contrib/theme/settings.py`

## Future Plans

The `fairdm.contrib.theme` app will eventually be:
- Extracted into a standalone PyPI package (e.g., `django-fairdm-theme`)
- Made available for use in non-FairDM Django projects
- Independently versioned and maintained

## Questions or Issues?

If you encounter any issues after the theme migration, please:
1. Check this migration guide
2. Review the theme app README: `fairdm/contrib/theme/README.md`
3. Open an issue on the FairDM GitHub repository
