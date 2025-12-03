from typing import Any

from django.db.models import QuerySet
from django.http import HttpResponse
from django.templatetags.static import static
from django.utils.translation import gettext as _

from fairdm import plugins
from fairdm.utils.utils import user_guide
from fairdm.views import FairDMCreateView, FairDMListView

from .filters import DatasetFilter
from .forms import DatasetForm
from .models import Dataset

# Get or create the PluggableView for Dataset model
DatasetDetailView = plugins.registry.get_or_create_view_for_model(Dataset)


class DatasetCreateView(FairDMCreateView):
    """View for creating new Dataset instances.

    Handles dataset creation with automatic contributor assignment. The user
    who creates the dataset is automatically added as a Creator, ProjectMember,
    and ContactPerson. Supports pre-populating the project field from query params.
    """

    model = Dataset
    form_class = DatasetForm
    title = _("Create a Dataset")
    heading_config = {
        "title": _("Create a dataset"),
        "description": _(
            "Datasets are the foundation of FAIR research data, and the metadata they contain are key to making data Findable, Accessible, Interoperable, and Reusable. Use the form below to quickly create a new dataset. After creation, you can upload data, add contributors, enrich your descriptions, and include advanced metadata to support discovery and reuse."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("datasets"),
                "icon": "documentation",
            }
        ],
    }
    fields = ["name", "license", "project"]

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

    def form_valid(self, form: DatasetForm) -> HttpResponse:
        """Handle successful form submission and add the creator as a contributor.

        Args:
            form: The validated DatasetForm instance.

        Returns:
            HttpResponse: The response from the parent class.
        """
        response = super().form_valid(form)
        self.object.add_contributor(self.request.user, with_roles=["Creator", "ProjectMember", "ContactPerson"])
        return response


class DatasetListView(FairDMListView):
    """List view for displaying publicly visible datasets.

    Shows all datasets with public visibility in a card layout, with
    filtering and sorting capabilities. Contributors are prefetched
    for optimal performance.
    """

    model = Dataset
    filterset_class = DatasetFilter
    title = _("Datasets")
    image = static("img/stock/dataset.jpg")
    heading_config = {
        "icon": "dataset",
        "title": _("Datasets"),
        "description": _(
            "A dataset is a structured collection of data generated or compiled during the course of a research activity. "
            "This page lists all publicly available datasets within the portal that adhere to the metadata and quality "
            "standards set by this community. Use the search and filter options to find datasets relevant to your research needs."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("datasets"),
                "icon": "documentation",
            }
        ],
    }

    description = _(
        "Search and filter thousands of open-access research datasets by topic, field, or format. Access high-quality "
        "data to support your research projects."
    )
    card_template = "dataset/dataset_card.html"

    def get_queryset(self) -> QuerySet[Dataset]:
        """Return the queryset of visible datasets with prefetched contributors.

        Returns:
            QuerySet: Filtered and optimized Dataset queryset.
        """
        return Dataset.objects.get_visible().with_contributors()
