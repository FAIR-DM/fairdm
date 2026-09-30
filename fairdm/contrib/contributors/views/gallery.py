"""Development gallery of the contributor display components.

Served only with DEBUG on, against the records ``manage.py seed_contributors`` creates.
"""

from django.views.generic import TemplateView

from fairdm.core.project.models import Project

from ..models import Organization, Person

SEED = "contributor-components"


class ContributorGalleryView(TemplateView):
    """Every ``c-contributor.*`` component in every state the seed data reaches."""

    template_name = "contributors/gallery.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        people = list(Person.objects.filter(config__seed=SEED).prefetch_related("groups").order_by("pk"))
        organizations = {o.name: o for o in Organization.objects.filter(config__seed=SEED)}
        projects = {
            p.name.removeprefix("[Contributors] "): p
            for p in Project.objects.filter(name__startswith="[Contributors] ")
        }

        def credits(name):
            project = projects.get(name)
            if project is None:
                return []
            return list(project.contributors.select_related("contributor").prefetch_related("roles"))

        by_name = {p.name: p for p in people}
        context.update(
            page={"title": "Contributor components"},
            seeded=bool(people),
            people=people,
            organizations=list(organizations.values()),
            many=credits("Many contributors"),
            few=credits("Three contributors"),
            one=credits("One contributor"),
            none=credits("Nobody credited"),
            many_url=projects["Many contributors"].get_absolute_url() if "Many contributors" in projects else "",
            avatar_states=[
                ("Person, photo", by_name.get("Ana Sofía Martínez-Ortega")),
                ("Person, no photo", by_name.get("Ben Wu")),
                ("Person, name in another script", by_name.get("李辰")),
                ("Organization, wide logo", organizations.get("GFZ Helmholtz Centre for Geosciences")),
                ("Organization, square logo", organizations.get("University of Potsdam")),
                ("Organization, no logo", organizations.get("Deutsche Forschungsgemeinschaft")),
            ],
            spotlight={
                "authenticated": by_name.get("Ana Sofía Martínez-Ortega"),
                "unauthenticated": by_name.get("Ben Wu"),
                "no_orcid": by_name.get("Priya Raghunathan"),
                "long": by_name.get("Maximiliane Theodora von Hohenzollern-Sigmaringen"),
                "script": by_name.get("李辰"),
                "org": organizations.get("GFZ Helmholtz Centre for Geosciences"),
                "org_bare": organizations.get("International Heat Flow Commission"),
                "org_long": organizations.get("Institute of Geology and Geophysics, Chinese Academy of Sciences"),
            },
        )
        return context
