"""FairDM API pagination classes."""

from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.settings import api_settings


class FairDMPagination(PageNumberPagination):
    """Standard pagination for FairDM API endpoints.

    The default page size is ``REST_FRAMEWORK["PAGE_SIZE"]`` and the largest a caller may ask
    for is ``FAIRDM_API_MAX_PAGE_SIZE``. Both are read when a request is answered, so a change
    to either setting changes the API.

    Response format::

        {
            "count": 100,
            "next": "http://example.com/api/v1/projects/?page=2",
            "previous": null,
            "results": [...],
        }

    Query parameters:
        - ``page``: page number (1-based)
        - ``page_size``: number of results per page, up to the largest page size
    """

    page_size_query_param = "page_size"

    # Properties, not class attributes, so each is read from the settings when used.
    @property
    def page_size(self) -> int | None:  # type: ignore[override]
        """The number of records in a page when the caller does not ask for another."""
        return api_settings.PAGE_SIZE

    @property
    def max_page_size(self) -> int | None:  # type: ignore[override]
        """The most records a caller may ask for in one page."""
        return settings.FAIRDM_API_MAX_PAGE_SIZE  # type: ignore[misc,no-any-return]
