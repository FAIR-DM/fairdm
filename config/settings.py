"""Settings for the demo portal."""

import fairdm

fairdm.setup(
    apps=["demo"],
)

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = False

# Set `logo`, `title` or `lead` to False to hide it. `title` accepts a {site_name} placeholder.
HOME_PAGE_CONFIG = {
    "logo": True,
    "title": "Welcome to {site_name}",
    "lead": "Discover, explore, and contribute to research data. Our platform enables FAIR data management practices.",
}

PORTAL_DESCRIPTION = "This research data portal provides a collaborative platform for sharing and discovering FAIR (Findable, Accessible, Interoperable, and Reusable) research data. Our community brings together researchers, organizations, and institutions to advance open science."


FAIRDM_FACTORIES = {}
