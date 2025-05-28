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
    help_text = _(
        "Create a new research project to share with the community. Projects are a great way to group multiple datasets and organize your research."
    )

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.add_contributor(self.request.user, with_roles=["Creator", "ProjectMember", "ContactPerson"])
        return response


class ProjectListView(FairDMListView):
    model = Project
    filterset_class = ProjectFilter
    title = _("Projects")
    description = _(
        "Discover past, present and future research projects shared by our community to see what other are working on."
    )
    about = [
        _(
            "A research project serves as a container for multiple datasets that share common metadata, such as funding sources, project descriptions, contributors, and institutional affiliations. This page presents publicly listed research projects contributed by community members, allowing you to explore what others are working on."
        ),
        _(
            "Search and filter projects by topic, field, or format. Each project may contain multiple datasets, which can be accessed individually."
        ),
    ]
    learn_more = user_guide("project")
    image = static("img/stock/project.jpg")
    card = "project.card"  # cotton/project/card.html

    def get_queryset(self):
        return Project.objects.with_contributors()
