from django.templatetags.static import static
from django.utils.translation import gettext as _

from fairdm.utils.utils import user_guide
from fairdm.views import FairDMCreateView, FairDMListView

from .forms import DatasetForm
from .models import Dataset


class DatasetCreateView(FairDMCreateView):
    model = Dataset
    form_class = DatasetForm
    title = _("Create a Dataset")
    help_text = _(
        "Create a new dataset to share with the community. Upload existing data or get started designing your next dataset from scratch."
    )
    learn_more = user_guide("datasets")
    fields = ["image", "project", "name", "license"]

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.add_contributor(self.request.user, with_roles=["Creator", "ProjectMember", "ContactPerson"])
        return response


class DatasetListView(FairDMListView):
    model = Dataset
    title = _("Datasets")
    image = static("img/stock/dataset.jpg")
    description = _(
        "Search and filter thousands of open-access research datasets by topic, field, or format. Access high-quality data to support your research projects."
    )
    about = _(
        "A dataset is a structured collection of data generated or compiled during the course of a research activity. This page lists all publicly available datasets within the portal that adhere to the metadata and quality standards set by this community. Use the search and filter options to find datasets relevant to your research needs."
    )
    learn_more = user_guide("datasets")
    card = "dataset.card"  # cotton/dataset/card.html

    def get_queryset(self):
        return Dataset.objects.with_contributors()
