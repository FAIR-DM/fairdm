"""Third-party package settings and FairDM's own framework configuration.

Owns the consolidated settings for activity stream, solo, waffle, flex-menus, easy-icons,
import/export, django-markdownx and meta tags, plus FairDM's identifiers, coordinate fields,
dataset and project keywords and the MVP page shell. A portal supplies its own
``FAIRDM_CONFIG``/``PAGE_CONFIG`` branding and any additional identifier schemes under
``FAIRDM_ALLOWED_IDENTIFIERS``.

Not to be confused with ``fairdm/conf/addons.py``, which discovers addons.
"""

ACTSTREAM_SETTINGS = {
    "USE_JSONFIELD": True,
}

GET_SOLO_TEMPLATE_TAG_NAME = "site_config"
""""""

SOLO_CACHE = "default"
""""""

SOLO_CACHE_TIMEOUT = 60 * 5
""""""

WAFFLE_CREATE_MISSING_SWITCHES = True
""""""

WAFFLE_CREATE_MISSING_FLAGS = True
""""""

WAFFLE_CREATE_MISSING_SAMPELS = True
""""""

FLEX_MENUS = {
    "renderers": {
        "sidebar": "mvp.renderers.SidebarRenderer",
        "dock": "mvp.renderers.MobileFooterNavRenderer",
        "plugin-menu-renderer": "fairdm.contrib.plugins.menus.PluginMenuRenderer",
    }
}

MVP_CONFIG = {
    "layout": {
        "sidebar": {
            "title": "FairDM",
            "collapse": "icons",
        },
        # The sidebar drawer already carries the login and theme controls, so the default
        # navbar copies would double them.
        "navbar": {
            "desktop": {"end": []},
        },
    },
}

# Orbit's dashboard defaults to open access when DEBUG is False; dashboard_access restricts
# it to superusers in production. Override AUTH_CHECK to change who can view it.
ORBIT_CONFIG = {
    "AUTH_CHECK": "fairdm.conf.orbit.dashboard_access",
}

EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {
            "tag": "i",
        },
        "packs": [
            "mvp.utils.BS5_ICONS",
            # The allauth management pages draw their icons from this pack and raise
            # `IconNotFoundError` without it.
            "dac.icons.DAC_ICONS",
        ],
        "icons": {
            "add": "bi bi-plus-circle",
            "create": "bi bi-plus-circle",
            "edit": "bi bi-pencil",
            "update": "bi bi-pencil-square",
            "delete": "bi bi-trash",
            "remove": "bi bi-trash",
            "save": "bi bi-floppy",
            "cancel": "bi bi-x-circle",
            "close": "bi bi-x",
            "confirm": "bi bi-check-circle",
            "view": "bi bi-eye",
            "hide": "bi bi-eye-slash",
            "share": "bi bi-share",
            "menu_vertical": "bi bi-three-dots-vertical",
            "menu_horizontal": "bi bi-three-dots",
            "chevron_left": "bi bi-chevron-left",
            "chevron_right": "bi bi-chevron-right",
            "chevron_up": "bi bi-chevron-up",
            "chevron_down": "bi bi-chevron-down",
            "chevron_expand": "bi bi-chevron-expand",
            "arrow-left": "bi bi-arrow-left",
            "arrow_up": "bi bi-arrow-up",
            "arrow_down": "bi bi-arrow-down",
            "external_link": "bi bi-box-arrow-up-right",
            "filter_active": "bi bi-funnel-fill",
            "submit": "bi bi-check-lg",
            "funding": "bi bi-cash-coin",
            "project": "bi bi-layers",
            "dataset": "bi bi-folder",
            "sample": "bi bi-droplet",
            "measurement": "bi bi-rulers",
            "data": "bi bi-table",
            "chart": "bi bi-bar-chart",
            "analytics": "bi bi-graph-up",
            "activity": "bi bi-activity",
            "timeline": "bi bi-clock-history",
            "bar-chart": "bi bi-bar-chart",
            "line-chart": "bi bi-graph-up",
            "pie-chart": "bi bi-pie-chart",
            "scatter-plot": "bi bi-broadcast",
            "heatmap": "bi bi-grid-3x3-gap",
            "histogram": "bi bi-bar-chart-steps",
            "download": "bi bi-download",
            "upload": "bi bi-upload",
            "import": "bi bi-box-arrow-in-down",
            "export": "bi bi-box-arrow-up",
            "file": "bi bi-file-earmark",
            "file_text": "bi bi-file-text",
            "member": "bi bi-person-fill",
            "organization": "bi bi-building",
            "location": "bi bi-geo-alt",
            "map": "bi bi-map",
            "globe": "bi bi-globe",
            "info": "bi bi-info-circle",
            "help": "bi bi-question-circle",
            "documentation": "bi bi-book",
            "literature": "bi bi-journal-text",
            "description": "bi bi-file-text",
            "keywords": "bi bi-tags",
            "tag": "bi bi-tag",
            "calendar": "bi bi-calendar3",
            "date": "bi bi-calendar3",
            "time": "bi bi-clock",
            "identifier": "bi bi-fingerprint",
            "cite": "bi bi-quote",
            "license": "bi bi-c-circle",
            "link": "bi bi-link-45deg",
            "relationships": "bi bi-diagram-3",
            "preferences": "bi bi-sliders",
            "administration": "bi bi-tools",
            "permissions": "bi bi-shield-check",
            "verified": "bi bi-patch-check",
            "grid": "bi bi-grid",
            "list_view": "bi bi-list",
            "card_view": "bi bi-grid-3x2",
            "collapse": "bi bi-chevron-down",
            "expand": "bi bi-arrows-expand",
            "fullscreen": "bi bi-arrows-fullscreen",
            "fullscreen_exit": "bi bi-fullscreen-exit",
            "image": "bi bi-image",
            "images": "bi bi-images",
            "rotate": "bi bi-arrow-clockwise",
            "success": "bi bi-check-circle",
            "error": "bi bi-x-circle",
            "warning": "bi bi-exclamation-triangle",
            "pending": "bi bi-clock",
            "loading": "bi bi-arrow-repeat",
            "home": "bi bi-house",
            "dashboard": "bi bi-speedometer2",
            "email": "bi bi-envelope",
            "lock": "bi bi-lock",
            "unlock": "bi bi-unlock",
            "visible": "bi bi-eye",
            "private": "bi bi-eye-slash",
            "star": "bi bi-star",
            "star_filled": "bi bi-star-fill",
            "lightbulb": "bi bi-lightbulb",
            "box": "bi bi-box",
            "review": "bi bi-chat-square-text",
            "comment": "bi bi-chat",
            "statistics": "bi bi-bar-chart",
            "award": "bi bi-award",
            "cloud_check": "bi bi-cloud-check",
            "cloud-check": "bi bi-cloud-check",
            "database_fill": "bi bi-database-fill",
            "database-fill": "bi bi-database-fill",
            "linkedin": "bi bi-linkedin",
            "whatsapp": "bi bi-whatsapp",
            "x_twitter": "bi bi-twitter-x",
            "api": "bi bi-braces",
            "login": "bi bi-box-arrow-in-right",
            "logout": "bi bi-box-arrow-right",
            "signup": "bi bi-person-plus",
            "check": "bi bi-check",
            "password": "bi bi-key",
            "mfa": "bi bi-shield-lock",
            "account": "bi bi-person-circle",
            "sessions": "bi bi-clock-history",
            "overview": "bi bi-layout-text-sidebar-reverse",
        },
    },
    "svg": {
        "renderer": "easy_icons.renderers.SvgRenderer",
        "config": {
            "svg_dir": "icons",
            "default_attrs": {
                "height": "1em",
                "fill": "currentColor",
            },
        },
        "icons": {
            "download-xml": "filetype-xml.svg",
            "missing_image": "missing_image.svg",
            "orcid": "orcid/authenticated.svg",
            "orcid_unauthenticated": "orcid/unauthenticated.svg",
            "ORCID": "orcid/authenticated.svg",
            "organization_svg": "organization.svg",
            "spinner": "spinner.svg",
            "ror": "ror.svg",
            "user_svg": "user.svg",
            "ROR": "ror.svg",
        },
    },
}

from import_export.formats.base_formats import CSV, DEFAULT_FORMATS, ODS, TSV, XLS, XLSX

from fairdm.contrib.import_export.formats import LaTex

IMPORT_EXPORT_FORMATS = [LaTex, *DEFAULT_FORMATS]

IMPORT_FORMATS = [CSV, TSV, XLS, XLSX, ODS]

# Read by both the page renderer and the live preview, so the two never diverge.
FAIRDM_MARKDOWN_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.nl2br",
    "markdown.extensions.smarty",
    "markdown.extensions.sane_lists",
    "pymdownx.magiclink",
    "pymdownx.tilde",
]

MARKDOWNX_MARKDOWNIFY_FUNCTION = "fairdm.utils.markdown.markdownify"

ALLOWED_URL_SCHEMES = [
    "https",
]

ALLOWED_HTML_TAGS = [
    "abbr",
    "b",
    "blockquote",
    "br",
    "dd",
    "dl",
    "dt",
    "em",
    "hr",
    "i",
    "li",
    "ol",
    "p",
    "pre",
    "small",
    "span",
    "strong",
    "sub",
    "sup",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
]

ALLOWED_HTML_ATTRIBUTES = []

META_SITE_PROTOCOL = "https"
""""""
META_USE_TITLE_TAG = True
""""""
META_USE_SITES = True
""""""
META_USE_OG_PROPERTIES = True
""""""
META_USE_TWITTER_PROPERTIES = True
""""""
""""""
""""""

FAIRDM_ALLOWED_IDENTIFIERS = {
    "samples.Sample": {
        "IGSN": "https://igsn.org/",
    },
    "contributors.Person": {
        "ORCID": "https://orcid.org/",
    },
    "contributors.Organization": {
        "ROR": "https://ror.org/",
        "GRID": "https://www.grid.ac/institutes/",
        "Wikidata": "https://www.wikidata.org/wiki/",
        "ISNI": "https://isni.org/isni/",
        "Crossref Funder ID": "https://doi.org/",
    },
}

FAIRDM_X_COORD = {
    "decimal_places": 5,
    "max_digits": None,
}

FAIRDM_Y_COORD = {
    "decimal_places": 5,
    "max_digits": None,
}

FAIRDM_CRS = "EPSG:4326"

FAIRDM_DATASET = {
    "keyword_vocabularies": [],
}

FAIRDM_PROJECT = {
    "keywords": [
        "fairdm.core.vocabularies.FairDMRoles",
    ],
}

FAIRDM_DEFAULT_LICENSE = "CC BY 4.0"

PAGE_CONFIG = {
    "brand": {
        "text": SITE_NAME,  # noqa: F821 - SITE_NAME is defined in apps.py
        "image_light": "img/brand/logo.svg",
        "icon_light": "img/brand/icon.svg",
    },
    "sidebar": {
        # False is navbar-only mode; a breakpoint ('sm' to 'xxl') shows the sidebar in-flow.
        "show_at": False,
        "collapsible": True,
    },
    "navbar": {
        "fixed": False,
        # Only applies when sidebar.show_at is False. False hides the navbar menu.
        "menu_visible_at": "lg",
    },
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

FAIRDM_CONFIG = {
    "colors": {
        "primary": "#18366a",
        "secondary": "#8045e5",
    },
    "home": {
        "explore": [
            "fdm.dashboard.research-projects",
            "fdm.dashboard.latest-activity",
        ],
        "create": [
            "fdm.dashboard.create-project",
            "fdm.dashboard.create-dataset",
        ],
        "more": [
            "fdm.dashboard.login-signup",
            "fdm.dashboard.user-guide",
            "fdm.dashboard.fairdm-framework",
        ],
    },
    "external_links": [
        {
            "url": "https://fairdm.org/",
            "name": "FairDM Website",
        },
    ],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/FAIR-DM/fairdm",
            "icon": "fa-brands fa-github fa-lg",
        },
    ],
    "logo": {
        "text": "FairDM",
        "image_dark": "img/brand/fairdm.svg",
        "image_light": "img/brand/fairdm.svg",
    },
    "announcement": "",
    "footer_start": ["copyright"],
    "footer_center": ["sphinx-version"],
    "back_to_top_button": True,
}

html_sidebars = {
    "community/index": [
        "sidebar-nav-bs",
        "custom-template",
    ],
    "examples/no-sidebar": [],
    "examples/persistent-search-field": ["search-field"],
    "examples/blog/*": [
        "ablog/postcard.html",
        "ablog/recentposts.html",
        "ablog/tagcloud.html",
        "ablog/categories.html",
        "ablog/authors.html",
        "ablog/languages.html",
        "ablog/locations.html",
        "ablog/archives.html",
    ],
}

html_context = {
    "github_user": "pydata",
    "github_repo": "pydata-sphinx-theme",
    "github_version": "main",
    "doc_path": "docs",
}
