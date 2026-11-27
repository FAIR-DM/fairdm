"""Adding an organization on a record's Contributors tab, in steps drawn in one sheet.

The steps are: find an organization in the portal, or start one from the search, then
what ROR has under that name ("Do you mean?"), and the organization's roles. The last
step posts.
"""

from urllib.parse import urlencode

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from ..models import Contribution, Organization
from ..services.crediting import Crediting
from ..services.registries import Ror
from .tab_base import ContributorsBase, initials_of
from .tab_people import PORTAL_RESULTS


class AddOrganization(ContributorsBase):
    """The Add organization sheet: find one, or name a new one, then pick its roles."""

    name = "add-organization"
    url_path = "add-organization"

    def title(self):
        """Return the sheet's own title."""
        return _("Add an organization to this %(kind)s") % {"kind": self.access.kind}

    def step_url(self, **query):
        """Return the address of a step of this sheet, carrying what is known of the
        organization.
        """
        query = {key: value for key, value in query.items() if value}
        return (
            self.record_url("contribution-list-add-organization")
            + "?"
            + urlencode(query)
        )

    def get(self, request, *args, **kwargs):
        """Open the sheet at its search step, answer a search, or draw a later step."""
        new_name = request.GET.get("new_name", "").strip()
        ror = request.GET.get("ror", "").strip()
        if ror:
            return self.picked_from_ror(ror, new_name)
        if new_name and request.GET.get("skip"):
            return self.roles_step(
                None, new_name, back=self.step_url(new_name=new_name)
            )
        if new_name:
            return self.ror_matches_step(new_name)
        if request.GET.get("organization"):
            return self.roles_step(
                get_object_or_404(Organization, uuid=request.GET["organization"])
            )
        return self.search_step()

    def search_step(self):
        """Open the sheet, answer a search of the portal, or draw the search again for
        Back.
        """
        request = self.request
        query = request.GET.get("q", "").strip()
        listed = Contribution.objects.for_entity(self.base_object).values_list(
            "contributor_id", flat=True
        )
        found = Organization.objects.exclude(pk__in=listed)
        if query:
            found = found.filter(name__icontains=query)
        found = list(found.order_by("name")[:PORTAL_RESULTS])
        context = {
            "found": found,
            "query": query,
            "step_url": self.record_url("contribution-list-add-organization"),
        }
        if len(query) > 1 and not any(o.name.lower() == query.lower() for o in found):
            context["new_row"] = {
                "name": query,
                "initials": Organization(name=query).get_initials(),
                "organization": True,
                "url": self.step_url(new_name=query),
            }
        if request.headers.get("HX-Target") == "contrib-organization-results":
            return self.step_response(
                "cotton/contributor/tab/organization_results.html",
                context,
                chrome=False,
            )
        if request.GET.get("back"):
            context["head"] = {"title": self.title()}
            return self.step_response(
                "cotton/contributor/tab/organization_search.html", context
            )
        return self.sheet_response(
            "contributors/tab/sheets/add_organization.html", context, self.title()
        )

    def picked_from_ror(self, ror, new_name):
        """Draw the roles step for an organization picked from ROR."""
        record, problem = self.search_registry(Ror().fetch, ror)
        if record is None:
            return self.ror_matches_step(new_name, problem=problem or "missing")
        known = Ror().known(record)
        back = self.step_url(new_name=new_name or record["name"])
        return self.roles_step(
            known, record["name"], "" if known else record["id"], back=back
        )

    def ror_matches_step(self, new_name, problem=""):
        """Draw what ROR finds under the name given, to pick from or skip."""
        found = None
        if not problem:
            found, problem = self.search_registry(Ror().search, new_name)
        results = (found or {"results": []})["results"]
        return self.step_response(
            "contributors/tab/sheets/ror_matches.html",
            {
                "found": [{**r, "initials": initials_of(r, True)} for r in results],
                "problem": problem,
                "new_name": new_name,
                "pick_url": self.step_url(new_name=new_name),
                "next_url": self.step_url(new_name=new_name, skip=1),
                "next_text": _("Add by name alone"),
                "back_url": self.record_url("contribution-list-add-organization")
                + "?"
                + urlencode({"back": 1, "q": new_name}),
                "head": {
                    "title": _("Do you mean?"),
                    "lead": _("Powered by the Research Organization Registry (ROR)"),
                },
            },
        )

    def roles_step(self, organization, new_name="", ror="", back=""):
        """Draw the step that picks the organization's roles on this record.

        Args:
            organization: The organization, when it is in the portal.
            new_name: The name of one not in the portal yet.
            ror: Its ROR ID, when it was picked from ROR.
            back: Where Back goes, the search step when not given.
        """
        context = {
            "organization": organization,
            "new_name": new_name,
            "ror": ror,
            "adding": True,
            "for_organization": True,
            "credit": None,
            **self.role_context(None),
            "action": self.record_url("contribution-list-add-organization"),
            "submit_text": _("Add to the %(kind)s") % {"kind": self.access.kind},
            "head": self.head_for(organization, new_name, organization=True),
            "back_url": back
            or self.record_url("contribution-list-add-organization") + "?back=1",
        }
        return self.step_response(
            "cotton/contributor/tab/organization_form.html", context
        )

    def post(self, request, *args, **kwargs):
        """List the organization with its roles."""
        if request.POST.get("organization"):
            organization = get_object_or_404(
                Organization, uuid=request.POST["organization"]
            )
        elif request.POST.get("ror"):
            record, problem = self.search_registry(
                Ror().fetch, request.POST["ror"].strip()
            )
            if record is None:
                return self.registry_refusal("ROR", problem)
            organization = Ror().known(record) or Ror().profile(record)
        else:
            name = request.POST.get("new_name", "").strip()
            if not name:
                return HttpResponseBadRequest()
            organization = None
        crediting = Crediting(self.base_object)
        try:
            with transaction.atomic():
                organization = organization or Organization.objects.create(name=name)
                crediting.list_organization(organization)
                credit = self.base_object.contributors.get(contributor=organization)
                crediting.update(credit, roles=self.chosen_roles(held=None))
        except ValidationError as error:
            return self.refusal(error)
        return self.region_response(
            toast={"text": _("%(name)s added.") % {"name": organization.name}}
        )
