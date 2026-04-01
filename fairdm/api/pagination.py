"""FairDM API pagination classes."""

from rest_framework.pagination import PageNumberPagination


class FairDMPagination(PageNumberPagination):
    """Standard pagination for FairDM API endpoints.

    Response format::

        {
            "count": 100,
            "next": "http://example.com/api/v1/projects/?page=2",
            "previous": null,
            "results": [...]
        }

    Query parameters:
        - ``page``: page number (1-based)
        - ``page_size``: number of results per page (max 100)
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100
