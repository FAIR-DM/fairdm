"""Django Flex Menu configuration for FairDM."""

# Custom renderers for FairDM navigation menus
FLEX_MENUS = {
    "renderers": {
        "navbar": "cotton_layouts.renderers.NavbarRenderer",
        "mobile_navbar": "cotton_layouts.renderers.MobileNavbarRenderer",
        "sidebar": "cotton_layouts.renderers.SidebarRenderer",
        "dropdown": "cotton_layouts.renderers.DropdownRenderer",
    }
}
