"""The Statistics tab of a person and of an organization.

Prototype code: the figures are worked out in Python on each request.
"""

from collections import Counter, defaultdict

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.overview import safe_reverse
from fairdm.core.statistics import RecordStatistics
from fairdm.views import FairDMTemplateView

from ..models import Contribution, Contributor, Organization
from ..profiles import ranked_shares


@plugins.register(Contributor, label=_("Statistics"), icon="statistics", order=300)
class Statistics(Plugin, FairDMTemplateView):
    """Lays out the person and the organization Statistics pages.

    A person's page counts what they are credited on and lists everyone they have worked with.
    An organization's page counts what its current members are credited on, beside its own
    records, and lists the organizations it shares records with. Projects and datasets are
    counted only when public, for every viewer.
    """

    url_path = "statistics"
    page_subtitle = _("Statistics")

    def get_template_names(self):
        """Draw the person or the organization page."""
        if self.base_object.is_organization:
            return ["contributors/statistics/organization.html"]
        return ["contributors/statistics/person.html"]

    def get_context_data(self, **kwargs):
        """Add everything the person or organization page draws."""
        context = super().get_context_data(**kwargs)
        if self.base_object.is_organization:
            context.update(self.get_organization_context())
        else:
            context.update(self.get_person_context())
        return context

    def get_breadcrumbs(self):
        """Lead the trail with the list of people or of organizations."""
        contributor = self.base_object
        if contributor.is_organization:
            first = {
                "text": gettext("Organizations"),
                "href": safe_reverse("organization-list"),
            }
        else:
            first = {"text": gettext("People"), "href": safe_reverse("people-list")}
        return [
            first,
            {"text": str(contributor), "href": contributor.get_absolute_url()},
        ]

    @staticmethod
    def by_year(records) -> dict[int, int]:
        """Count records by the year they were added to the portal."""
        return dict(Counter(record.added.year for record in records))

    # ------------------------------------------------------------------ person

    def get_person_context(self):
        """Everything the person page draws."""
        person = self.base_object
        contributions = person.get_visible_contributions(self.request.user)
        kinds = Counter(contribution.kind for contribution in contributions)
        projects = list(person.get_public_projects())
        datasets = list(person.get_public_datasets())
        collaborators = person.get_collaborators(contributions=contributions)
        return {
            "person": person,
            "has_credits": bool(contributions),
            "counts": {
                "projects": len(projects),
                "datasets": len(datasets),
                "samples": kinds.get("sample", 0),
                "measurements": kinds.get("measurement", 0),
            },
            "yearly_chart": RecordStatistics.get_yearly_chart(
                {
                    gettext("Projects"): self.by_year(projects),
                    gettext("Datasets"): self.by_year(datasets),
                }
            ),
            "roles": ranked_shares(person.get_role_counts(contributions)),
            "collaborators": list(collaborators),
        }

    # ------------------------------------------------------------ organization

    def get_organization_context(self):
        """Everything the organization page draws."""
        organization = self.base_object
        members = [m.person for m in organization.get_current_memberships()]
        own_projects = list(organization.get_public_projects())
        own_datasets = list(organization.get_public_datasets())

        member_projects, member_datasets = {}, {}
        active = defaultdict(set)
        for member in members:
            for project in member.get_public_projects():
                member_projects[project.pk] = project
                active[project.added.year].add(member.pk)
            for dataset in member.get_public_datasets():
                member_datasets[dataset.pk] = dataset
                active[dataset.added.year].add(member.pk)

        counted = (
            own_projects
            + own_datasets
            + list(member_projects.values())
            + list(member_datasets.values())
        )
        return {
            "organization": organization,
            "has_figures": bool(counted),
            "counts": {
                "own_projects": len(own_projects),
                "own_datasets": len(own_datasets),
                "member_projects": len(member_projects),
                "member_datasets": len(member_datasets),
                "members": len(members),
            },
            "yearly_chart": RecordStatistics.get_yearly_chart(
                {
                    gettext("Projects"): self.by_year(member_projects.values()),
                    gettext("Datasets"): self.by_year(member_datasets.values()),
                }
            ),
            "active_chart": RecordStatistics.get_yearly_chart(
                {
                    gettext("Active members"): {
                        year: len(people) for year, people in active.items()
                    }
                }
            ),
            "partners": self.get_partner_organizations(counted),
        }

    def get_partner_organizations(self, records):
        """List the other organizations on the records counted, most shared records first.

        An organization counts when it is credited on a record itself, or when it is the
        affiliation recorded on a person's credit there.

        Args:
            records: The projects and datasets the page counts.

        Returns:
            ``{"organization", "count", "percent"}`` entries.
        """
        organization = self.base_object
        ids_by_type = defaultdict(set)
        for record in records:
            ids_by_type[ContentType.objects.get_for_model(record).pk].add(
                str(record.pk)
            )
        shared = defaultdict(set)
        organization_ids = set(Organization.objects.values_list("pk", flat=True))
        for content_type, ids in ids_by_type.items():
            rows = Contribution.objects.filter(
                content_type_id=content_type, object_id__in=ids
            ).values_list("object_id", "contributor_id", "affiliation_id")
            for object_id, contributor_id, affiliation_id in rows:
                for candidate in (contributor_id, affiliation_id):
                    if candidate in organization_ids and candidate != organization.pk:
                        shared[candidate].add((content_type, object_id))
        if not shared:
            return []
        partners = Organization.objects.in_bulk(shared)
        ranked = sorted(
            ((partners[pk], len(found)) for pk, found in shared.items()),
            key=lambda item: (-item[1], item[0].name or ""),
        )
        most = ranked[0][1]
        return [
            {
                "organization": partner,
                "count": count,
                "percent": round(100 * count / most),
            }
            for partner, count in ranked
        ]
