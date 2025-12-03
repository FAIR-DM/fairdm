from django.apps import apps
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
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
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        """Add statistics and recent content to the context."""
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        from fairdm.contrib.contributors.models import Organization, Person
        from fairdm.core.models import Dataset, Project
        from fairdm.registry import registry

        context = super().get_context_data(**kwargs)

        # Add home page configuration with site_name substitution
        home_config = getattr(
            settings,
            "HOME_PAGE_CONFIG",
            {
                "logo": True,
                "title": "Welcome to {site_name}",
                "lead": "Discover, explore, and contribute to research data. Our platform enables FAIR data management practices.",
            },
        ).copy()  # Make a copy to avoid mutating the original

        # Get site_name from settings
        site_name = getattr(settings, "SITE_NAME", "")

        # Process title with site_name placeholder if it's a string
        if isinstance(home_config.get("title"), str):
            home_config["title"] = home_config["title"].format(site_name=site_name)

        # Process lead with site_name placeholder if it's a string
        if isinstance(home_config.get("lead"), str):
            home_config["lead"] = home_config["lead"].format(site_name=site_name)

        context["home_config"] = home_config

        User = get_user_model()

        # Calculate statistics
        stats = {
            "projects": Project.objects.get_visible().count(),
            "datasets": Dataset.objects.get_visible().count(),
            "samples": 0,
            "measurements": 0,
            "active_members": User.objects.filter(is_active=True).count(),
            "contributors": Person.objects.count(),
            "organizations": Organization.objects.count(),
        }

        # Count samples and measurements from registered models
        for sample_model in registry.samples:
            try:
                stats["samples"] += sample_model.objects.count()
            except Exception:
                pass

        for measurement_model in registry.measurements:
            try:
                stats["measurements"] += measurement_model.objects.count()
            except Exception:
                pass

        context["stats"] = stats

        # Get recent projects and datasets (limit to 3 for featured section)
        context["recent_projects"] = Project.objects.get_visible().with_contributors().order_by("-added")[:3]
        context["recent_datasets"] = Dataset.objects.get_visible().with_related().order_by("-added")[:3]

        # Prepare sample and measurement data for template to avoid model class method calls
        context["has_samples"] = bool(registry.samples)
        context["has_measurements"] = bool(registry.measurements)

        # Store first sample and measurement URLs if available
        if registry.samples:
            try:
                context["first_sample_url"] = registry.samples[0].get_collection_url()
            except Exception:
                context["first_sample_url"] = None

        if registry.measurements:
            try:
                context["first_measurement_url"] = registry.measurements[0].get_collection_url()
            except Exception:
                context["first_measurement_url"] = None

        # Prepare sample types data (max 5) with counts
        sample_types = []
        for sample_model in registry.samples[:5]:
            try:
                # Build URL manually from model metadata
                slug = sample_model._meta.model_name.lower()
                try:
                    url = reverse(f"{slug}-collection")
                except Exception:
                    url = "#"  # Fallback if URL pattern doesn't exist

                sample_types.append(
                    {
                        "name": sample_model.__name__,
                        "url": url,
                        "count": sample_model.objects.count(),
                    }
                )
            except Exception as e:
                # Log the error but continue
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to add sample type {sample_model.__name__}: {e}")
        context["sample_types"] = sample_types

        # Prepare measurement types data (max 5) with counts
        measurement_types = []
        for measurement_model in registry.measurements[:5]:
            try:
                # Build URL manually from model metadata
                slug = measurement_model._meta.model_name.lower()
                try:
                    url = reverse(f"{slug}-collection")
                except Exception:
                    url = "#"  # Fallback if URL pattern doesn't exist

                measurement_types.append(
                    {
                        "name": measurement_model.__name__,
                        "url": url,
                        "count": measurement_model.objects.count(),
                    }
                )
            except Exception as e:
                # Log the error but continue
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to add measurement type {measurement_model.__name__}: {e}")
        context["measurement_types"] = measurement_types

        return context
