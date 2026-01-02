from django.db.models import QuerySet
from django.http import HttpResponse
from django.templatetags.static import static
from django.utils.translation import gettext as _

from fairdm import plugins
from fairdm.utils.utils import user_guide
from fairdm.views import FairDMCreateView, FairDMListView

from ..models import Project
from .filters import ProjectFilter
from .forms import ProjectForm

# Get or create the PluggableView for Project model
# This replaces the need for an explicit ProjectDetailPage class
ProjectDetailPage = plugins.registry.get_or_create_view_for_model(Project)


class ProjectCreateView(FairDMCreateView):
    """View for creating new Project instances.

    Handles project creation with automatic contributor assignment. The user
    who creates the project is automatically added as a Creator, ProjectMember,
    and ContactPerson.
    """

    model = Project
    form_class = ProjectForm
    title = _("Create a Project")
    fields = ["name", "visibility", "status"]

    heading_config = {
        "title": _("Create a project"),
        "description": _(
            "A project is a way to group related datasets that share common metadata such as contributors, funding sources, and research goals. Projects help organize your work, provide essential context, and make your research easier for others to find and understand."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("project"),
                "icon": "documentation",
            }
        ],
    }

    def form_valid(self, form: ProjectForm) -> HttpResponse:
        """Handle successful form submission and add the creator as a contributor.

        Args:
            form: The validated ProjectForm instance.

        Returns:
            HttpResponse: The response from the parent class.
        """
        response = super().form_valid(form)
        self.object.add_contributor(self.request.user, with_roles=["Creator", "ProjectMember", "ContactPerson"])
        return response


class ProjectListView(FairDMListView):
    """List view for displaying publicly visible projects.

    Shows all projects with public visibility in a card layout, with
    filtering and sorting capabilities. Contributors are prefetched
    for optimal performance.
    """

    model = Project
    filterset_class = ProjectFilter
    title = _("Research Projects")
    description = _(
        "Discover past, present and future research projects shared by our community to see what other are working on."
    )
    page = {
        "title": _("Research Projects"),
        "description": _(
            "A research project serves as a container for multiple datasets that share common metadata, such as funding sources, project descriptions, contributors, and institutional affiliations. This page presents publicly listed research projects contributed by community members, allowing you to explore what others community members are currently working on."
        ),
    }

    image = static("img/stock/project.jpg")
    card_template = "project/project_card.html"

    def get_queryset(self) -> QuerySet[Project]:
        """Return the queryset of visible projects with prefetched contributors.

        Returns:
            QuerySet: Filtered and optimized Project queryset.
        """
        return Project.objects.get_visible().with_contributors()
