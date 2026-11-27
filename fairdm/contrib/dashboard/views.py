"""The pages the dashboard links out to, and the control that hides its getting-started list."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View

from fairdm.contrib.activity.lines import group_days
from fairdm.contrib.dashboard.models import DashboardState
from fairdm.contrib.dashboard.panels import PortalActivity, everyone_datasets, readiness, still_needs
from fairdm.core.dataset.models import Dataset
from fairdm.portal_roles import PortalRoles
from fairdm.utils.choices import Visibility
from fairdm.views.base import FairDMTemplateView


class HideGettingStartedView(LoginRequiredMixin, View):
    """Hide the getting-started list, or bring it back, for the person signed in."""

    def post(self, request):
        state, _created = DashboardState.objects.get_or_create(person=request.user)
        state.getting_started_hidden = request.POST.get("show") != "1"
        state.save(update_fields=["getting_started_hidden"])
        return HttpResponseRedirect(reverse("home"))


class PublicationQueueView(LoginRequiredMixin, UserPassesTestMixin, FairDMTemplateView):
    """Every public dataset not yet published, oldest change first, for the data curators."""

    template_name = "dashboard/publication_queue.html"
    page_title = _("Waiting to be published")
    page_lead = _(
        "Public datasets that have not been published yet, longest waiting first. "
        "Publishing fixes a dataset's record so it can be cited."
    )
    paginate_by = 20

    def test_func(self):
        user = self.request.user
        return user.is_superuser or PortalRoles.is_held_by(user, PortalRoles.DATA_CURATOR)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queue = (
            Dataset.all_objects.filter(visibility=Visibility.PUBLIC, published=False)
            .select_related("project")
            .order_by("modified")
        )
        paginator = Paginator(queue, self.paginate_by)
        try:
            page = paginator.page(self.request.GET.get("page", 1))
        except InvalidPage as error:
            raise Http404(_("That page of the queue does not exist.")) from error
        context["page_obj"] = page
        context["rows"] = [
            {"dataset": d, "ready": (ready := readiness(d)), "still_needs": still_needs(ready["required_missing"])}
            for d in page.object_list
        ]
        return context


class CommunityActivityView(LoginRequiredMixin, FairDMTemplateView):
    """What has happened lately across every dataset anyone may open."""

    template_name = "dashboard/community_activity.html"
    page_title = _("Across the portal")
    page_lead = _("The latest changes to every dataset anyone may open, newest first.")
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(PortalActivity(everyone_datasets(), self.request.user), self.paginate_by)
        try:
            page = paginator.page(self.request.GET.get("page", 1))
        except InvalidPage as error:
            raise Http404(_("That page of activity does not exist.")) from error
        context["page_obj"] = page
        context["days"] = group_days(page.object_list)
        return context
