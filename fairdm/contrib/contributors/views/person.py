"""Views for listing and adding people."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.utils.translation import gettext as _

from fairdm.views import FairDMCreateView, FairDMListView

from ..filters import PersonFilter
from ..forms.contribution import PersonCreateForm
from ..models import Person


class PersonListView(FairDMListView):
    """List people, excluding superusers."""

    model = Person
    page_title = _("People")
    page_icon = "people"
    filterset_class = PersonFilter
    queryset = Person.objects.real()
    list_item_template = "contributors/contributor_card.html"
    grid = {"md": 2, "xl": 3}
    show_create_action = False

    def get_queryset(self):
        """Prefetch what each person's card reads."""
        return super().get_queryset().for_cards()


class PersonCreateView(LoginRequiredMixin, FairDMCreateView):
    """Add a person who has no account yet."""

    form_class = PersonCreateForm

    def form_valid(self, form):
        """Save the person as inactive, since being active needs an account."""
        response = super().form_valid(form)

        self.object.is_active = False
        self.object.save()

        self.messages.info("Succesfully added contributor.")

        return response

    def assign_permissions(self):
        """Skip the creator's default full permissions."""
        pass
