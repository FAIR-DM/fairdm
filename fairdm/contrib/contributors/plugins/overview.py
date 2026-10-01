"""What the person and organization overview pages work out from a contributor.

A contributor holds contributions on other records rather than carrying contributions of its own, so these
pages share the record overview skeleton (``overview/page.html``) and its cards but not
``RecordOverviewPlugin``. Everything counted or listed is limited to the records the viewer can
open, so a profile never names a private record.
"""

from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.core.overview import json_ld, safe_reverse
from fairdm.core.plugins import OverviewPlugin

from ..models import Contributor
from ..profiles import active_then_recent, checklist, fill_slots, ranked_shares


@plugins.register(Contributor, label=_("Overview"), icon="overview", order=0)
class Overview(OverviewPlugin):
    """Lays out the person and organization overview pages.

    What a contributor has done, who it works with and what its record is missing are worked out
    by the models. This class picks what each page shows, in what order and how much of it, and
    supplies the page's own wording.

    Attributes:
        collaborators_shown: How many faces the Frequent collaborators card draws.
        records_shown: How many projects, and how many datasets, their cards list.
        member_slots: How many places the Members card has, the "+n" entry included.
    """

    url_path = None
    collaborators_shown = 18
    records_shown = 5
    member_slots = 10

    # ------------------------------------------------------------------ shared

    def get_template_names(self):
        """Draw the person or the organization page."""
        if self.base_object.is_organization:
            return ["contributors/overview/organization.html"]
        return ["contributors/overview/person.html"]

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

    def get_record_card(self, entries, active=None):
        """Shape a Projects or Datasets card: active records first, then the most recent.

        Args:
            entries: ``{"record", "owned"}`` dicts, one per record.
            active: Says whether a record counts as active, or None when the type has no such
                state.

        Returns:
            The entries to show, how many more there are, and the total.
        """
        ordered = active_then_recent(
            entries,
            modified=lambda entry: entry["record"].modified,
            active=(lambda entry: active(entry["record"])) if active else None,
        )
        return fill_slots(ordered, self.records_shown)

    def get_readiness(self, items, title, about, badge):
        """Shape a checklist for ``c-card.readiness``, with the page's wording."""
        readiness = checklist(items)
        readiness.update(
            title=title,
            summary=gettext("%(done)s of %(total)s in place") % readiness,
            about=about,
            badge=badge,
        )
        return readiness

    def get_shared_context(self):
        """The keys both pages and the shared skeleton read."""
        contributor = self.base_object
        identifier = contributor.default_identifier
        return {
            "record": contributor,
            "identifiers": [
                {"type": i.get_type_display(), "value": i.value, "link": i.resolver_url}
                for i in contributor.identifiers.all()
            ],
            "identifier": identifier,
            "identifier_url": identifier.resolver_url if identifier else None,
            "links": contributor.get_links_display(),
            "languages": ", ".join(contributor.get_language_names()),
            "json_ld": json_ld(contributor.to_public_schema_org()),
            "api_url": safe_reverse("api:contributor-detail", uuid=contributor.uuid),
            "urls": {
                "projects": safe_reverse(
                    "contributor:contributor-projects", uuid=contributor.uuid
                ),
                "datasets": safe_reverse(
                    "contributor:contributor-datasets", uuid=contributor.uuid
                ),
            },
        }

    # ------------------------------------------------------------------ person

    def get_person_context(self):
        """Everything the person page draws."""
        person = self.base_object
        user = self.request.user
        contributions = person.get_visible_contributions(user)
        context = self.get_shared_context()
        context["roles"] = ranked_shares(person.get_role_counts(contributions))
        is_self = user.is_authenticated and user.pk == person.pk
        affiliations = person.get_affiliation_history()
        primary = next(
            (a.organization for a in affiliations["current"] if a.is_primary), None
        )
        state = person.account_state
        collaborators = person.get_collaborators(contributions=contributions)
        projects = [{"record": p, "owned": False} for p in person.get_public_projects()]
        datasets = [{"record": d, "owned": False} for d in person.get_public_datasets()]

        context.update(
            {
                "overview_icon": "member",
                "person": person,
                "is_self": is_self,
                "is_unclaimed": state in ("ghost", "invited"),
                "is_inactive": state == "inactive",
                "affiliations": affiliations,
                "primary_organization": primary,
                "location_text": primary.get_location_display() if primary else "",
                "orcid_verified": person.orcid_is_authenticated,
                "portal_roles": person.portal_roles,
                "people": {
                    "shown": list(collaborators[: self.collaborators_shown]),
                    "more": max(collaborators.count() - self.collaborators_shown, 0),
                },
                "counts": {"project": len(projects), "dataset": len(datasets)},
                "projects": self.get_record_card(projects, lambda p: p.is_active),
                "datasets": self.get_record_card(datasets),
                "member_since": person.member_since,
            }
        )
        if is_self:
            complete = person.get_profile_completeness()
            context["readiness"] = self.get_readiness(
                [
                    {
                        "label": gettext("A profile photo"),
                        "done": complete["image"],
                        "required": False,
                    },
                    {
                        "label": gettext("ORCID iD connected by signing in with ORCID"),
                        "done": complete["orcid"],
                        "url": safe_reverse("socialaccount_connections"),
                    },
                    {
                        "label": gettext("A short biography"),
                        "done": complete["profile"],
                    },
                    {
                        "label": gettext("A primary affiliation"),
                        "done": complete["primary_affiliation"],
                    },
                    {
                        "label": gettext("Links to your other profiles"),
                        "done": complete["links"],
                        "required": False,
                    },
                ],
                title=gettext("Your profile"),
                about=gettext(
                    "A complete profile is how other researchers recognise your work and tell "
                    "you apart from someone with the same name."
                ),
                badge=gettext("Only you can see this"),
            )
        return context

    # ------------------------------------------------------------ organization

    def get_organization_context(self):
        """Everything the organization page draws."""
        organization = self.base_object
        user = self.request.user
        context = self.get_shared_context()
        members = organization.get_current_memberships()
        can_manage = organization.is_managed_by(user)

        projects = [
            {"record": p, "owned": p.owner_id == organization.pk}
            for p in organization.get_public_projects()
        ]
        datasets = [
            {"record": d, "owned": False} for d in organization.get_public_datasets()
        ]

        context.update(
            {
                "overview_icon": "organization",
                "organization": organization,
                "can_manage": can_manage,
                "is_member": organization.has_member(user),
                "members": fill_slots(members, self.member_slots, reserve=True),
                "projects": self.get_record_card(projects, lambda p: p.is_active),
                "datasets": self.get_record_card(datasets),
                "org_counts": {
                    "members": len(members),
                    "projects": len(projects),
                    "datasets": len(datasets),
                },
                "hierarchy": organization.get_hierarchy(),
                "location_text": organization.get_location_display(),
                "has_map": organization.location_id is not None,
            }
        )
        if can_manage:
            complete = organization.get_record_completeness()
            context["readiness"] = self.get_readiness(
                [
                    {"label": gettext("A ROR identifier"), "done": complete["ror"]},
                    {
                        "label": gettext("A logo"),
                        "done": complete["image"],
                        "required": False,
                    },
                    {
                        "label": gettext("The type of organization"),
                        "done": complete["type"],
                    },
                    {
                        "label": gettext("City and country"),
                        "done": complete["location"],
                    },
                    {"label": gettext("A description"), "done": complete["profile"]},
                    {
                        "label": gettext("A website"),
                        "done": complete["links"],
                        "required": False,
                    },
                ],
                title=gettext("Organization record"),
                about=gettext(
                    "A ROR identifier lets data repositories match this record to the same "
                    "organization everywhere else."
                ),
                badge=gettext("Only admin can see this"),
            )
        return context
