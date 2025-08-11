from django.templatetags.static import static
from django.utils.translation import gettext as _

from fairdm.core.filters import ProjectFilter
from fairdm.utils.utils import user_guide
from fairdm.views import FairDMCreateView, FairDMListView

from ..models import Project
from .forms import ProjectForm


class ProjectCreateView(FairDMCreateView):
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
                "icon": "fa-solid fa-book",
            }
        ],
    }

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.add_contributor(self.request.user, with_roles=["Creator", "ProjectMember", "ContactPerson"])
        return response


class ProjectListView(FairDMListView):
    model = Project
    filterset_class = ProjectFilter
    title = _("Research Projects")
    description = _(
        "Discover past, present and future research projects shared by our community to see what other are working on."
    )
    heading_config = {
        "icon": "project",
        "title": _("Research Projects"),
        "description": _(
            "A research project serves as a container for multiple datasets that share common metadata, such as funding sources, project descriptions, contributors, and institutional affiliations. This page presents publicly listed research projects contributed by community members, allowing you to explore what others community members are currently working on."
        ),
        "links": [
            {
                "text": _("Learn More"),
                "href": user_guide("project"),
                "icon": "fa-solid fa-book",
            },
        ],
    }

    image = static("img/stock/project.jpg")
    # card = "project.card"  # cotton/project/card.html

    def get_queryset(self):
        return Project.objects.get_visible().with_contributors()
