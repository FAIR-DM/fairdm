"""Markdown rendering with HTML sanitisation."""

import markdown
import nh3
from django.conf import settings


def markdownify(content):
    """Render markdown to HTML that is safe to insert into a page.

    Markdown authored by users may contain raw HTML, so the rendered output is sanitised before
    it is returned: scripts, event-handler attributes and dangerous URL schemes are stripped, and
    links gain ``rel="noopener noreferrer"``. The extensions applied come from
    ``settings.FAIRDM_MARKDOWN_EXTENSIONS``.

    Both the ``safe_markdown`` template filter and the editor's live preview render through this
    function, so a preview always matches the page.

    Args:
        content: The markdown source. ``None`` renders as an empty string.

    Returns:
        The sanitised HTML.

    Example:
        >>> markdownify("**bold** <script>alert(1)</script>")
        '<p><strong>bold</strong> </p>'
    """
    html = markdown.markdown(
        content or "", extensions=settings.FAIRDM_MARKDOWN_EXTENSIONS
    )
    return nh3.clean(html)
