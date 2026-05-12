from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DetailView
from guardian.shortcuts import assign_perm

from fairdm.views import FairDMCreateView, FairDMDeleteView, FairDMListView, FairDMUpdateView

from .filters import DatasetFilter
from .forms import DatasetCreateForm, DatasetForm
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
    and ContactPerson.
    """

    model = Dataset
    form_class = DatasetCreateForm
    page_title = _("Create a Dataset")
    default_roles = ["Creator", "ProjectMember", "ContactPerson"]

    def get_form_kwargs(self):
        """Add request to form kwargs for user-specific filtering.

        Returns:
            dict: Form kwargs including the current request.
        """
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self) -> str:
        """Return URL to redirect to after successful creation.

        Returns:
            str: URL to dataset detail page.
        """
        return reverse("dataset-detail", kwargs={"uuid": self.object.uuid})

    def form_valid(self, form) -> HttpResponse:
        """Handle successful form submission and assign permissions.

        Automatically assigns full dataset permissions to the creating user and
        adds them as a contributor with Creator, ProjectMember, and ContactPerson roles.

        Args:
            form: The validated DatasetCreateForm instance.

        Returns:
            HttpResponse: Redirect to dataset detail page.
        """
        response = super().form_valid(form)

        user = self.request.user
        dataset = self.object

        permissions = [
            "view_dataset",
            "change_dataset",
            "delete_dataset",
            "change_dataset_metadata",
            "change_dataset_settings",
        ]

        for perm in permissions:
            assign_perm(perm, user, dataset)

        dataset.add_contributor(user, with_roles=["Creator", "ProjectMember", "ContactPerson"])

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

        Returns:
            QuerySet: Filtered and optimized Dataset queryset.
        """
        qs = super().get_queryset()
        return qs.get_visible().with_contributors()


class DatasetUpdateView(LoginRequiredMixin, FairDMUpdateView):
    """View for editing existing Dataset instances.

    Enforces ``change_dataset`` object-level permission. Passes ``request``
    to ``DatasetForm`` so the project dropdown is filtered to the user's
    accessible projects. Redirects to the dataset detail page on success.

    Permissions required:
        change_dataset: To edit the dataset

    Usage:
        URL: /datasets/<uuid>/update/
        Login required: Yes
        Object permission: change_dataset
    """

    model = Dataset
    form_class = DatasetForm
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_object(self, queryset=None):
        """Retrieve dataset and enforce change_dataset permission."""
        uuid = self.kwargs.get("uuid")
        dataset = get_object_or_404(Dataset, uuid=uuid)
        if not self.request.user.has_perm("change_dataset", dataset):
            raise PermissionDenied("You do not have permission to edit this dataset.")
        return dataset

    def get_form_kwargs(self):
        """Add request to form kwargs for user-specific project filtering.

        Returns:
            dict: Form kwargs including the current request.
        """
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self) -> str:
        """Return URL to redirect to after successful update.

        Returns:
            str: URL to dataset detail page.
        """
        return reverse("dataset-detail", kwargs={"uuid": self.object.uuid})


class DatasetDeleteView(LoginRequiredMixin, FairDMDeleteView):
    """View for deleting a Dataset instance with name-confirmation guard.

    Requires:
        - User must be authenticated (LoginRequiredMixin)
        - User must hold the ``delete_dataset`` object-level permission
        - The ``DeleteConfirmForm`` field ``confirmation`` must match the dataset name exactly

    Usage:
        URL: /datasets/<uuid>/delete/
        Login required: Yes
        Object permission: delete_dataset
    """

    model = Dataset
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("dataset-list")
    require_confirmation = True

    def get_object(self, queryset=None):
        """Retrieve dataset and enforce delete_dataset permission."""
        uuid = self.kwargs.get("uuid")
        dataset = get_object_or_404(Dataset, uuid=uuid)
        if not self.request.user.has_perm("delete_dataset", dataset):
            raise PermissionDenied("You do not have permission to delete this dataset.")
        return dataset

    def get_confirmation_value(self):
        """Return the dataset name as the required confirmation value."""
        return self.object.name
