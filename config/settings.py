"""Settings for the demo portal."""

import fairdm

fairdm.setup(
    apps=["demo"],
)

# Set `logo`, `title` or `lead` to False to hide it. `title` accepts a {site_name} placeholder.
HOME_PAGE_CONFIG = {
    "logo": True,
    "title": "Welcome to {site_name}",
    "lead": "Discover, explore and contribute to FAIR research data. This platform is FAIR by design, not as an afterthought.",
}

PORTAL_DESCRIPTION = "This research data portal provides a collaborative platform for sharing and discovering FAIR (Findable, Accessible, Interoperable, and Reusable) research data. Our community brings together researchers, organizations, and institutions to advance open science."


FAIRDM_FACTORIES = {}

# FairDM's vocabularies are loaded from the copies in the test fixtures, so neither the demo nor
# the test suite fetches anything over the network.
vocabulary_files = BASE_DIR / "tests" / "fixtures" / "vocabularies"  # noqa: F821

CONTROLLED_VOCABULARIES = {
    slug: {"source": vocabulary_files / f"{slug}.ttl"}
    for slug in (
        "contributor-roles",
        "date-types",
        "description-types",
        "identifier-types",
        "organization-types",
        "project-status",
        "relation-types",
        "sample-relation-types",
        "sample-status",
    )
}
