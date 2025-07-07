from actstream import actions
from actstream.models import Follow
from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.generic.base import RedirectView
from django_contact_form.views import ContactFormView
from literature.models import LiteratureItem

from fairdm.contrib import CORE_MAPPING
from fairdm.views import FairDMListView, FairDMTemplateView

from .filters import LiteratureFilterset


class ReferenceListView(FairDMListView):
    title = _("References")
    model = LiteratureItem
    paginate_by = 20
    filterset_class = LiteratureFilterset
    heading_config = {
        "icon": "literature",
        "title": _("References"),
        "description": _(
            "This section lists all references that have been added to this portal. "
            "You can search and filter references by type, author, title, and other metadata. "
            "Each reference may include a DOI, publication date, and other relevant information to help you find and cite the literature effectively."
        ),
    }
    grid_config = {
        "card": "literature.card",
    }


def follow_unfollow(request, uuid):
    model_class = apps.get_model(CORE_MAPPING[uuid[0]])
    instance = get_object_or_404(model_class, uuid=uuid)
    is_following = Follow.objects.is_following(request.user, instance)

    if is_following:
        actions.unfollow(request.user, instance)
    else:
        actions.follow(request.user, instance)
    return HttpResponse(status=200)


class GenericContactForm(LoginRequiredMixin, ContactFormView):
    """A view class that will send an email to all contributors with the ContactPerson role."""

    def get_object(self, queryset=None):
        model_class = apps.get_model(CORE_MAPPING[self.kwargs["object_type"]])
        return model_class.objects.get(uuid=self.kwargs["uuid"])

    @property
    def recipient_list(self):
        self.object = self.get_object()

        contacts = self.object.contributors.filter(roles__contains=["ContactPerson"])

        # get the email addresses of the contributors
        emails = []
        for c in contacts:
            if c.profile.user:
                emails.append(c.profile.user.email)
        return emails


class DirectoryView(RedirectView):
    """
    Redirects shortened URLs to full, descriptive URLs for various object types.

    E.g. /p1234567890abcdef/ -> /project/p1234567890abcdef/
    or /s1234567890abcdef/ -> /sample/s1234567890abcdef/
    """

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        uuid = self.kwargs["uuid"]
        model = apps.get_model(CORE_MAPPING[uuid[0]])
        obj = get_object_or_404(model, uuid=uuid)
        return obj.get_absolute_url()


class HomeView(FairDMTemplateView):
    title = _("Home")
    template_name = "fairdm/pages/home.html"
    slider_breakpoints = {
        0: {"slidesPerView": 1, "spaceBetween": 10},
        768: {"slidesPerView": 3, "spaceBetween": 10},
    }
