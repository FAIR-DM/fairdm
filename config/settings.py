import fairdm

fairdm.setup(
    apps=["fairdm_demo"],
    addons=["fairdm_discussions"],
)

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = False

# Home Page Configuration
HOME_PAGE_CONFIG = {
    "logo": True,  # Set to False to hide the logo
    "title": "Welcome to {site_name}",  # Set to False to hide title, use {site_name} placeholder
    "lead": "Discover, explore, and contribute to research data. Our platform enables FAIR data management practices.",  # Set to False to hide lead text
}

# Portal description shown in About section
PORTAL_DESCRIPTION = "This research data portal provides a collaborative platform for sharing and discovering FAIR (Findable, Accessible, Interoperable, and Reusable) research data. Our community brings together researchers, organizations, and institutions to advance open science."


FAIRDM_FACTORIES = {}
