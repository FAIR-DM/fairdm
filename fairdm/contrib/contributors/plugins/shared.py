"""The Contributors tab of a project, dataset, sample or measurement.

Prototype for ``specs/022-record-contributors-and-access``: the screens are the deliverable and
the code behind them is to be rebuilt. ``specs/022-record-contributors-and-access/sketch.md``
lists what is faked.
"""

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from guardian.utils import get_anonymous_user
from research_vocabs.models import Concept

from fairdm import plugins
from fairdm.contrib.plugins import Plugin, reverse
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.views import FairDMTemplateView

from .. import access
from ..models import Contribution, Contributor


def type_name(record):
    """Return the word for a record's kind: project, dataset, sample or measurement."""
    return access.record_type(record)._meta.verbose_name


def level_choices(record, floor=None):
    """Return the three levels as the edit page draws them, marking those below ``floor``."""
    kind = type_name(record)
    hints = {
        access.VIEW: _("Open this %(kind)s while it is private.") % {"kind": kind},
        access.EDIT: _("Also change this %(kind)s and the data in it.")
        % {"kind": kind},
        access.MANAGE: _(
            "Also change its contributors and their access, change its visibility and delete it."
        ),
    }
    lowest = access.LEVELS.index(floor) if floor else 0
    return [
        {
            "value": level,
            "label": access.LEVEL_LABELS[level],
            "hint": hints[level],
            "disabled": index < lowest,
        }
        for index, level in enumerate(access.LEVELS)
    ]


class ContributionPage(Plugin, FairDMTemplateView):
    """What every page of the tab shares: the record, its kind and who may manage it."""

    manager_only = False

    def dispatch(self, request, *args, **kwargs):
        """Refuse a page for changing contributors to anyone who may not manage the record."""
        if self.manager_only and not access.can_manage(request.user, self.base_object):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    @property
    def list_url(self):
        """The address of the record's Contributors tab."""
        return reverse(self.base_object, "contribution-list")

    def get_contribution(self):
        """Return the contribution named in the address, on this record only."""
        return get_object_or_404(
            self.base_object.contributors.select_related("contributor"),
            pk=self.kwargs["pk"],
        )

    def describe(self, contribution):
        """Work out everything the pages say about one contributor on this record."""
        contributor = contribution.contributor.get_real_instance()
        is_person = not contributor.is_organization
        own = above = source = None
        if is_person:
            own = access.own_level(contributor, self.base_object)
            above, source = access.level_from_above(contributor, self.base_object)
        effective = access.higher(own, above)
        return {
            "contribution": contribution,
            "contributor": contributor,
            "is_person": is_person,
            "own": own,
            "above": above,
            "source": source,
            "source_kind": type_name(source) if source else "",
            "effective": effective,
            "label": access.LEVEL_LABELS.get(effective, ""),
            "from_above": bool(above and above == effective and above != own),
            "has_account": is_person and access.has_account(contributor),
        }

    def is_last_manager(self, contributor):
        """Say whether nobody else counts as able to manage the record."""
        return access.managers(self.base_object) == {contributor.pk}

    def get_context_data(self, **kwargs):
        """Add the record's kind, the tab's address and whether the viewer may manage."""
        context = super().get_context_data(**kwargs)
        record = self.base_object
        context.update(
            record=record,
            kind=type_name(record),
            list_url=self.list_url,
            can_manage=access.can_manage(self.request.user, record),
        )
        return context


class ContributionAdd(ContributionPage):
    """Find a person or an organization and add them to the record."""

    url_path = "add"
    manager_only = True
    template_name = "contributors/plugins/contribution_add.html"
    page_title = gettext_lazy("Add a contributor")
    results_shown = 20

    def get_context_data(self, **kwargs):
        """Add the search term and who it matches, marking those already listed."""
        context = super().get_context_data(**kwargs)
        term = self.request.GET.get("q", "").strip()
        listed = set(
            self.base_object.contributors.values_list("contributor_id", flat=True)
        )
        results = []
        if term:
            matches = (
                Contributor.objects.filter(name__icontains=term)
                .exclude(pk=get_anonymous_user().pk)
                .order_by("name")[: self.results_shown]
            )
            results = [{"contributor": c, "listed": c.pk in listed} for c in matches]
        context.update(term=term, results=results)
        return context

    def post(self, request, *args, **kwargs):
        """Add the chosen contributor last, at the view level, and go on to their roles."""
        record = self.base_object
        contributor = get_object_or_404(Contributor, pk=request.POST.get("contributor"))
        contributor = contributor.get_real_instance()
        if record.contributors.filter(contributor=contributor).exists():
            messages.error(
                request,
                _("%(name)s is already a contributor on this %(kind)s.")
                % {"name": contributor, "kind": type_name(record)},
            )
            return redirect(request.get_full_path())
        contribution = Contribution.add_to(contributor, record)
        if not contributor.is_organization and not access.own_level(
            contributor, record
        ):
            access.set_level(contributor, record, access.VIEW)
        messages.success(
            request,
            _("%(name)s was added. Say what they did, and what they may do here.")
            % {"name": contributor},
        )
        return redirect(f"{self.list_url}{contribution.pk}/edit/")


class ContributionEdit(ContributionPage):
    """Set a contributor's contribution roles and, for a person, their level."""

    url_path = "<int:pk>/edit"
    manager_only = True
    template_name = "contributors/plugins/contribution_edit.html"
    page_title = gettext_lazy("Edit a contributor")

    def get_roles(self):
        """Return the roles the record's type offers, in the vocabulary's order."""
        names = list(self.base_object.CONTRIBUTOR_ROLES.values)
        concepts = Concept.objects.filter(
            vocabulary__name="fairdm-roles", name__in=names
        )
        return sorted(concepts, key=lambda concept: names.index(concept.name))

    def get_context_data(self, **kwargs):
        """Add the contributor, the roles on offer and the levels that may be chosen."""
        context = super().get_context_data(**kwargs)
        entry = self.describe(self.get_contribution())
        held = set(entry["contribution"].roles.values_list("pk", flat=True))
        chosen_roles = kwargs.get("chosen_roles", held)
        context.update(
            entry=entry,
            roles=[
                {"concept": concept, "checked": concept.pk in chosen_roles}
                for concept in self.get_roles()
            ],
            levels=level_choices(self.base_object, floor=entry["above"]),
            chosen_level=kwargs.get("chosen_level", entry["effective"]),
            errors=kwargs.get("errors", {}),
        )
        return context

    def post(self, request, *args, **kwargs):
        """Save the roles and the level together, or neither."""
        record = self.base_object
        entry = self.describe(self.get_contribution())
        contribution, contributor = entry["contribution"], entry["contributor"]

        offered = {concept.pk: concept for concept in self.get_roles()}
        chosen_roles = {int(pk) for pk in request.POST.getlist("roles") if pk.isdigit()}
        level = request.POST.get("level")
        errors = {}

        if chosen_roles - set(offered):
            errors["roles"] = _("Choose from the roles listed for this %(kind)s.") % {
                "kind": type_name(record)
            }
        if entry["is_person"]:
            if level not in access.LEVELS:
                errors["level"] = _("Choose what this person may do.")
            elif access.higher(level, entry["above"]) != level:
                errors["level"] = _(
                    "They hold “%(level)s” from the %(kind)s above, and it cannot be lowered here."
                ) % {
                    "level": access.LEVEL_LABELS[entry["above"]],
                    "kind": entry["source_kind"],
                }
            elif (
                entry["own"] == access.MANAGE
                and level != access.MANAGE
                and self.is_last_manager(contributor)
            ):
                errors["level"] = _(
                    "%(name)s is the only person who can manage this %(kind)s. "
                    "Give someone else “Can manage” first."
                ) % {"name": contributor, "kind": type_name(record)}

        if errors:
            context = self.get_context_data(
                errors=errors, chosen_roles=chosen_roles, chosen_level=level
            )
            return self.render_to_response(context, status=422)

        contribution.roles.set([offered[pk] for pk in chosen_roles])
        if entry["is_person"]:
            access.set_level(contributor, record, level)
        messages.success(request, _("%(name)s was saved.") % {"name": contributor})
        return redirect(self.list_url)


class ContributionRemove(ContributionPage):
    """Confirm, then remove a contributor and whatever they held through being listed."""

    url_path = "<int:pk>/remove"
    manager_only = True
    template_name = "contributors/plugins/contribution_remove.html"
    page_title = gettext_lazy("Remove a contributor")

    def get_context_data(self, **kwargs):
        """Add the contributor and whether removing them would leave nobody to manage."""
        context = super().get_context_data(**kwargs)
        entry = self.describe(self.get_contribution())
        context.update(
            entry=entry,
            refused=entry["own"] == access.MANAGE
            and self.is_last_manager(entry["contributor"]),
        )
        return context

    def post(self, request, *args, **kwargs):
        """Remove the contributor unless they are the last who can manage the record."""
        record = self.base_object
        entry = self.describe(self.get_contribution())
        contributor = entry["contributor"]
        if entry["own"] == access.MANAGE and self.is_last_manager(contributor):
            return self.render_to_response(self.get_context_data(), status=422)
        if entry["is_person"]:
            access.set_level(contributor, record, None)
        entry["contribution"].delete()
        messages.success(
            request,
            _("%(name)s was removed from this %(kind)s.")
            % {"name": contributor, "kind": type_name(record)},
        )
        return redirect(self.list_url)


class ContributionMove(ContributionPage):
    """Move a contributor one place up or down the record's order."""

    url_path = "<int:pk>/move"
    manager_only = True
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        """Swap the contributor with their neighbour and renumber the record's order."""
        ordered = list(self.base_object.contributors.order_by("order", "pk"))
        index = next(i for i, c in enumerate(ordered) if c.pk == self.kwargs["pk"])
        target = index - 1 if request.POST.get("direction") == "up" else index + 1
        if 0 <= target < len(ordered):
            ordered[index], ordered[target] = ordered[target], ordered[index]
            for place, contribution in enumerate(ordered):
                contribution.order = place
            Contribution.objects.bulk_update(ordered, ["order"])
        return redirect(f"{self.list_url}#contributor-{self.kwargs['pk']}")


@plugins.register(
    Project,
    Dataset,
    Sample,
    Measurement,
    label=gettext_lazy("Contributors"),
    icon="users",
    order=150,
)
class ContributionList(ContributionPage):
    """List a record's contributors in order, with the controls for whoever may manage it."""

    url_path = "contributors"
    template_name = "contributors/plugins/contribution_list.html"
    page_title = gettext_lazy("Contributors")
    extra_views = [
        ContributionAdd,
        ContributionEdit,
        ContributionRemove,
        ContributionMove,
    ]

    def get_page_subtitle(self):
        """Name the record the contributors belong to."""
        return str(self.base_object)

    def get_context_data(self, **kwargs):
        """Add the contributors, the search term and, for a manager, access held from above."""
        context = super().get_context_data(**kwargs)
        record = self.base_object
        term = self.request.GET.get("q", "").strip()
        contributions = list(
            record.contributors.select_related("contributor")
            .prefetch_related("roles")
            .order_by("order", "pk")
        )
        total = len(contributions)
        rows = []
        for place, contribution in enumerate(contributions, start=1):
            if contribution.contributor is None:
                continue
            entry = self.describe(contribution)
            if term and term.lower() not in entry["contributor"].name.lower():
                continue
            entry.update(place=place, first=place == 1, last=place == total)
            rows.append(entry)

        above = []
        if context["can_manage"]:
            listed = {
                c.contributor_id for c in contributions if c.contributor_id is not None
            }
            above = [
                {
                    "person": person,
                    "label": access.LEVEL_LABELS[level],
                    "source": source,
                    "source_kind": type_name(source),
                    "source_url": reverse(source, "contribution-list"),
                }
                for person, level, source in access.people_above(record)
                if person.pk not in listed
            ]
        parents = access.records_above(record)
        context.update(
            rows=rows,
            total=total,
            term=term,
            above=above,
            parent=parents[0] if parents else None,
            parent_url=reverse(parents[0], "contribution-list") if parents else "",
            parent_kind=capfirst(type_name(parents[0])) if parents else "",
        )
        return context
