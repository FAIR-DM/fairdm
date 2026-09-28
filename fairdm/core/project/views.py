"""Views for creating and listing projects."""

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
    """List the public projects as cards, with filtering and sorting."""

    model = Project
    filterset_class = ProjectFilter
    list_item_template = "project/project_card.html"
    grid = {"cols": 1, "gap": 4}
    search_fields = ["uuid", "name", "identifiers__value"]
    order_by = [
        ("name", _("Name (A-Z)"), "name"),
        ("-name", _("Name (Z-A)"), "-name"),
        ("added", _("Date created (oldest first)"), "added"),
        ("-added", _("Date created (newest first)"), "-added"),
    ]
    image = static("img/stock/project.jpg")
    show_list_action = True

    def show_create_action(self, user):
        """Offer the create link only to a signed-in user."""
        return user.is_authenticated

    def get_queryset(self) -> QuerySet[Project]:
        """Limit to public projects and load everything a card draws, in a constant number of queries."""
        qs: ProjectQuerySet = super().get_queryset()
        return qs.get_visible().with_list_data().with_contributors()


class ProjectCreateView(LoginRequiredMixin, FairDMCreateView):
    """Create a project, granting the creating user every project permission and crediting them."""

    model = Project
    form_class = ProjectCreateForm
    page_title = _("Create a project")

    def form_valid(self, form: ProjectCreateForm) -> HttpResponse:
        """Record the creator, grant them the project permissions and credit them as Creator, ProjectMember and ContactPerson."""
        # `created_by` is editable=False, so it is set from the request user, never the form.
        form.instance.created_by = self.request.user
        response: HttpResponse = super().form_valid(form)

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

        project.add_contributor(
            user, with_roles=["Creator", "ProjectMember", "ContactPerson"]
        )

        return response

    def get_success_url(self) -> str:
        """Redirect to the new project's own page."""
        return str(self.object.get_absolute_url())
