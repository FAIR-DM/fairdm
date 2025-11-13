"""Custom menu renderers for FairDM navigation."""

from flex_menu.renderers import BaseRenderer


class NavbarRenderer(BaseRenderer):
    """Renderer for desktop navbar navigation.

    Maps menu item types to their corresponding navbar templates.
    Supports regular links, dropdowns with headers and items.
    """

    templates = {
        0: {"default": "fairdm/menus/navbar/menu.html"},
        1: {
            "parent": "fairdm/menus/navbar/nav_dropdown.html",
            "leaf": "fairdm/menus/navbar/nav_link.html",
        },
        "default": {
            "parent": "fairdm/menus/navbar/nav_dropdown.html",
            "leaf": "fairdm/menus/navbar/dropdown_item.html",
        },
    }


class MobileNavbarRenderer(BaseRenderer):
    """Renderer for mobile navbar navigation.

    Uses mobile-specific templates that work better on small screens.
    """

    templates = {
        0: {"default": "fairdm/menus/navbar/mobile_menu.html"},
        1: {
            "parent": "fairdm/menus/navbar/mobile_nav_dropdown.html",
            "leaf": "fairdm/menus/navbar/mobile_nav_link.html",
        },
        "default": {
            "parent": "fairdm/menus/navbar/mobile_nav_dropdown.html",
            "leaf": "fairdm/menus/navbar/mobile_dropdown_item.html",
        },
    }


class SidebarRenderer(BaseRenderer):
    """Renderer for sidebar/detail page menus.

    Used for plugin menus in detail views with categorized sections.
    """

    templates = {
        0: {"default": "fairdm/menus/sidebar/menu.html"},
        1: {
            "parent": "fairdm/menus/sidebar/section.html",
            "leaf": "fairdm/menus/sidebar/item.html",
        },
        "default": {
            "parent": "fairdm/menus/sidebar/section.html",
            "leaf": "fairdm/menus/sidebar/item.html",
        },
    }
