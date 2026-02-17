"""Menu and tab data structures for plugin system."""

from dataclasses import dataclass


@dataclass
class Tab:
    """Represents a single tab entry for template rendering.

    Attributes:
        label: Display text for the tab
        icon: Icon identifier (e.g., "chart-bar", "pencil")
        url: Resolved URL for the tab link
        order: Sort position (lower values appear first)
        is_active: Whether this tab is the current page
    """

    label: str
    icon: str = ""
    url: str = ""
    order: int = 0
    is_active: bool = False
