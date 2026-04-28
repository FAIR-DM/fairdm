from __future__ import annotations

from django_filters.views import FilterView
from meta.views import MetadataMixin
from mvp.views import MVPCreateView, MVPDeleteView, MVPDetailView, MVPTemplateView, MVPUpdateView
from mvp.views.list import MVPFilteredListView
from mvp.views.table import MVPTableViewMixin


class FairDMTemplateView(MetadataMixin, MVPTemplateView):
    pass


class FairDMListView(MetadataMixin, MVPFilteredListView):
    """
    The base class for displaying a list of objects within the FairDM framework.
    """

    paginate_by = 25
    grid = {"cols": 1, "gap": 2}


class FairDMDetailView(MetadataMixin, MVPDetailView):
    pass


class FairDMCreateView(MetadataMixin, MVPCreateView):
    """
    The base class for creating objects within the FairDM framework.
    """

    default_roles = []

    def form_valid(self, form: DatasetForm) -> HttpResponse:
        """Handle successful form submission and add the creator as a contributor.

        Args:
            form: The validated DatasetForm instance.

        Returns:
            HttpResponse: The response from the parent class.
        """
        response = super().form_valid(form)
        if self.default_roles and hasattr(self.object, "add_contributor"):
            self.object.add_contributor(self.request.user, with_roles=self.default_roles)
        return response


class FairDMUpdateView(MetadataMixin, MVPUpdateView):
    """
    The base class for creating objects within the FairDM framework.
    """


class FairDMDeleteView(MetadataMixin, MVPDeleteView):
    """
    The base class for deleting objects within the FairDM framework.
    """

    pass


class FairDMTableView(MetadataMixin, MVPTableViewMixin, FilterView):
    """
    A list view that displays objects in a table format. Expects the template to handle rendering the table.
    """

    pass
