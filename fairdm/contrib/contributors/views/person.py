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
    model = Person
    page_title = _("People")
    page_icon = "people"
    filterset_class = PersonFilter
    queryset = Person.objects.real()
    list_item_template = "contributors/contributor_card.html"
    has_create_permission = False  # Creation is handled by a separate view

    def get_queryset(self):
        # Step 1: Filter active non-superuser persons
        qs = super().get_queryset()

        # Step 2: Prefetch only ORCID identifiers
        orcid_prefetch = Prefetch(
            "identifiers",
            queryset=ContributorIdentifier.objects.filter(type="ORCID"),
            to_attr="orcid_identifiers",
        )

        # Step 3: Prefetch ORCID social accounts
        orcid_accounts_prefetch = Prefetch(
            "socialaccount_set",
            queryset=SocialAccount.objects.filter(provider="orcid"),
            to_attr="orcid_accounts",
        )

        # Step 4: Apply select_related and prefetch_related
        qs = qs.prefetch_related(orcid_prefetch, orcid_accounts_prefetch, "affiliations")

        return qs


class PersonCreateView(LoginRequiredMixin, FairDMCreateView):
    form_class = PersonCreateForm

    def form_valid(self, form):
        response = super().form_valid(form)

        # Users created through this view are not active by default.
        # Being active requires having an account and loggin in.
        self.object.is_active = False
        self.object.save()

        self.messages.info("Succesfully added contributor.")

        return response

    def assign_permissions(self):
        # assigning full permissions is the default for FairDMCreateView (perhaps needs to be reviewed)
        # overriding this method to prevent that
        # Need to think about what permissions they get by default. Perhaps depends on the role?
        pass
