# Home Page

The home page is the first page that users see when they visit your portal. FairDM provides a configurable home page that you can customize through Django settings and templates.

## Configuration

You can configure the home page welcome section through the `HOME_PAGE_CONFIG` setting in your `settings.py` file:

```python
# config/settings.py

HOME_PAGE_CONFIG = {
    "logo": True,  # Set to False to hide the logo
    "title": "Welcome to {site_name}",  # Set to False to hide the title
    "lead": "Discover, explore, and contribute to research data. Our platform enables FAIR data management practices.",  # Set to False to hide the lead text
}
```

### Configuration Options

- **`logo`** (boolean): Controls whether the portal logo is displayed above the title. Set to `False` to hide the logo.
- **`title`** (string or False): The main heading text. Use `{site_name}` as a placeholder to include your site name. Set to `False` to hide the title completely.
- **`lead`** (string or False): The lead/subtitle text displayed below the title. Use `{site_name}` as a placeholder if needed. Set to `False` to hide the lead text completely.

### Example Configurations

**Minimal configuration (no logo, no lead):**
```python
HOME_PAGE_CONFIG = {
    "logo": False,
    "title": "Welcome",
    "lead": False,
}
```

**Custom branding:**
```python
HOME_PAGE_CONFIG = {
    "logo": True,
    "title": "{site_name} Research Portal",
    "lead": "A collaborative platform for sharing research data in the {site_name} community.",
}
```

**Default behavior:**
If you don't define `HOME_PAGE_CONFIG`, the following defaults are used:
```python
{
    "logo": True,
    "title": "Welcome to {site_name}",
    "lead": "Discover, explore, and contribute to research data. Our platform enables FAIR data management practices.",
}
```

## Template Customization

The default home page is a full screen slider using the [SwiperJS](https://swiperjs.com/) library in combination with the [Swiper Element](https://swiperjs.com/element) web components. This provides an attractive and modern web page that is responsive and easy to customise. To get started, we will have to override and extend the default `fairdm/home.html` template. 

Start by creating a .html file in your project's `templates` directory. This file should extend the `fairdm/base.html` template and include the `home_page.html` template tag. Here is an example of a custom home page template:


```html
{% extends "fairdm/home.html" %}
{% load static %}

{% block slides %}
{% endblock slides %}
```

If you were to reload the page now, you will see that the home page is completely empty. This is because our `slides` block has overridden the `slides` block in the default template. If you wish to keep the original slides, as well as create some custom slides, you can do so by including the `super` template tag. Here is an example of a custom home page template that includes the default slides:

```html
{% extends "fairdm/home.html" %}
{% load static %}

{% block slides %}
<!-- Add custom slides before defaults here -->
{{ block.super }}
<!-- Add custom slides after defaults here -->

{% endblock slides %}
```

## Creating a new slide

FairDM provides a few basic slides layouts that you can use to quickly and easily create your own slides that work well on any device. Let's start by creating a full screen landing page.

Inside your `slides` block, you can create a new slide by using the `slide` template tag. Here is an example of a full screen landing page slide:

```html
{% block slides %}
  <c-home.full-screen display="My research portal"
                      lead="{% trans 'Welcome to the my custom FairDM research portal. This is a community for like-minded researchers to share their work with others' %}"
                      slide_class="bg-primary" />
{% endblock slides %}
```

This will create a full screen slide with a title, subtitle (lead text), and a background color based on the primary color of your custom theme. You can adjust the background color to any of your custom theme colors using valid [Bootstrap 5 bg-* CSS classes](https://getbootstrap.com/docs/5.3/utilities/background/#background-color).



Each slide is a `Slide` object that can contain a title, subtitle, and image. You can customize the slides by editing the `home_page_slides` fixture in your project's `fixtures` directory.