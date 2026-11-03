"""Views for the measurement pages that are not registered plugins."""

from django.urls import reverse
from django.utils.encoding import escape_uri_path
from django.views.generic import RedirectView


class FormerAddressRedirect(RedirectView):
    """Send an address under ``/measurement/<uuid>/``, where a measurement's pages used to live,
    to the same page under ``/measurements/<uuid>/``.

    It looks at no record. The page it leads to decides who may see the measurement, so a private
    measurement and an address that does not exist get the same answer here.
    """

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        """Return the record's address with the rest of the path and the query string kept."""
        url = reverse("measurement:overview", kwargs={"uuid": kwargs["uuid"]})
        url += escape_uri_path(kwargs["rest"])
        query = self.request.META.get("QUERY_STRING", "")
        return f"{url}?{query}" if query else url
