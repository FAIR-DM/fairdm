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
