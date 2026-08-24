from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.templatetags.static import static
from django.utils.translation import gettext as _
from guardian.shortcuts import assign_perm

from fairdm.views import FairDMCreateView, FairDMListView

from ..models import Project
from .filters import ProjectFilter
from .forms import ProjectCreateForm
from .models import ProjectQuerySet


class ProjectListView(FairDMListView):
    """List view for displaying publicly visible projects.

    Shows all projects with public visibility in a card layout, with
    filtering and sorting capabilities. Contributors are prefetched
    for optimal performance.
    """

    model = Project
    filterset_class = ProjectFilter
    list_item_template = "project/project_card.html"
    search_fields = ["uuid", "name"]
    order_by = [
        ("name", _("Name (A-Z)"), "name"),
        ("-name", _("Name (Z-A)"), "-name"),
        ("added", _("Date created (oldest first)"), "added"),
        ("-added", _("Date created (newest first)"), "-added"),
    ]
    image = static("img/stock/project.jpg")
    show_create_action = False  # Creation is handled by a separate view
    show_list_action = True  # All users can view the list of public projects

    def get_queryset(self) -> QuerySet[Project]:
        """Return the queryset of visible projects with prefetched contributors.

        Returns:
            QuerySet: Filtered and optimized Project queryset.
        """
        qs: ProjectQuerySet = super().get_queryset()
        return qs.get_visible().with_contributors()


class ProjectCreateView(LoginRequiredMixin, FairDMCreateView):
    """View for creating new Project instances.

    Provides a streamlined project creation form with minimal required fields.
    Users can add detailed metadata through the edit interface after creation.

    Automatically assigns full permissions to the creating user including:
    - view_project
    - change_project
    - delete_project
    - change_project_metadata
    - change_project_settings

    Usage:
        URL: /projects/create/
        Login required: Yes
        Permissions: Authenticated users can create projects
    """

    model = Project
    form_class = ProjectCreateForm
    page_title = _("Create a project")

    def form_valid(self, form: ProjectCreateForm) -> HttpResponse:
        """Handle successful form submission and assign permissions.

        Automatically assigns full project permissions to the creating user and
        adds them as a contributor with Creator, ProjectMember, and ContactPerson roles.

        Args:
            form: The validated ProjectCreateForm instance.

        Returns:
            HttpResponse: Redirect to project detail page.
        """
        # Set the creator before saving so `created_by` is written with the
        # rest of the record in one save, from the request user only.
        form.instance.created_by = self.request.user
        response: HttpResponse = super().form_valid(form)

        # Assign full permissions to creator
        user = self.request.user
        project = self.object

        permissions = [
            "view_project",
            "change_project",
            "delete_project",
            "change_project_metadata",
            "change_project_settings",
        ]

        for perm in permissions:
            assign_perm(perm, user, project)

        # Add creator as contributor
        project.add_contributor(
            user, with_roles=["Creator", "ProjectMember", "ContactPerson"]
        )

        return response

    def get_success_url(self) -> str:
        """Return URL to redirect to after successful creation.

        Returns:
            str: URL to the project's own page.
        """
        return str(self.object.get_absolute_url())
