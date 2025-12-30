"""Page configuration for django-mvp integration."""

# Page configuration for django-mvp
PAGE_CONFIG = {
    # Site branding
    "brand": {
        "text": SITE_NAME,  # noqa: F821 - SITE_NAME is defined in general.py
        "image_light": "img/brand/logo.svg",  # Logo for light theme
        # "image_dark": "img/brand/logo-dark.svg",  # Optional logo for dark theme
        "icon_light": "img/brand/icon.svg",  # Favicon for light theme
        # "icon_dark": "img/brand/icon-dark.svg",  # Optional favicon for dark theme
    },
    # Sidebar configuration
    "sidebar": {
        "show_at": False,  # False = navbar-only mode (sidebar always offcanvas)
        # Or set to 'sm', 'md', 'lg', 'xl', 'xxl' to show in-flow at that breakpoint
        "collapsible": True,  # Whether sidebar can collapse to icon-only mode when visible
        # "width": "280px",  # Optional: custom sidebar width (default: 260px)
    },
    # Navbar configuration
    "navbar": {
        "fixed": False,  # Whether navbar is fixed to top
        "menu_visible_at": "lg",  # Show navbar menu at this breakpoint (lg = 992px+)
        # Only applies when sidebar.show_at is False (navbar-only mode)
        # Set to False to never show navbar menu (sidebar toggle only)
        # Options: 'sm', 'md', 'lg', 'xl', 'xxl', or False
    },
    # Navigation bar actions (icons/links in the navbar)
    "actions": [
        {
            "icon": "theme_light",
            "text": "Toggle theme",
            "href": "#",
            "id": "themeToggle",
        },
        {
            "icon": "github",
            "text": "GitHub",
            "href": "https://github.com/FAIR-DM/fairdm",
            "target": "_blank",
        },
        {
            "icon": "documentation",
            "text": "Documentation",
            "href": "/docs/",
            "target": "_blank",
        },
    ],
}
