"""Views for listing and adding people."""

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.db.models.base import Model as Model
from django.utils.translation import gettext as _

from fairdm.views import FairDMCreateView, FairDMListView

from ..filters import PersonFilter
from ..forms.contribution import PersonCreateForm
from ..models import ContributorIdentifier, Person


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
        """Prefetch each person's ORCID identifiers, ORCID accounts and affiliations."""
        qs = super().get_queryset()

        orcid_prefetch = Prefetch(
            "identifiers",
            queryset=ContributorIdentifier.objects.filter(type="ORCID"),
            to_attr="orcid_identifiers",
        )

        orcid_accounts_prefetch = Prefetch(
            "socialaccount_set",
            queryset=SocialAccount.objects.filter(provider="orcid"),
            to_attr="orcid_accounts",
        )

        qs = qs.prefetch_related(
            orcid_prefetch, orcid_accounts_prefetch, "affiliations"
        )

        return qs


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
