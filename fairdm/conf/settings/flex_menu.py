"""Django Flex Menu configuration for FairDM."""

# Custom renderers for FairDM navigation menus
FLEX_MENUS = {
    "renderers": {
        "navbar": "mvp.renderers.NavbarRenderer",
        "mobile_navbar": "mvp.renderers.MobileNavbarRenderer",
        "sidebar": "mvp.renderers.SidebarRenderer",
        "dropdown": "mvp.renderers.DropdownRenderer",
    }
}
