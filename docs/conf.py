import html
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
os.environ.setdefault("DATABASE_URL", "postgresql://username:password@hostname:5555/database_name")

sys.path.append(str(BASE_DIR / "tests"))


from docs.conf import *

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
        "header_links_before_dropdown": 4,
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
    "sphinx_copybutton",
    "sphinxext.opengraph",
    # "autodoc2",
    # "sphinx_comments",
    "myst_parser",
    # "sphinx_tippy",
]

epub_theme = html_theme
epub_title = "FairDM Documentation"
epub_author = "FAIR-DM"
epub_publisher = "FAIR-DM"
epub_copyright = "2023, FAIR-DM"

