from actstream.models import Follow
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch
from django.db.models.base import Model as Model
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from formset.views import EditCollectionView
from meta.views import MetadataMixin

from fairdm.views import FairDMListView

from ..filters import ContributorFilter
from ..models import ContributorIdentifier, Person


class ContributorListView(FairDMListView):
    model = Person
    title = _("All Contributors")
    filterset_class = ContributorFilter
    sidebar_primary_config = {
        "title": _("Find someone"),
    }
    grid_config = {
        "cols": 1,
        "gap": 2,
        "responsive": {"md": 2},
        "card": "contributor.card.person",
    }

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
            "socialaccount_set", queryset=SocialAccount.objects.filter(provider="orcid"), to_attr="orcid_accounts"
        )

        # Step 4: Get the content type for follow lookups (cached)
        self.person_ct = ContentType.objects.get_for_model(Person)

        # Step 5: Apply select_related and prefetch_related
        qs = qs.prefetch_related(orcid_prefetch, orcid_accounts_prefetch, "affiliations")

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = context["object_list"]
        user = self.request.user

        # Step 6: Batch follow lookup
        if user.is_authenticated:
            followed_ids = set(
                Follow.objects.filter(
                    content_type=self.person_ct, user=user, object_id__in=queryset.values_list("pk", flat=True)
                ).values_list("object_id", flat=True)
            )

            for person in queryset:
                person.is_followed = person.pk in followed_ids
        else:
            for person in queryset:
                person.is_followed = False

        return context


class PortalTeamView(ContributorListView):
    title = _("Portal Team")
    queryset = Person.objects.filter(is_staff=True, is_superuser=False)
    sections = {"sidebar_primary": False}


class ActiveMemberListView(ContributorListView):
    title = _("Active Members")
    queryset = Person.objects.filter(is_active=True, is_superuser=False)


class AccountEdit(MetadataMixin, LoginRequiredMixin, EditCollectionView):
    template_name = "user/settings/base.html"

    def get_object(self):
        return self.request.user


class CodeOfConduct(MetadataMixin, LoginRequiredMixin, TemplateView):
    template_name = "user/agreements/code_of_conduct.html"
    title = _("Code of Conduct")

    def get_object(self):
        return self.request.user


class TermsOfUse(MetadataMixin, LoginRequiredMixin, TemplateView):
    template_name = "fairdm/pages/code_of_conduct.html"
    title = _("Terms of Use")

    def get_object(self):
        return self.request.user
