"""The portal's brand images, for django-mvp's ``MVP_CONFIG["brand"]`` resolvers."""

from django.templatetags.static import static
from mvp.utils import icon_url as mvp_icon_url

FAVICON_HEIGHT = "16px"
"""The height django-mvp's page head asks for, and nothing else does."""


def icon_url(request, height, theme):
    """Return the favicon for the page head and the brand icon everywhere else.

    The symbol is redrawn for a browser tab, where the gaps of the full-size drawing would blur.

    Args:
        request: The current request, or ``None``.
        height: The height the caller asked for.
        theme: ``"light"`` or ``"dark"``.

    Returns:
        The image's URL.
    """
    if height == FAVICON_HEIGHT:
        return static("brand/favicon.svg")
    return mvp_icon_url(request, height, theme)
