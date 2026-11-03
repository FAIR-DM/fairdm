"""Plugins for contributor pages and for contributions on other records."""

from .organisation import *
from .overview import *
from .person import *
from .shared import *

# Specification 023 sketch: the Samples and Measurements tabs, registered on datasets, projects
# and contributors. Loaded here because this app is discovered after the core record apps.
from fairdm.core import record_lists  # noqa: E402, F401
