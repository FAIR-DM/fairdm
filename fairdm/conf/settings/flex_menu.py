"""Django Flex Menu configuration for FairDM."""

# Custom renderers for FairDM navigation menus
FLEX_MENUS = {
    "renderers": {
        # Desktop navbar renderer
        "navbar": "fairdm.menus.renderers.NavbarRenderer",
        # Mobile navbar renderer
        "mobile_navbar": "fairdm.menus.renderers.MobileNavbarRenderer",
        # Sidebar/detail menu renderer for plugin menus
        "sidebar": "fairdm.menus.renderers.SidebarRenderer",
    }
}
