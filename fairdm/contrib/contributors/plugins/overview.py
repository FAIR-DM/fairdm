"""What the person and organization overview pages work out from a contributor.

A contributor holds credits on other records rather than carrying credits of its own, so these
pages share the record overview skeleton (``overview/page.html``) and its cards but not
``RecordOverviewPlugin``. Everything counted or listed is limited to the records the viewer can
open, so a profile never names a private record.
"""

from collections import Counter, defaultdict

from django.conf.locale import LANG_INFO
from django.utils.translation import gettext

from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.overview import (
    format_partial_date,
    json_ld,
    safe_reverse,
    sentence_case,
)
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample

from ..models import Affiliation, Contribution, Contributor

# The record types a credit can point at, in the order the pages show them, with each type's
# colour and icon from the record overview pages.
KINDS = {
    "project": {"model": Project, "variant": "info", "icon": "project"},
    "dataset": {"model": Dataset, "variant": "success", "icon": "dataset"},
    "sample": {"model": Sample, "variant": "secondary", "icon": "sample"},
    "measurement": {"model": Measurement, "variant": "accent", "icon": "measurement"},
}


class ContributorOverviewMixin:
    """Gathers the context of the person and organization overview pages."""

    collaborators_shown = 18
    credits_shown = 6
    members_shown = 12

    # ------------------------------------------------------------------ shared

    def get_breadcrumbs(self):
        """Lead the trail with the list of people or of organizations."""
        contributor = self.base_object
        if contributor.is_organization:
            first = {"text": gettext("Organizations"), "href": safe_reverse("organization-list")}
        else:
            first = {"text": gettext("People"), "href": safe_reverse("people-list")}
        return [first, {"text": str(contributor), "href": contributor.get_absolute_url()}]

    def visible_records(self, kind, ids):
        """Return the records of one kind among ``ids`` that the viewer may open, keyed by id."""
        user = self.request.user
        if kind == "project":
            queryset = Project.objects.get_visible()
        elif kind == "dataset":
            queryset = Dataset.objects.all()
        else:
            queryset = KINDS[kind]["model"].objects.visible_to(user)
        return {str(pk): obj for pk, obj in queryset.in_bulk(list(ids)).items()}

    def get_visible_credits(self, contributor=None):
        """List the contributor's credits on records the viewer may open, newest first.

        Each credit carries ``record`` (the credited object, as its own subtype), ``kind`` and
        ``style`` (the kind's colour and icon).
        """
        contributor = contributor or self.base_object
        credits = list(
            contributor.contributions.select_related("content_type")
            .prefetch_related("roles")
            .order_by("-id")
        )
        ids_by_kind = defaultdict(set)
        for credit in credits:
            credit.kind = self.kind_of(credit.content_type.model_class())
            if credit.kind:
                ids_by_kind[credit.kind].add(credit.object_id)
        records = {kind: self.visible_records(kind, ids) for kind, ids in ids_by_kind.items()}
        visible = []
        for credit in credits:
            record = records.get(credit.kind, {}).get(str(credit.object_id))
            if record is not None:
                credit.record = record
                credit.style = KINDS[credit.kind]
                credit.type_label = sentence_case(record._meta.verbose_name)
                visible.append(credit)
        return visible

    @staticmethod
    def kind_of(model_class):
        """Name the record kind a credited model belongs to, or None."""
        for kind, entry in KINDS.items():
            if model_class is not None and issubclass(model_class, entry["model"]):
                return kind
        return None

    @staticmethod
    def count_by_kind(credits):
        """Count distinct credited records of each kind."""
        counts = {kind: set() for kind in KINDS}
        for credit in credits:
            counts[credit.kind].add(credit.object_id)
        return {kind: len(ids) for kind, ids in counts.items()}

    @staticmethod
    def get_roles(credits):
        """Rank the roles held across the credits, with how many records each is held on."""
        counts = Counter(role.label for credit in credits for role in credit.roles.all())
        if not counts:
            return []
        most = max(counts.values())
        return [
            {"label": label, "count": count, "percent": round(100 * count / most)}
            for label, count in counts.most_common()
        ]

    def get_collaborators(self, credits):
        """Everyone else credited on the same visible records, most shared records first."""
        pairs = {(c.content_type_id, c.object_id) for c in credits}
        if not pairs:
            return {"shown": [], "more": 0, "total": 0}
        tally = Counter()
        others = Contribution.objects.filter(
            content_type_id__in={p[0] for p in pairs},
            object_id__in={p[1] for p in pairs},
        ).exclude(contributor=self.base_object).exclude(contributor__isnull=True)
        for content_type_id, object_id, contributor_id in others.values_list(
            "content_type_id", "object_id", "contributor_id"
        ):
            if (content_type_id, object_id) in pairs:
                tally[contributor_id] += 1
        ranked = [pk for pk, _ in tally.most_common()]
        shown_ids = ranked[: self.collaborators_shown]
        found = Contributor.objects.in_bulk(shown_ids)
        shown = [found[pk] for pk in shown_ids if pk in found]
        return {"shown": shown, "more": len(ranked) - len(shown), "total": len(ranked)}

    def get_identifiers(self):
        """Every identifier with the address it resolves to, in the Identifiers card's shape."""
        return [
            {
                "type": identifier.get_type_display(),
                "value": identifier.value,
                "link": self.identifier_link(identifier),
            }
            for identifier in self.base_object.identifiers.all()
        ]

    @staticmethod
    def identifier_link(identifier):
        """The address an identifier resolves to, when it is one that resolves."""
        url = identifier.get_absolute_url()
        return url if url and url.startswith("http") else None

    @staticmethod
    def get_links(contributor):
        """The contributor's links, each with the host name a reader recognises."""
        from urllib.parse import urlparse

        links = []
        for url in contributor.links or []:
            host = urlparse(url).netloc.removeprefix("www.")
            links.append({"url": url, "host": host or url})
        return links

    @staticmethod
    def language_names(codes):
        """Name each ISO 639-1 code in the portal's language, keeping unknown codes as written."""
        names = []
        for code in codes or []:
            info = LANG_INFO.get(code)
            names.append(gettext(info["name"]) if info else code)
        return ", ".join(names)

    def get_json_ld(self):
        """schema.org JSON-LD for the page, without the email address the page never shows."""
        data = self.base_object.to_schema_org()
        data.pop("email", None)
        return json_ld(data)

    @staticmethod
    def readiness(items, title, about):
        """Shape a checklist for ``c-card.readiness``."""
        done = sum(1 for item in items if item["done"])
        total = len(items)
        return {
            "items": items,
            "done": done,
            "total": total,
            "ready": done == total,
            "title": title,
            "summary": gettext("%(done)s of %(total)s in place") % {"done": done, "total": total},
            "about": about,
        }

    def get_shared_context(self, credits):
        """The keys both pages and the shared skeleton read."""
        contributor = self.base_object
        return {
            "record": contributor,
            "details": [],
            "contributor": contributor,
            "credits": credits,
            "recent_credits": credits[: self.credits_shown],
            "more_credits": max(len(credits) - self.credits_shown, 0),
            "counts": self.count_by_kind(credits),
            "roles": self.get_roles(credits),
            "identifiers": self.get_identifiers(),
            "links": self.get_links(contributor),
            "json_ld": self.get_json_ld(),
            "api_url": safe_reverse("api:contributor-detail", uuid=contributor.uuid),
            "urls": {
                "projects": safe_reverse("contributor:contributorprojects", uuid=contributor.uuid),
                "datasets": safe_reverse("contributor:contributordatasets", uuid=contributor.uuid),
            },
            "also_known_as": ", ".join(contributor.alternative_names or []),
            "languages": self.language_names(contributor.lang),
        }

    # ------------------------------------------------------------------ person

    def get_person_context(self):
        """Everything the person page draws."""
        person = self.base_object
        credits = self.get_visible_credits()
        context = self.get_shared_context(credits)
        is_self = self.request.user.is_authenticated and self.request.user.pk == person.pk

        affiliations = list(
            person.affiliations.select_related("organization")
            .prefetch_related("organization__identifiers")
            .filter(type__gte=Affiliation.MembershipType.MEMBER)
        )
        current = sorted(
            (a for a in affiliations if a.end_date is None),
            key=lambda a: (not a.is_primary, a.organization.name),
        )
        past = sorted(
            (a for a in affiliations if a.end_date is not None),
            key=lambda a: str(a.end_date),
            reverse=True,
        )
        for affiliation in affiliations:
            affiliation.start_text = format_partial_date(affiliation.start_date)
            affiliation.end_text = format_partial_date(affiliation.end_date)
        primary = next((a.organization for a in current if a.is_primary), None)
        orcid = next((i for i in person.identifiers.all() if i.type == "ORCID"), None)
        state = person.account_state

        context.update(
            {
                "overview_icon": "member",
                "person": person,
                "is_self": is_self,
                "can_manage": is_self,
                "account_state": state,
                "is_unclaimed": state in ("ghost", "invited"),
                "is_inactive": state == "inactive",
                "affiliations": {"current": current, "past": past},
                "primary_organization": primary,
                "location_text": primary.get_location_display() if primary else "",
                "orcid": orcid,
                "orcid_url": self.identifier_link(orcid) if orcid else None,
                "orcid_verified": person.orcid_is_authenticated,
                "portal_roles": person.portal_roles,
                "people": self.get_collaborators(credits),
            }
        )
        if is_self:
            context["readiness"] = self.readiness(
                [
                    {"label": gettext("A profile photo"), "done": bool(person.image), "required": False},
                    {
                        "label": gettext("ORCID iD connected by signing in with ORCID"),
                        "done": person.orcid_is_authenticated,
                        "url": safe_reverse("socialaccount_connections"),
                    },
                    {"label": gettext("A short biography"), "done": bool(person.profile)},
                    {"label": gettext("A primary affiliation"), "done": primary is not None},
                    {"label": gettext("Links to your other profiles"), "done": bool(person.links), "required": False},
                ],
                title=gettext("Your profile"),
                about=gettext(
                    "Only you see this. A complete profile is how other researchers recognise "
                    "your work and tell you apart from someone with the same name."
                ),
            )
        return context

    # ------------------------------------------------------------ organization

    def get_organization_context(self):
        """Everything the organization page draws."""
        organization = self.base_object
        credits = self.get_visible_credits()
        context = self.get_shared_context(credits)
        user = self.request.user

        memberships = list(
            organization.affiliations.select_related("person")
            .prefetch_related("person__identifiers", "person__socialaccount_set")
            .filter(type__gte=Affiliation.MembershipType.MEMBER)
        )
        current = sorted(
            (m for m in memberships if m.end_date is None),
            key=lambda m: (-m.type, m.person.name or ""),
        )
        former = [m for m in memberships if m.end_date is not None]
        managers = {
            m.person_id for m in current if m.type >= Affiliation.MembershipType.ADMIN
        }
        can_manage = user.is_authenticated and user.pk in managers
        owner = next(
            (m.person for m in current if m.type == Affiliation.MembershipType.OWNER), None
        )
        is_member = user.is_authenticated and any(m.person_id == user.pk for m in current)

        # Projects the organization owns come first, then those it is credited on.
        owned = list(Project.objects.get_visible().filter(owner=organization).order_by("name"))
        owned_ids = {p.pk for p in owned}
        credited_projects = [
            c for c in credits if c.kind == "project" and c.record.pk not in owned_ids
        ]
        projects = [{"project": p, "owned": True, "roles": []} for p in owned] + [
            {"project": c.record, "owned": False, "roles": list(c.roles.all())}
            for c in credited_projects
        ]
        datasets = set(
            Dataset.objects.filter(project__in=owned).values_list("pk", flat=True)
        ) | {c.record.pk for c in credits if c.kind == "dataset"}

        ror = next((i for i in organization.identifiers.all() if i.type == "ROR"), None)
        sub_organizations = list(organization.sub_organizations.order_by("name"))

        context.update(
            {
                "overview_icon": "organization",
                "organization": organization,
                "can_manage": can_manage,
                "is_member": is_member,
                "members": {
                    "shown": current[: self.members_shown],
                    "more": max(len(current) - self.members_shown, 0),
                    "total": len(current),
                    "former": len(former),
                },
                "owner": owner,
                "projects": projects,
                "org_counts": {
                    "members": len(current),
                    "projects": len(projects),
                    "datasets": len(datasets),
                },
                "ror": ror,
                "ror_url": self.identifier_link(ror) if ror else None,
                "sub_organizations": sub_organizations,
                "location_text": organization.get_location_display(),
                "has_map": organization.location_id is not None,
            }
        )
        if can_manage:
            context["readiness"] = self.readiness(
                [
                    {"label": gettext("A ROR identifier"), "done": ror is not None},
                    {"label": gettext("A logo"), "done": bool(organization.image), "required": False},
                    {"label": gettext("The type of organization"), "done": bool(organization.type)},
                    {"label": gettext("City and country"), "done": bool(organization.city and organization.country)},
                    {"label": gettext("A description"), "done": bool(organization.profile)},
                    {"label": gettext("A website"), "done": bool(organization.links), "required": False},
                ],
                title=gettext("Organization record"),
                about=gettext(
                    "Only the organization's owners and administrators see this. A ROR "
                    "identifier lets data repositories match this record to the same "
                    "organization everywhere else."
                ),
            )
        return context

