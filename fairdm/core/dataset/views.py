from typing import Any

from django.templatetags.static import static
from django.utils.translation import gettext as _

from fairdm.core.filters import DatasetFilter
from fairdm.utils.utils import user_guide
from fairdm.views import FairDMCreateView, FairDMListView

from .forms import DatasetForm
from .models import Dataset


class DatasetCreateView(FairDMCreateView):
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
                "icon": "fa-solid fa-book",
            }
        ],
    }
    fields = ["image", "project", "name", "license"]

    def get_initial(self) -> dict[str, Any]:
        if self.request.GET.get("project"):
            project_id = self.request.GET["project"]
            if project_id.isdigit():
                return {"project": int(project_id)}
        return super().get_initial()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.add_contributor(self.request.user, with_roles=["Creator", "ProjectMember", "ContactPerson"])
        return response


class DatasetListView(FairDMListView):
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
                "icon": "fa-solid fa-book",
            }
        ],
    }
    grid_config = {
        "card": "dataset.card",
    }
    description = _(
        "Search and filter thousands of open-access research datasets by topic, field, or format. Access high-quality "
        "data to support your research projects."
    )

    def get_queryset(self):
        return Dataset.objects.get_visible().with_contributors()
