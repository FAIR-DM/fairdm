"""The generated API documentation: what the schema says about the portal, and what it leaves out.

``describe_api`` is a drf-spectacular postprocessing hook named in
``SPECTACULAR_SETTINGS["POSTPROCESSING_HOOKS"]``. It appends to the schema's description how
to authenticate, the limits and the page sizes, read from the settings and the pagination
class at the moment the schema is generated, so the text cannot drift from what the portal does.
"""

from __future__ import annotations

from typing import Any, cast

from drf_spectacular.contrib.django_filters import DjangoFilterExtension
from rest_framework.settings import api_settings


class ApiDescription:
    """The part of the schema's description that comes from the portal's settings."""

    def render(self) -> str:
        """Write the sections on authentication, limits and paging.

        Returns:
            Markdown that follows the description a portal writes.
        """
        return "\n\n".join((self.authentication(), self.limits(), self.paging()))

    def authentication(self) -> str:
        """Describe how a caller proves who they are.

        Returns:
            A Markdown section on tokens and sessions.
        """
        return (
            "### Authentication\n\n"
            "Most data can be read without signing in. To create, change or delete "
            "records, or to read records that are not public, identify yourself in one "
            "of two ways:\n\n"
            "- **Token**: create one on your account pages, under API tokens, and send it "
            "with every request as `Authorization: Token <your-token>`. A token is shown "
            "once, when it is created.\n"
            "- **Session**: a page that is part of the portal can call the API with the "
            "signed-in person's session, sending the CSRF token with each write."
        )

    def limits(self) -> str:
        """List the request limits as the settings hold them.

        Returns:
            A Markdown section with one line per configured rate, or an empty section
            when no rate is set.
        """
        rates = api_settings.DEFAULT_THROTTLE_RATES or {}
        lines = [f"- `{scope}`: {rate}" for scope, rate in rates.items() if rate]
        if not lines:
            return "### Limits\n\nThe portal sets no limit on requests."
        return (
            "### Limits\n\n"
            "A caller past a limit is answered `429` with a `Retry-After` header "
            "saying how long to wait.\n\n" + "\n".join(lines)
        )

    def paging(self) -> str:
        """State the default and the largest page size of a list.

        Returns:
            A Markdown section read from the configured pagination class, or one saying a list
            is not paged when the portal sets none.
        """
        pagination_class = cast("Any", api_settings.DEFAULT_PAGINATION_CLASS)
        if pagination_class is None:
            return "### Paging\n\nA list returns all its records in one response."
        pagination = pagination_class()
        return (
            "### Paging\n\n"
            f"A list returns {pagination.page_size} records a page unless "
            f"`{pagination.page_size_query_param}` asks for another number, up to "
            f"{pagination.max_page_size}. Follow `next` in the response to read the "
            f"following page."
        )


def describe_api(result: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Append the portal's authentication, limits and page sizes to the schema's description.

    Args:
        result: The generated schema.
        **kwargs: The generator, request and ``public`` flag drf-spectacular passes to a hook.

    Returns:
        The schema, with its ``info.description`` extended.
    """
    info = result.setdefault("info", {})
    written = info.get("description", "").rstrip()
    info["description"] = "\n\n".join(
        filter(None, (written, ApiDescription().render()))
    )
    return result


class FairDMFilterExtension(DjangoFilterExtension):
    """Describe a list's filters as the API applies them.

    A filter on a relation that has no short identifier is removed when the filter set is
    built for a request, so the schema leaves it out too.
    """

    target_class = "fairdm.api.filters.FairDMFilterBackend"
    # Ahead of the extension for django-filter, which also matches this backend.
    priority = 1

    def resolve_filter_field(
        self, auto_schema, model, filterset_class, field_name, filter_field
    ):
        """Describe a filter unless the API drops it when it builds the filter set."""
        drops = getattr(filterset_class, "drops", None)
        if drops is not None and drops(filter_field):
            return []
        return super().resolve_filter_field(
            auto_schema, model, filterset_class, field_name, filter_field
        )
