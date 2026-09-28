"""Views for creating and listing datasets."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.utils.translation import gettext as _
from guardian.shortcuts import assign_perm

from fairdm.views import FairDMCreateView, FairDMListView

from .filters import DatasetFilter
from .forms import DatasetCreateForm
from .models import Dataset, DatasetQuerySet


class DatasetCreateView(LoginRequiredMixin, FairDMCreateView):
    """Create a dataset, crediting the creating user as Creator, ProjectMember and ContactPerson."""

    model = Dataset
    form_class = DatasetCreateForm
    page_title = _("Create a Dataset")
    default_roles = ["Creator", "ProjectMember", "ContactPerson"]

    def get_form_kwargs(self):
        """Pass the request to the form for user-specific filtering."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self) -> str:
        """Redirect to the new dataset's own page."""
        return str(self.object.get_absolute_url())

    def form_valid(self, form) -> HttpResponse:
        """Record the creator, grant them the dataset permissions and credit them."""
        # `created_by` is editable=False, so it is set from the request user, never the form.
        form.instance.created_by = self.request.user
        response: HttpResponse = super().form_valid(form)

        user = self.request.user
        dataset = self.object

        # A dataset is private by default, so the creator needs these to open, edit or delete it.
        permissions = [
            "view_dataset",
            "change_dataset",
            "delete_dataset",
            "change_dataset_metadata",
            "change_dataset_settings",
        ]

        for perm in permissions:
            assign_perm(perm, user, dataset)

        dataset.add_contributor(
            user, with_roles=["Creator", "ProjectMember", "ContactPerson"]
        )

        return response


class DatasetListView(FairDMListView):
    """List the visible datasets as cards, with filtering and sorting."""

    model = Dataset
    filterset_class = DatasetFilter
    page_title = _("Datasets")
    page_icon = "dataset"
    list_item_template = "dataset/dataset_card.html"
    grid = {"cols": 1, "gap": 4}
    order_by = [
        ("-added", _("Date created (newest first)"), "-added"),
        ("added", _("Date created (oldest first)"), "added"),
        ("-modified", _("Recently Updated"), "-modified"),
        ("name", _("Name A-Z"), "name"),
        ("-name", _("Name Z-A"), "-name"),
    ]
    search_fields = [
        "name",
        "uuid",
        "identifiers__value",
        "descriptions__value",
        "keywords__name",
    ]

    def get_queryset(self) -> QuerySet[Dataset]:
        """Load everything a card draws, so the query count does not grow with the page."""
        qs: DatasetQuerySet = super().get_queryset()
        return qs.with_list_data()
