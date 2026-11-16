"""The full list of a project's or a dataset's recent activity, a page at a time."""

from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.activity.lines import ActivityLines, group_days
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.mixins import PrivateRecordNotFoundMixin
from fairdm.core.dataset.models import Dataset
from fairdm.core.dataset.plugins import dataset_is_visible
from fairdm.core.project.models import Project
from fairdm.core.project.plugins import project_is_visible
from fairdm.views import FairDMTemplateView


class ActivityList(PrivateRecordNotFoundMixin, Plugin, FairDMTemplateView):
    """List every line of a record's recent activity, newest first, 25 to a page.

    Attributes:
        paginate_by: How many lines a page holds.
    """

    url_path = "activity"
    name = "activity"
    template_name = "activity/activity_list.html"
    page_title = _("Recent activity")
    paginate_by = 25

    def get_page_lead(self):
        """Name the record the activity belongs to."""
        return str(self.base_object)

    def get_context_data(self, **kwargs):
        """Add the requested page of lines, grouped into days.

        Raises:
            Http404: When the page asked for does not exist.
        """
        context = super().get_context_data(**kwargs)
        paginator = Paginator(
            ActivityLines(self.base_object, self.request.user), self.paginate_by
        )
        try:
            page = paginator.page(self.request.GET.get("page", 1))
        except InvalidPage as error:
            raise Http404(_("That page of activity does not exist.")) from error
        context["page_obj"] = page
        context["days"] = group_days(page.object_list)
        return context


@plugins.register(Project, menu=False)
class ProjectActivity(ActivityList):
    """The full list of a project's recent activity."""

    check = staticmethod(project_is_visible)


@plugins.register(Dataset, menu=False)
class DatasetActivity(ActivityList):
    """The full list of a dataset's recent activity."""

    check = staticmethod(dataset_is_visible)
