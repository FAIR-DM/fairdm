"""Generic portal views."""

from django.conf import settings
from django.db.models import Count
from django.db.models.base import Model as Model
from django.templatetags.static import static
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from mvp.views import MVPHomeView

from fairdm.contrib.contributors.models import Organization, Person
from fairdm.contrib.identity.models import Authority, Identity
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.registry import registry


class FairDMHomeView(MVPHomeView):
    """Portal home page, a landing page for visitors and a dashboard for users.

    Each landing page section reads its data from one ``get_*`` method, and every one returns
    only what somebody who has not signed in may see. Subclass the view and override a method
    or a limit to change what a section shows.

    Attributes:
        hero_defaults: The hero's content where ``HOME_PAGE_CONFIG`` leaves a key out.
        latest_limit: How many datasets and how many projects the page shows.
        record_type_limit: How many sample types and how many measurement types are listed.
        people_limit: How many people's faces are shown.
        organization_limit: How many organizations are named.
    """

    page_subtitle = "Welcome"
    page_title = "Getting started"
    dashboard_template_name = "fairdm/dashboard.html"
    landing_template_name = "fairdm/landing.html"

    hero_defaults = {
        "logo": True,
        "eyebrow": gettext_lazy("Research data portal"),
        "title": gettext_lazy("Welcome to {site_name}"),
        "lead": gettext_lazy(
            "Discover, explore and contribute to FAIR research data. "
            "This platform is FAIR by design, not as an afterthought."
        ),
        "image": None,
    }
    latest_limit = 3
    record_type_limit = 5
    people_limit = 8
    organization_limit = 6

    def get_landing_context(self, context):
        """Add what the landing page's sections read."""
        context.update(
            hero=self.get_hero(),
            about=self.get_about(),
            portal_counts=self.get_counts(),
            latest_datasets=self.get_latest_datasets(),
            latest_projects=self.get_latest_projects(),
            sample_types=self.get_record_types(Sample, registry.samples),
            measurement_types=self.get_record_types(Measurement, registry.measurements),
            people=self.get_people(),
            people_count=Person.objects.real().count(),
            organizations=self.get_organizations(),
            allow_registration=settings.ACCOUNT_ALLOW_REGISTRATION,
        )
        return context

    def get_portal_name(self):
        """Return the portal's name.

        Returns:
            The name saved in the portal identity, or ``SITE_NAME`` when none has been saved.
        """
        return Identity.get_solo().safe_translation_getter("name") or settings.SITE_NAME

    def get_hero(self):
        """Return the hero's words and picture from ``HOME_PAGE_CONFIG``, over the defaults.

        Returns:
            A dict with ``eyebrow``, ``title`` and ``lead`` (``{site_name}`` filled in, empty
            where the setting is ``False``), ``image`` (an address, or empty) and ``logo``.
        """
        config = {**self.hero_defaults, **getattr(settings, "HOME_PAGE_CONFIG", {})}
        name = self.get_portal_name()
        content = {
            key: str(config[key]).format(site_name=name) if config[key] else ""
            for key in ("eyebrow", "title", "lead")
        }
        image = config["image"]
        if image and "://" not in image and not image.startswith("/"):
            image = static(image)
        content["image"] = image or ""
        content["logo"] = bool(config["logo"])
        return content

    def get_about(self):
        """Return what the portal says about itself, and who runs it.

        Returns:
            A dict with the portal's ``name``, ``description`` (the saved one, or
            ``PORTAL_DESCRIPTION``), ``keywords``, ``authority`` and ``authority_url``.
        """
        identity = Identity.get_solo()
        authority = Authority.get_solo()
        return {
            "name": self.get_portal_name(),
            "description": identity.safe_translation_getter("description")
            or getattr(settings, "PORTAL_DESCRIPTION", ""),
            "keywords": identity.keywords.all(),
            "authority": authority.safe_translation_getter("name") or "",
            "authority_url": authority.url or "",
        }

    def get_counts(self):
        """Return the headline figures, leaving out anything the portal has none of.

        Returns:
            A list of dicts, each with a ``title``, an ``icon`` name and a ``value``.
        """
        figures = [
            (gettext_lazy("Datasets"), "dataset", Dataset.objects.get_visible()),
            (gettext_lazy("Samples"), "sample", Sample.objects.visible_to(None)),
            (
                gettext_lazy("Measurements"),
                "measurement",
                Measurement.objects.visible_to(None),
            ),
            (gettext_lazy("People"), "member", Person.objects.real()),
            (gettext_lazy("Organizations"), "organization", Organization.objects),
        ]
        counted = [
            {"title": title, "icon": icon, "value": records.count()}
            for title, icon, records in figures
        ]
        return [figure for figure in counted if figure["value"]]

    def get_latest_datasets(self):
        """Return the public datasets changed most recently.

        Returns:
            At most ``latest_limit`` datasets, loaded for their cards.
        """
        return (
            Dataset.objects.get_visible()
            .with_list_data()
            .order_by("-modified")[: self.latest_limit]
        )

    def get_latest_projects(self):
        """Return the public projects added most recently.

        Returns:
            At most ``latest_limit`` projects, loaded for their cards.
        """
        return (
            Project.objects.get_visible()
            .with_list_data()
            .with_contributors()
            .order_by("-added")[: self.latest_limit]
        )

    def get_record_types(self, base, models):
        """Return the registered types of sample or measurement holding the most public records.

        Args:
            base: ``Sample`` or ``Measurement``.
            models: The registered subclasses of ``base``.

        Returns:
            A dict with ``shown``, at most ``record_type_limit`` types each with a ``name``,
            ``description``, ``count`` and ``url``, and ``more``, how many were left out.
        """
        seen = dict(
            base.objects.visible_to(None)
            .non_polymorphic()
            .order_by()
            .values_list("polymorphic_ctype__model")
            .annotate(count=Count("pk"))
        )
        types = []
        for model in models:
            config = registry.get_for_model(model)
            description = config.description
            if config.metadata and config.metadata.description:
                description = config.metadata.description
            try:
                url = reverse(f"{config.get_slug()}-list")
            except NoReverseMatch:
                url = ""
            types.append(
                {
                    "name": config.get_verbose_name_plural(),
                    "description": description,
                    "count": seen.get(model._meta.model_name, 0),
                    "url": url,
                }
            )
        types.sort(key=lambda kind: -kind["count"])
        limit = self.record_type_limit
        return {"shown": types[:limit], "more": max(len(types) - limit, 0)}

    def get_people(self):
        """Return people for the row of faces, those credited on the most records first.

        Returns:
            At most ``people_limit`` people.
        """
        return (
            Person.objects.real()
            .annotate(credits=Count("contributions"))
            .order_by("-credits", "pk")[: self.people_limit]
        )

    def get_organizations(self):
        """Return organizations to name, those credited on the most records first.

        Returns:
            At most ``organization_limit`` organizations.
        """
        return Organization.objects.annotate(credits=Count("contributions")).order_by(
            "-credits", "pk"
        )[: self.organization_limit]

    def get_page_subtitle(self):
        """Greet a signed-in user by first name, falling back to the username."""
        if self.request.user.is_authenticated:
            return f"Welcome, {self.request.user.first_name or self.request.user.username}!"
        return self.page_subtitle

    def get_page_title(self):
        """Title a signed-in user's page as their dashboard."""
        if self.request.user.is_authenticated:
            return _("My Dashboard")
        return self.page_title
