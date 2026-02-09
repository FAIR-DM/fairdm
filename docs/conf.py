import html
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
os.environ.setdefault("DJANGO_ENV", "development")
os.environ.setdefault("DATABASE_URL", "postgresql://username:password@hostname:5555/database_name")

sys.path.append(str(BASE_DIR / "tests"))


from docs.conf import * # type: ignore

# https://sphinx-book-theme.readthedocs.io/en/stable/reference.html
# https://pydata-sphinx-theme.readthedocs.io/en/latest/user_guide/index.html
# html_theme_options.update(
#     {
#         "announcement": (
#             "⚠️FairDM is currently undergoing rapid development and the API may change without notice! ⚠️"
#         ),
#     }
# )
html_theme = "pydata_sphinx_theme"
html_show_sphinx = False
html_theme_options.update({
       "logo": {
            "image_light": "_static/fairdm_light.svg",
            "image_dark": "_static/fairdm_dark.svg",
        },
        "header_links_before_dropdown": 0,
        "navbar_align": "left",
        "secondary_sidebar_items": {
            "**": ["page-toc", "edit-this-page",],
            "about/*": [],
            "index": [],
        },
        "icon_links": [
        {
            # Label for this link
            "name": "GitHub",
            # URL where the link will redirect
            "url": "https://github.com/FAIR-DM/fairdm/",  # required
            # Icon class (if "type": "fontawesome"), or path to local image (if "type": "local")
            "icon": "fa-brands fa-github",
            # The type of image to be used (see below for details)
            "type": "fontawesome",
        }
   ]
})

html_context = {
    # "github_url": "https://github.com", # or your GitHub Enterprise site
    "github_user": "FAIR-DM",
    "github_repo": "fairdm",
    "github_version": "main",
    "doc_path": "docs",
}

# exclude_patterns = ["apidocs/index.rst"]

# # despite the fact that extensions is declared in docs/conf.py, and is definitely available here (see print(extensions)),
# # the build will not work without declaring the extensions variable here as well.
extensions = [
    "sphinx.ext.viewcode",
    "sphinx.ext.duration",
    # 'sphinx.ext.doctest',
    "sphinx.ext.todo",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    # "sphinx.ext.linkcheck",  # Not an extension - use `sphinx-build -b linkcheck` instead
    "sphinx_copybutton",
    "sphinxext.opengraph",
    # "autodoc2",
    # "sphinx_comments",
    "myst_parser",
    # "sphinx_tippy",
]

# Link checking configuration
linkcheck_ignore = [
    # Ignore localhost and example domains
    r'http://localhost:\d+/',
    r'http://127.0.0.1:\d+/',
    r'https?://example\.(com|org|net)',
    # Ignore temporary or flaky external sites (add as needed)
    # Ignore sites that consistently fail or are slow
    r'https://unesdoc\.unesco\.org/.*',  # Returns 403 Forbidden
    r'https://docs\.fairdm\.org.*',  # DNS resolution fails (domain not registered yet)
    r'https://vocabularies\.example\.org.*',  # Example domain
    r'https://github\.com/.*/discussions.*',  # GitHub discussions may not be enabled
]

# Treat internal link failures as hard errors
linkcheck_allowed_redirects = {}

# External links: check but don't fail build (warnings only handled in CI)
linkcheck_timeout = 10  # Reduced from 30 to speed up checks
linkcheck_retries = 1  # Reduced from 2 to speed up checks
linkcheck_workers = 10  # Increased from 5 to parallelize better

# MyST Parser configuration for cross-references
myst_enable_extensions = [
    "colon_fence",      # Allow ::: fence style
    "deflist",          # Definition lists
    "html_image",       # Parse HTML img tags
    # "linkify",          # Auto-link URLs (requires linkify-it-py package)
    "replacements",     # Text replacements
    "smartquotes",      # Smart quotes
    "substitution",     # Variable substitutions
    "tasklist",         # Task lists with [ ] and [x]
]

myst_heading_anchors = 3  # Auto-generate anchors for H1-H3

epub_theme = html_theme
epub_title = "FairDM Documentation"
epub_author = "FAIR-DM"
epub_publisher = "FAIR-DM"
epub_copyright = "2023, FAIR-DM"

# Use custom template for index page
html_additional_pages = {
    'index': 'index.html',
}
