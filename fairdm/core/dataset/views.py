from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.utils.translation import gettext as _
from django.views.generic import DetailView

from fairdm.views import FairDMCreateView, FairDMListView

from .filters import DatasetFilter
from .forms import DatasetForm
from .models import Dataset


class DatasetDetailView(DetailView):
    """Detail view for Dataset model with plugin support.

    This view displays a dataset and makes plugin URLs available.
    """

    model = Dataset
    template_name = "dataset/dataset_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    context_object_name = "dataset"


class DatasetCreateView(LoginRequiredMixin, FairDMCreateView):
    """View for creating new Dataset instances.

    Handles dataset creation with automatic contributor assignment. The user
    who creates the dataset is automatically added as a Creator, ProjectMember,
    and ContactPerson. Supports pre-populating the project field from query params.
    """

    model = Dataset
    form_class = DatasetForm
    page_title = _("Create a Dataset")
    default_roles = ["Creator", "ProjectMember", "ContactPerson"]

    def get_initial(self) -> dict[str, Any]:
        """Get initial form data, pre-populating project if provided in query params.

        Returns:
            dict: Initial form data including project ID if available.
        """
        if self.request.GET.get("project"):
            project_id = self.request.GET["project"]
            if project_id.isdigit():
                return {"project": int(project_id)}
        return super().get_initial()

    def get_form_kwargs(self):
        """Add request to form kwargs for user-specific filtering.

        Returns:
            dict: Form kwargs including the current request.
        """
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class DatasetListView(FairDMListView):
    """List view for displaying publicly visible datasets.

    Shows all datasets with public visibility in a card layout, with
    filtering and sorting capabilities. Contributors are prefetched
    for optimal performance.
    """

    model = Dataset
    filterset_class = DatasetFilter
    page_title = _("All Datasets")
    page_icon = "dataset"
    list_item_template = "dataset/dataset_card.html"
    order_by = (
        ("-added", _("Newest First")),
        ("added", _("Oldest First")),
        ("-modified", _("Recently Updated")),
        ("name", _("Name A-Z")),
        ("-name", _("Name Z-A")),
    )
    search_fields = ["name", "uuid", "descriptions__value"]

    def get_queryset(self) -> QuerySet[Dataset]:
        """Return the queryset of visible datasets with prefetched contributors.

        Returns:
            QuerySet: Filtered and optimized Dataset queryset.
        """
        qs = super().get_queryset()
        return qs.get_visible().with_contributors()
