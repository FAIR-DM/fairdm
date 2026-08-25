from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.utils.translation import gettext as _
from guardian.shortcuts import assign_perm

from fairdm.views import FairDMCreateView, FairDMListView

from .filters import DatasetFilter
from .models import Dataset, DatasetQuerySet


class DatasetCreateView(LoginRequiredMixin, FairDMCreateView):
    """View for creating new Dataset instances.

    Handles dataset creation with automatic contributor assignment. The user
    who creates the dataset is automatically added as a Creator, ProjectMember,
    and ContactPerson.
    """

    model = Dataset
    # form_class = DatasetCreateForm
    fields = ["name", "project", "license"]
    page_title = _("Create a Dataset")
    default_roles = ["Creator", "ProjectMember", "ContactPerson"]

    def get_form_kwargs(self):
        """Add request to form kwargs for user-specific filtering.

        Returns:
            dict: Form kwargs including the current request.
        """
        kwargs = super().get_form_kwargs()
        # kwargs["request"] = self.request
        return kwargs

    def get_success_url(self) -> str:
        """Return URL to redirect to after successful creation.

        ``Dataset.get_absolute_url()`` rather than a name reversed here: the dataset's own page
        is a registration, not a standalone route, since 014 T057.

        Returns:
            str: URL to the dataset's own page.
        """
        return str(self.object.get_absolute_url())

    def form_valid(self, form) -> HttpResponse:
        """Handle successful form submission and assign permissions.

        Automatically assigns full dataset permissions to the creating user and
        adds them as a contributor with Creator, ProjectMember, and ContactPerson roles.

        Args:
            form: The validated DatasetCreateForm instance.

        Returns:
            HttpResponse: Redirect to dataset detail page.
        """
        response: HttpResponse = super().form_valid(form)

        user = self.request.user
        dataset = self.object

        # A dataset is private unless stated otherwise, so without these the
        # creator cannot open, edit or delete the record they just made. The
        # set and the order match `ProjectCreateView.form_valid`.
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
    order_by = [
        ("-added", _("Date created (newest first)"), "-added"),
        ("added", _("Date created (oldest first)"), "added"),
        ("-modified", _("Recently Updated"), "-modified"),
        ("name", _("Name A-Z"), "name"),
        ("-name", _("Name Z-A"), "-name"),
    ]
    search_fields = ["name", "uuid", "descriptions__value"]

    def get_queryset(self) -> QuerySet[Dataset]:
        """Return the queryset of visible datasets with prefetched contributors.

        `Dataset.objects` (the base this view's `super().get_queryset()`
        reads through) is privacy-first by default, so no separate
        visibility filter is needed here any more (R1).

        Returns:
            QuerySet: Filtered and optimized Dataset queryset.
        """
        qs: DatasetQuerySet = super().get_queryset()
        return qs.with_contributors()
