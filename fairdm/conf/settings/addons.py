"""Third-Party Add-on Configurations

Consolidated settings for third-party Django packages and FairDM-specific features.

This is the production baseline. Environment-specific overrides in local.py/staging.py.
"""

# =============================================================================
# ACTIVITY STREAM
# https://django-activity-stream.readthedocs.io
# =============================================================================

ACTSTREAM_SETTINGS = {
    # 'MANAGER': 'myapp.managers.MyActionManager',
    # 'FETCH_RELATIONS': True,
    "USE_JSONFIELD": True,
}

# =============================================================================
# CONFIGURATION & FEATURE FLAGS
# https://django-solo.readthedocs.io
# https://waffle.readthedocs.io
# =============================================================================

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

# =============================================================================
# NAVIGATION MENUS
# https://django-flex-menus.readthedocs.io
# =============================================================================

# Custom renderers for FairDM navigation menus
FLEX_MENUS = {
    "renderers": {
        "adminlte": "mvp.renderers.AdminLTERenderer",
        "nav": "mvp.renderers.NavRenderer",
        "navbar": "mvp.renderers.NavbarRenderer",
        "mobile_navbar": "mvp.renderers.MobileNavbarRenderer",
        "sidebar": "mvp.renderers.SidebarRenderer",
        "dropdown": "mvp.renderers.DropdownRenderer",
    }
}

# =============================================================================
# ICON SYSTEM
# https://django-easy-icons.readthedocs.io
# =============================================================================

EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {
            "tag": "i",
        },
        "packs": [
            "mvp.utils.BS5_ICONS",
        ],
        "icons": {
            # Core Actions
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
            # Navigation
            "menu_vertical": "bi bi-three-dots-vertical",
            "menu_horizontal": "bi bi-three-dots",
            "chevron_left": "bi bi-chevron-left",
            "chevron_right": "bi bi-chevron-right",
            "chevron_up": "bi bi-chevron-up",
            "chevron_down": "bi bi-chevron-down",
            "chevron_expand": "bi bi-chevron-expand",
            "arrow_left": "bi bi-arrow-left",
            "arrow_up": "bi bi-arrow-up",
            "arrow_down": "bi bi-arrow-down",
            "external_link": "bi bi-box-arrow-up-right",
            # Search & Filter
            "filter_active": "bi bi-funnel-fill",
            "submit": "bi bi-check-lg",
            "funding": "bi bi-cash-coin",
            # Data & Content Types
            "project": "bi bi-layers",
            "dataset": "bi bi-folder",
            "sample": "bi bi-droplet",
            "measurement": "bi bi-rulers",
            "data": "bi bi-table",
            "chart": "bi bi-bar-chart",
            "analytics": "bi bi-graph-up",
            "activity": "bi bi-activity",
            "timeline": "bi bi-clock-history",
            # Charts & Visualization
            "bar-chart": "bi bi-bar-chart",
            "line-chart": "bi bi-graph-up",
            "pie-chart": "bi bi-pie-chart",
            "scatter-plot": "bi bi-broadcast",
            "heatmap": "bi bi-grid-3x3-gap",
            "histogram": "bi bi-bar-chart-steps",
            # File Operations
            "download": "bi bi-download",
            "upload": "bi bi-upload",
            "import": "bi bi-box-arrow-in-down",
            "export": "bi bi-box-arrow-up",
            "file": "bi bi-file-earmark",
            "file_text": "bi bi-file-text",
            # People & Organizations
            "member": "bi bi-person-fill",
            "organization": "bi bi-building",
            # Location & Geography
            "location": "bi bi-geo-alt",
            "map": "bi bi-map",
            "globe": "bi bi-globe",
            # Metadata & Info
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
            "link": "bi bi-link-45deg",
            "relationships": "bi bi-diagram-3",
            # Settings & Configuration
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
            # Media
            "image": "bi bi-image",
            "images": "bi bi-images",
            "rotate": "bi bi-arrow-clockwise",
            # Status & Indicators
            "success": "bi bi-check-circle",
            "error": "bi bi-x-circle",
            "warning": "bi bi-exclamation-triangle",
            "pending": "bi bi-clock",
            "loading": "bi bi-arrow-repeat",
            # Misc
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
            # Theme
            # Social & External
            "linkedin": "bi bi-linkedin",
            "whatsapp": "bi bi-whatsapp",
            "x_twitter": "bi bi-twitter-x",
            # Auth
            "login": "bi bi-box-arrow-in-right",
            "password": "bi bi-key",
            "mfa": "bi bi-shield-lock",
            "account": "bi bi-person-circle",
            "sessions": "bi bi-clock-history",
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

# =============================================================================
# IMPORT/EXPORT
# https://django-import-export.readthedocs.io
# =============================================================================

from import_export.formats.base_formats import DEFAULT_FORMATS, CSV, TSV, XLS, XLSX, ODS
from fairdm.contrib.import_export.formats import LaTex

IMPORT_EXPORT_FORMATS = [LaTex, *DEFAULT_FORMATS]

IMPORT_FORMATS = [CSV, TSV, XLS, XLSX, ODS]

# =============================================================================
# MARKDOWN EDITOR
# https://martor.readthedocs.io
# =============================================================================

MARTOR_THEME = "bootstrap"

# Global martor settings
# Input: string boolean, `true/false`
MARTOR_ENABLE_CONFIGS = {
    "emoji": "false",  # to enable/disable emoji icons.
    "imgur": "false",  # to enable/disable imgur/custom uploader.
    "mention": "false",  # to enable/disable mention
    "jquery": "false",  # to include/revoke jquery (require for admin default django)
    "living": "false",  # to enable/disable live updates in preview
    "spellcheck": "false",  # to enable/disable spellcheck in form textareas
    "hljs": "false",  # to enable/disable hljs highlighting in preview
}

# To show the toolbar buttons
MARTOR_TOOLBAR_BUTTONS = [
    "bold",
    "italic",
    "horizontal",
    # "heading",
    # "pre-code",
    # "blockquote",
    "unordered-list",
    "ordered-list",
    # "link",
    # "image-link",
    # "image-upload",
    # "emoji",
    "direct-mention",
    # "toggle-maximize",
    "help",
]

# To setup the martor editor with title label or not (default is False)
MARTOR_ENABLE_LABEL = True

# Disable admin style when using custom admin interface e.g django-grappelli (default is True)
MARTOR_ENABLE_ADMIN_CSS = False

# Imgur API Keys (NOT USED)
# MARTOR_IMGUR_CLIENT_ID = "your-client-id"
# MARTOR_IMGUR_API_KEY = "your-api-key"

# Markdownify
MARTOR_MARKDOWNIFY_FUNCTION = "martor.utils.markdownify"  # default
MARTOR_MARKDOWNIFY_URL = "/martor/markdownify/"  # default

# Delay in milliseconds to update editor preview when in living mode.
# MARTOR_MARKDOWNIFY_TIMEOUT = 0  # update the preview instantly
# or:
MARTOR_MARKDOWNIFY_TIMEOUT = 1000  # default

# Markdown extensions (default)
MARTOR_MARKDOWN_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.nl2br",
    "markdown.extensions.smarty",
    # "markdown.extensions.fenced_code",
    "markdown.extensions.sane_lists",
    # Custom markdown extensions.
    "martor.extensions.urlize",
    "martor.extensions.del_ins",  # ~~strikethrough~~ and ++underscores++
    # "martor.extensions.mention",  # to parse markdown mention
    # "martor.extensions.emoji",  # to parse markdown emoji
    # "martor.extensions.mdx_video",  # to parse embed/iframe video
    "martor.extensions.escape_html",  # to handle the XSS vulnerabilities
    # "martor.extensions.mdx_add_id",  # to parse id like {#this_is_id}
]

# Markdown Extensions Configs
MARTOR_MARKDOWN_EXTENSION_CONFIGS = {}

# Markdown urls
MARTOR_UPLOAD_URL = "/martor/uploader/"  # default

MARTOR_SEARCH_USERS_URL = "/martor/search-user/"  # default

# Markdown Extensions
MARTOR_MARKDOWN_BASE_EMOJI_URL = ""  # Completely disables the endpoint
# MARTOR_MARKDOWN_BASE_MENTION_URL = "https://python.web.id/author/"  # please change this to your domain

# If you need to use your own themed "bootstrap" or "semantic ui" dependency
# replace the values with the file in your static files dir
# MARTOR_ALTERNATIVE_JS_FILE_THEME = "semantic-themed/semantic.min.js"  # default None
MARTOR_ALTERNATIVE_CSS_FILE_THEME = "x"  # default None
# MARTOR_ALTERNATIVE_JQUERY_JS_FILE = "jquery/dist/jquery.min.js"  # default None

# URL schemes that are allowed within links
ALLOWED_URL_SCHEMES = [
    # "file",
    # "ftp",
    # "ftps",
    # "http",
    "https",
    # "irc",
    # "mailto",
    # "sftp",
    # "ssh",
    # "tel",
    # "telnet",
    # "tftp",
    # "vnc",
    # "xmpp",
]

# https://gist.github.com/mrmrs/7650266
ALLOWED_HTML_TAGS = [
    # "a",
    "abbr",
    "b",
    "blockquote",
    "br",
    # "cite",
    # "code",
    # "command",
    "dd",
    # "del",
    "dl",
    "dt",
    "em",
    # "fieldset",
    # "h1",
    # "h2",
    # "h3",
    # "h4",
    # "h5",
    # "h6",
    "hr",
    "i",
    # "iframe",
    # "img",
    # "input",
    # "ins",
    # "kbd",
    # "label",
    # "legend",
    "li",
    "ol",
    # "optgroup",
    # "option",
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

# https://github.com/decal/werdlists/blob/master/html-words/html-attributes-list.txt
ALLOWED_HTML_ATTRIBUTES = [
    # "alt",
    # "class",
    # "color",
    # "colspan",
    # "datetime",  # "data",
    # "height",
    # "href",
    # "id",
    # "name",
    # "reversed",
    # "rowspan",
    # "scope",
    # "src",
    # "style",
    # "title",
    # "type",
    # "width",
]

# =============================================================================
# SEO & META TAGS
# https://django-meta.readthedocs.io
# =============================================================================

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
# META_INCLUDE_KEYWORDS = FAIRDM["database"]["keywords"]
""""""
# META_DEFAULT_KEYWORDS = FAIRDM["database"]["keywords"]
""""""

# =============================================================================
# FAIRDM-SPECIFIC SETTINGS
# FairDM framework configuration
# =============================================================================

FAIRDM_ALLOWED_IDENTIFIERS = {
    "samples.Sample": {
        "IGSN": "https://igsn.org/",
        # "DOI": "https://doi.org/",
    },
    "contributors.Person": {
        "ORCID": "https://orcid.org/",
        # "researcher_id": "https://app.geosamples.org/sample/researcher_id/",
        # "scopus_id": "https://app.geosamples.org/sample/scopus_id/",
        # "researchgate_id": "https://app.geosamples.org/sample/researchgate_id/",
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
    "keyword_vocabularies": [
        # "fairdm_geo.vocabularies.cgi.geosciml.SimpleLithology",
        # "fairdm_geo.vocabularies.stratigraphy.GeologicalTimescale",
    ],
}

FAIRDM_PROJECT = {
    "keywords": [
        "fairdm.core.vocabularies.FairDMRoles",
        # "fairdm_geo.vocabularies.cgi.geosciml.SimpleLithology",
        # "fairdm_geo.vocabularies.stratigraphy.GeologicalTimescale",
    ],
}


FAIRDM_DEFAULT_LICENSE = "CC BY 4.0"

# =============================================================================
# PAGE CONFIGURATION
# django-mvp page-level settings
# =============================================================================

# Page configuration for django-mvp
PAGE_CONFIG = {
    # Site branding
    "brand": {
        "text": SITE_NAME,  # noqa: F821 - SITE_NAME is defined in apps.py
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

# =============================================================================
# THEME & UI
# pydata-sphinx-theme inspired configuration
# =============================================================================

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
    # "navbar_start": [
    #     "pst.components.navbar-logo",
    # ],
    # "navbar_center": [
    #     "pst.components.navbar-nav",
    # ],
    # "navbar_end": [
    #     "pst.components.theme-switcher",
    #     "pst.components.navbar-icon-links",
    #     "dac.sections.user-sidebar.toggle",
    # ],
    # "primary_sidebar_end": ["custom-template", "sidebar-ethical-ads"],
    # "article_footer_items": ["test", "test"],
    # "content_footer_items": ["test", "test"],
    "footer_start": ["copyright"],
    "footer_center": ["sphinx-version"],
    # "secondary_sidebar_items": {
    #     "**/*": ["page-toc", "edit-this-page", "sourcelink"],
    #     "examples/no-sidebar": [],
    # },
    # "switcher": {
    #     "json_url": json_url,
    #     "version_match": version_match,
    # },
    "back_to_top_button": True,
    # "search_bar": False,
    # "search_as_you_type": False,
}

html_sidebars = {
    "community/index": [
        "sidebar-nav-bs",
        "custom-template",
    ],  # This ensures we test for custom sidebars
    "examples/no-sidebar": [],  # Test what page looks like with no sidebar items
    "examples/persistent-search-field": ["search-field"],
    # Blog sidebars
    # ref: https://ablog.readthedocs.io/manual/ablog-configuration-options/#blog-sidebars
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
