# FairDM Theme

A reusable Django app providing the default theme for the FairDM framework.

## Overview

The `fairdm.contrib.theme` app contains all theme-related assets including:

- **Templates**: Base templates, Cotton components, partials, and page layouts
- **Static Files**: SCSS stylesheets, JavaScript, images, and vendor assets
- **Template Tags**: Custom template tags for theme functionality
- **Settings**: Default theme configuration

## Installation

The theme app is automatically included in FairDM projects. It's added to `INSTALLED_APPS` in your settings:

```python
INSTALLED_APPS = [
    # ...
    'fairdm.contrib.theme',
    'fairdm',
    # ...
]
```

**Important**: `fairdm.contrib.theme` must be listed **before** `fairdm` in `INSTALLED_APPS` to ensure template and static file precedence.

## Structure

```
fairdm/contrib/theme/
├── __init__.py
├── apps.py
├── settings.py              # Default theme configuration
├── static/
│   ├── fairdm/             # Main SCSS files
│   ├── js/                 # JavaScript files
│   ├── scss/               # Additional SCSS
│   ├── img/                # Theme images
│   └── vendor/             # Third-party assets
├── templates/
│   ├── base.html           # Root base template
│   ├── cotton/             # Cotton components
│   ├── fairdm/             # FairDM-specific templates
│   ├── pages/              # Page templates
│   ├── partials/           # Template partials
│   └── plugins/            # Plugin templates
└── templatetags/
    ├── __init__.py
    └── fairdm_theme.py     # Theme template tags
```

## Configuration

### Theme Settings

Default theme settings are defined in `fairdm.contrib.theme.settings`. Override these in your project's `settings.py`:

```python
# Home page configuration
HOME_PAGE_CONFIG = {
    "logo": True,
    "title": "Welcome to {site_name}",
    "lead": "Your custom lead text here.",
}

# Portal description
PORTAL_DESCRIPTION = "Your custom portal description."

# Main theme configuration
FAIRDM_CONFIG = {
    "colors": {
        "primary": "#your-color",
        "secondary": "#your-color",
    },
    "logo": {
        "text": "Your Site Name",
        "image_dark": "path/to/dark/logo.svg",
        "image_light": "path/to/light/logo.svg",
    },
    # ... more configuration options
}
```

### Template Tags

Load theme template tags in your templates:

```django
{% load fairdm_theme %}

{# Use theme template tags #}
{% is_active '/path/' %}
{% avatar_url contributor %}
{% normalize_doi doi_string %}
```

### Static Files

Theme static files are automatically collected during `collectstatic`. Reference them in templates:

```django
{% load static compress %}

{% compress css file fairdm %}
  <link rel="stylesheet" type="text/x-scss" href="{% static 'fairdm/fairdm.scss' %}" />
{% endcompress %}

<script src="{% static 'js/navbar.js' %}"></script>
<img src="{% static 'img/brand/fairdm.svg' %}" alt="Logo">
```

## Customization

### Override Templates

Create templates with the same path in your project to override theme templates:

```
your_project/
└── templates/
    └── base.html           # Overrides theme's base.html
```

### Extend Templates

Extend theme templates to customize specific blocks:

```django
{% extends "fairdm/base.html" %}

{% block content %}
  {# Your custom content #}
{% endblock %}
```

### Custom Styles

Add custom SCSS by creating your own stylesheet that imports theme variables:

```scss
@import "fairdm/variables";

// Your custom styles using theme variables
.my-component {
    color: $primary-color;
}
```

## Future Plans

This theme app will eventually be extracted into a standalone third-party package for use in non-FairDM Django projects. This will allow other projects to benefit from the FairDM theme and UI components.

## License

Same as the FairDM framework.
