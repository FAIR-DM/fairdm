from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DetailView
from guardian.shortcuts import assign_perm

from fairdm.views import FairDMCreateView, FairDMDeleteView, FairDMListView, FairDMUpdateView

from ..models import Project
from .filters import ProjectFilter
from .forms import ProjectCreateForm, ProjectForm
from .models import PublicDatasetsProtect


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
    has_create_permission = False  # Creation is handled by a separate view

    def get_queryset(self) -> QuerySet[Project]:
        """Return the queryset of visible projects with prefetched contributors.

        Returns:
            QuerySet: Filtered and optimized Project queryset.
        """
        return super().get_queryset().get_visible().with_contributors()


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
        response = super().form_valid(form)

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
        project.add_contributor(user, with_roles=["Creator", "ProjectMember", "ContactPerson"])

        return response

    def get_success_url(self) -> str:
        """Return URL to redirect to after successful creation.

        Returns:
            str: URL to project detail page.
        """
        return reverse("project-detail", kwargs={"uuid": self.object.uuid})


class ProjectUpdateView(LoginRequiredMixin, FairDMUpdateView):
    """View for editing existing Project instances.

    Provides full access to project fields with validation rules to prevent
    invalid state transitions. Requires 'change_project' permission.

    Permissions required:
    - change_project: To edit the project

    Usage:
        URL: /projects/<uuid>/update/
        Login required: Yes
        Object permission: change_project
    """

    model = Project
    form_class = ProjectForm
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_object(self, queryset=None):
        """Get project instance and check permissions.

        Returns:
            Project: The project instance to edit.
        """
        uuid = self.kwargs.get("uuid")
        project = get_object_or_404(Project, uuid=uuid)

        # Check if user has change permission
        if not self.request.user.has_perm("change_project", project):
            raise PermissionDenied("You do not have permission to edit this project.")

        return project

    def get_success_url(self) -> str:
        """Return URL to redirect to after successful update.

        Returns:
            str: URL to project detail page.
        """
        return reverse("project-detail", kwargs={"uuid": self.object.uuid})


class ProjectDeleteView(LoginRequiredMixin, FairDMDeleteView):
    """View for deleting a Project instance with name-confirmation guard.

    Requires:
    - User must be authenticated (LoginRequiredMixin)
    - User must hold the ``delete_project`` object-level permission
    - The ``DeleteConfirmForm`` field ``confirmation`` must match the project name exactly

    Public datasets block deletion; only private datasets are cascade-deleted.

    Usage:
        URL: /projects/<uuid>/delete/
        Login required: Yes
        Object permission: delete_project
    """

    model = Project
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("project-list")
    require_confirmation = True

    def get_object(self, queryset=None):
        """Retrieve project and enforce delete_project permission."""
        uuid = self.kwargs.get("uuid")
        obj = get_object_or_404(Project, uuid=uuid)
        if not self.request.user.has_perm("delete_project", obj):
            raise PermissionDenied("You do not have permission to delete this project.")
        return obj

    def get_confirmation_value(self):
        """Return the project name as the required confirmation value."""
        return self.object.name

    def form_valid(self, form):
        """Delete the project, catching the public-dataset guard if raised."""
        try:
            return super().form_valid(form)
        except PublicDatasetsProtect as e:
            context = self.get_context_data(object=self.object, protected_datasets=e.datasets)
            return self.render_to_response(context)


class ProjectDetailView(DetailView):
    """View for displaying project details.

    Shows comprehensive project information including metadata, contributors,
    datasets, and related content. Public projects are accessible to all users,
    while private projects require appropriate permissions.

    Visibility rules:
    - Public projects: Accessible to all users (including anonymous)
    - Private projects: Requires 'view_project' permission

    Usage:
        URL: /projects/<uuid>/
        Login required: No (for public projects)
        Object permission: view_project (for private projects)
    """

    model = Project
    template_name = "project/project_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    page_title = _("Overview")

    def get_object(self, queryset=None):
        """Get project instance and check visibility/permissions.

        Returns:
            Project: The project instance to display.

        Raises:
            Http404: If project not found.
            PermissionDenied: If user lacks permission to view private project.
        """
        uuid = self.kwargs.get("uuid")
        project = get_object_or_404(Project, uuid=uuid)

        # Public projects are accessible to everyone
        if project.visibility == 1:  # PUBLIC
            return project

        # Private projects require authentication and permission
        if not self.request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to view this project.")

        # Check if user has view permission
        if not self.request.user.has_perm("view_project", project):
            raise PermissionDenied("You do not have permission to view this project.")

        return project

    def get_queryset(self):
        """Return optimized queryset with prefetched metadata.

        Returns:
            QuerySet: Project queryset with related data.
        """
        return Project.objects.with_metadata()

    def get_context_data(self, **kwargs):
        """Add permission information to context.

        Returns:
            dict: Context with can_edit_project permission flag.
        """
        context = super().get_context_data(**kwargs)

        # Check if user has permission to edit
        if self.request.user.is_authenticated:
            context["can_edit_project"] = self.request.user.has_perm("change_project", self.object)
        else:
            context["can_edit_project"] = False

        return context
