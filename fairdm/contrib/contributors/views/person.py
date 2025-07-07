from actstream.models import Follow
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Prefetch
from django.db.models.base import Model as Model
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from formset.views import EditCollectionView
from meta.views import MetadataMixin

from fairdm.views import FairDMCreateView, FairDMListView, FairDMTemplateView

from ..choices import DefaultGroups
from ..filters import PersonFilter
from ..forms.contribution import PersonCreateForm
from ..models import ContributorIdentifier, Person


class PortalTeamView(FairDMTemplateView):
    title = _("Portal Team")
    template_name = "fairdm/pages/portal_team.html"
    heading_config = {
        "icon": "team",
        "title": _("Portal Team"),
        "description": _(
            "The portal team is responsible for maintaining and developing this research portal. "
            "This team ensures that the portal is user-friendly, up-to-date, and provides access to the latest data and resources. "
            "The team consists of portal administrators, data administrators, and developers who work together to enhance the portal's functionality and user experience."
        ),
    }
    groups = {
        DefaultGroups.PORTAL_ADMIN: _("Portal Administrators"),
        DefaultGroups.DATA_ADMIN: _("Data Administrators"),
        DefaultGroups.DEVELOPERS: _("Developers"),
    }
    slider_breakpoints = {
        0: {"slidesPerView": 1, "spaceBetween": 10},
        768: {"slidesPerView": 4, "spaceBetween": 10},
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        group_qs = (
            Group.objects.filter(name__in=self.groups.keys())
            .annotate(user_count=Count("user"))
            .filter(user_count__gt=0)
            .prefetch_related("user_set")
        )

        # Map by internal name (untranslated)
        group_dict = {group.name: group for group in group_qs}

        # Ordered list of (translated name, group)
        ordered_groups = [
            {"label": self.groups[name], "group": group_dict[name]} for name in self.groups if name in group_dict
        ]
        context["groups"] = ordered_groups
        return context


class ContributorBaseListView(FairDMListView):
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
        return super().get_queryset().filter(is_superuser=False)


class ContributorListView(ContributorBaseListView):
    model = Person
    title = _("All Contributors")
    filterset_class = PersonFilter
    queryset = Person.contributors.all()
    heading_config = {
        "icon": "contributors",
        "title": _("Personal Contributors"),
        "description": _(
            "Contributors are individuals who have made contributions to data made public within this portal. "
            "They may include researchers, developers, data curators, and other professionals who have played a key role in producing datasets."
        ),
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
                    content_type=self.person_ct,
                    user=user,
                    object_id__in=[str(pk) for pk in queryset.values_list("pk", flat=True)],
                ).values_list("object_id", flat=True)
            )

            for person in queryset:
                person.is_followed = person.pk in followed_ids
        else:
            for person in queryset:
                person.is_followed = False

        return context


class ActiveMemberListView(ContributorListView):
    title = _("Active Members")
    queryset = Person.contributors.filter(is_active=True)
    heading_config = {
        "icon": "contributors",
        "title": _("Active Members"),
        "description": _(
            "Active members are contributors who have created a personal account within the portal. "
            "They are engaged with the community and may be involved in ongoing projects or discussions."
        ),
    }


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
