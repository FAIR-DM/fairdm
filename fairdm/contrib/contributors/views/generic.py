from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.templatetags.static import static
from django.utils.translation import gettext as _
from django.views.generic.detail import SingleObjectMixin
from django_contact_form.views import ContactFormView

from fairdm.utils.utils import user_guide
from fairdm.views import FairDMListView

from ..filters import ContributorFilter
from ..models import Contributor, Person


class ContributorContactView(LoginRequiredMixin, SingleObjectMixin, ContactFormView):
    """Contact form for a contributor."""

    model = Contributor

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    @property
    def recipient_list(self):
        email = [self.get_object().preferred_email]
        return email


class ContributorListView(FairDMListView):
    """List view for contributions."""

    model = Contributor
    title = _("Contributors")
    learn_more = user_guide("project")
    image = static("img/stock/contributors.jpg")
    filterset_class = ContributorFilter

    paginate_by = 20

    def get_queryset(self):
        return self.model.objects.instance_of(Person).prefetch_related("affiliations", "identifiers")
