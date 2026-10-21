"""Autocomplete views for FairDM records, people, organizations, publications, tags and ROR."""

import functools
import logging
import math

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Case, CharField, IntegerField, Q, Value, When
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django_tomselect.autocompletes import (
    AutocompleteIterablesView,
    AutocompleteModelView,
)
from literature.models import LiteratureItem
from taggit.models import Tag

from fairdm.contrib.autocomplete.throttling import (
    AutocompleteAnonBurstThrottle,
    AutocompleteAnonDailyThrottle,
    AutocompleteUserBurstThrottle,
    AutocompleteUserDailyThrottle,
)
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import (
    Affiliation,
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.contrib.contributors.services.registries import RegistryUnavailable, Ror
from fairdm.contrib.generic.models import TaggedItem
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample, SampleIdentifier
from fairdm.utils.choices import Visibility

logger = logging.getLogger(__name__)


#: Scope is part of the address, so a request can never widen what an address offers.
SCOPES = ("public", "view", "edit")

#: The scope of the one address per kind that offers a person's own records, named by ``owner``.
PROFILE = "profile"

#: A tag is not edited through a record, so its address has no ``edit`` scope.
TAG_SCOPES = ("public", "view")

#: The ranks that order a page of records into its groups. PREFERRED holds the records that
#: match what the field asked to see first, whoever they belong to.
PREFERRED, OWN, PUBLIC, OTHER = -1, 0, 1, 2


@functools.cache
def scoped_view(view_class, scope):
    """Return the subclass of a record view that serves one scope.

    django-tomselect rebuilds a view as ``view_class()`` when it validates a value, so the
    scope has to be an attribute of the class and cannot be an argument of ``as_view()``.

    Args:
        view_class: The record view to subclass.
        scope: One of ``"public"``, ``"view"`` or ``"edit"``.

    Returns:
        A subclass of ``view_class`` with ``scope`` set. The same class for the same arguments.
    """
    return type(
        f"{view_class.__name__}_{scope}",
        (view_class,),
        {
            "scope": scope,
            "search_lookups": list(view_class.search_lookups),
            "value_fields": list(view_class.value_fields),
        },
    )


class LimitedAutocompleteMixin:
    """Keep what one request can cost, and what it can reveal, in the view's hands.

    Attributes:
        page_size: The results in a page. A request cannot change it.
        max_pages: The last page that is served.
        max_query_length: The longest search text. Longer text is cut.
        throttle_classes: The limits on one caller, checked before anything is searched.
        allowed_filter_fields: The fields a request may filter on through ``f`` and ``e``. A
            request naming any other field is offered nothing.
        allowed_ordering_fields: The fields a request may order by. Others are ignored.
    """

    skip_authorization = True
    allow_anonymous = True
    page_size = 20
    max_pages = 25
    max_query_length = 100
    allowed_filter_fields: list[str] = []
    allowed_ordering_fields: list[str] = []
    throttle_classes = (
        AutocompleteAnonBurstThrottle,
        AutocompleteAnonDailyThrottle,
        AutocompleteUserBurstThrottle,
        AutocompleteUserDailyThrottle,
    )

    def dispatch(self, request, *args, **kwargs):
        """Refuse a caller over a limit, before anything is searched."""
        throttles = [throttle() for throttle in self.throttle_classes]
        refused = [t for t in throttles if not t.allow_request(request, self)]
        if refused:
            waits = [wait for t in refused if (wait := t.wait())]
            response = JsonResponse(
                {"results": [], "page": 1, "has_more": False}, status=429
            )
            response["Retry-After"] = str(math.ceil(max(waits, default=1)))
            return response
        return super().dispatch(request, *args, **kwargs)

    def setup(self, request, *args, **kwargs):
        """Fix the page size and the length of the search text, whatever the request asks."""
        super().setup(request, *args, **kwargs)
        self.page_size = type(self).page_size
        self.query = self.query[: self.max_query_length]

    def paginate_queryset(self, queryset):
        """Serve nothing past the last page of results or past the page limit."""
        try:
            requested = max(1, int(self.page))
        except (TypeError, ValueError):
            requested = 1
        empty = {
            "results": [],
            "page": requested,
            "has_more": False,
            "next_page": None,
            "total_pages": self.max_pages,
        }
        if requested > self.max_pages:
            return empty
        data = super().paginate_queryset(queryset)
        if data["page"] != requested:
            return empty
        if requested == self.max_pages:
            data["has_more"] = False
            data["next_page"] = None
        return data

    def get(self, request, *args, **kwargs):
        """Answer a search that failed with the failure and nothing else."""
        response = super().get(request, *args, **kwargs)
        if response.status_code >= 500:
            return JsonResponse(
                {"results": [], "page": 1, "has_more": False}, status=500
            )
        return response


class RecordAutocompleteView(LimitedAutocompleteMixin, AutocompleteModelView):
    """Offer the records of one kind that the person searching may reach at one scope.

    Attributes:
        scope: ``"public"`` offers public records to everyone. ``"view"`` adds the records the
            person may view. ``"edit"`` offers only the records the person may edit.
            ``"profile"`` offers the records one person, the ``owner``, is credited on: their
            private ones only to them. Fixed by the address and never read from the request.
        noun_plural: The kind's name in the plural, for the headings of the groups.
        exact_lookups: Lookups on which an exact match is offered first.
        prefer_param: The request parameter that names a relation and a value, as
            ``dataset=5``. Records that match come first, in a group of their own. It orders
            and groups, and never adds or removes a record.
        preferred_heading: The heading of the preferred group, with ``%(things)s`` standing
            for the kind's name in the plural.
    """

    scope = "view"
    exact_lookups: list[str] = []
    noun_plural = ""
    prefer_param = "prefer"
    preferred_heading = ""

    @classmethod
    def for_scope(cls, scope):
        """Return the subclass of this view that serves one scope.

        Args:
            scope: One of ``"public"``, ``"view"`` or ``"edit"``.

        Returns:
            The view class for that scope.
        """
        return scoped_view(cls, scope)

    def base_queryset(self):
        """Return every record of the kind, before any visibility rule.

        Returns:
            A queryset over the kind's records.
        """
        return self.model.objects.all()

    def public_q(self):
        """Return the condition under which a record is public.

        Returns:
            A ``Q`` object over the kind's records.
        """
        return Q(visibility=Visibility.PUBLIC)

    def offered(self, user, *, owner=None, type=None, depends_on=None):  # noqa: A002
        """Return the records this scope offers a person, before any search or page.

        Args:
            user: The person searching, or an anonymous user.
            owner: The person whose records the ``profile`` scope offers, as a person or a
                primary key. Other scopes ignore it.
            type: A registered sample or measurement type to keep, or ``None`` for every type.
            depends_on: Lookups the records must match, such as ``{"dataset": 5}``, when the
                field chooses within another field's value. Each lookup must be one the view
                allows a request to filter on.

        Returns:
            A queryset of the records the scope offers that person.
        """
        records = self.base_queryset()
        if self.scope == "public":
            offered = records.filter(self.public_q())
        elif self.scope == "edit":
            offered = records.accessible_to(user, ContributionLevel.EDIT)
        elif self.scope == PROFILE:
            offered = self.credited_to(user, owner)
        else:
            offered = records.filter(self.public_q()) | records.accessible_to(
                user, ContributionLevel.VIEW
            )
        if type is not None:
            offered = offered.filter(
                polymorphic_ctype=ContentType.objects.get_for_model(type)
            )
        return offered.filter(**depends_on) if depends_on else offered

    def credited_to(self, user, owner):
        """Return the records one person is credited on that a person may be offered.

        Args:
            user: The person searching, or an anonymous user.
            owner: The person whose records are wanted, or their primary key.

        Returns:
            The owner's records, private ones included only when ``user`` is the owner.
            Nothing when there is no such person.
        """
        records = self.base_queryset()
        if not isinstance(owner, Person):
            owner = Person.objects.filter(pk=owner).first()
        if owner is None:
            return records.none()
        credited = records.with_level(owner, ContributionLevel.VIEW)
        if user is not None and user.is_authenticated and user.pk == owner.pk:
            return credited
        return credited.filter(self.public_q())

    def requested_owner(self):
        """Return the primary key the request names as the owner, or ``None``."""
        owner = self.request.GET.get("owner", "")
        return owner if self.scope == PROFILE and owner.isdigit() else None

    def preference(self):
        """Return the condition the request asks to see first.

        Only a relation the view allows a request to filter on is accepted, and only a value
        that can name a record of it. Anything else is ignored.

        Returns:
            A ``Q`` object, or ``None`` when the request asks for nothing the view can use.
        """
        relation, _separator, value = self.request.GET.get(
            self.prefer_param, ""
        ).partition("=")
        if relation not in self.allowed_filter_fields or not value:
            return None
        try:
            value = self.model._meta.get_field(relation).target_field.to_python(value)
        except ValidationError:
            return None
        return Q(**{relation: value})

    def get_queryset(self):
        """Return the offered records, searched, ranked into groups and ordered."""
        user = self.request.user
        records = self.base_queryset()
        ranks = [
            When(
                pk__in=records.with_level(user, ContributionLevel.VIEW).values("pk"),
                then=Value(OWN),
            ),
            When(
                pk__in=records.filter(self.public_q()).values("pk"),
                then=Value(PUBLIC),
            ),
        ]
        if (preferred := self.preference()) is not None:
            ranks.insert(0, When(preferred, then=Value(PREFERRED)))
        queryset = self.offered(user, owner=self.requested_owner()).annotate(
            group_rank=Case(*ranks, default=Value(OTHER), output_field=IntegerField())
        )
        queryset = self.apply_filters(self.hook_queryset(queryset))
        queryset = self.search(queryset, self.query)
        ordering = ["group_rank", "name", "pk"]
        if self.query and self.exact_lookups:
            queryset = queryset.annotate(
                exact_rank=Case(
                    When(self.exact_q(self.query), then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            ordering.insert(0, "exact_rank")
        return queryset.order_by(*ordering)

    def exact_q(self, query):
        """Return the condition under which a record matches a search exactly.

        Args:
            query: The text searched for.

        Returns:
            A ``Q`` object, empty when the kind has no exact lookups.
        """
        exact = Q()
        for lookup in self.exact_lookups:
            exact |= Q(**{lookup: query})
        return exact

    def search(self, queryset, query):
        """Match the text on the search lookups, and on the exact lookups as well."""
        if not query:
            return queryset
        matched = self._build_simple_search_q(query) | self.exact_q(query)
        return queryset.filter(matched)

    def get_value_fields(self):
        """Return the fields the results are built from."""
        return ["id", "name", "group_rank", *self.value_fields]

    def group_names(self):
        """Return the heading of each group, by rank."""
        return {
            PREFERRED: self.preferred_heading
            % {"things": str(self.noun_plural).capitalize()},
            OWN: _("Your %(things)s") % {"things": self.noun_plural},
            PUBLIC: _("Public %(things)s") % {"things": self.noun_plural},
            OTHER: _("Other %(things)s") % {"things": self.noun_plural},
        }

    def hook_prepare_results(self, results):
        """Add each result's group heading and its row, drawn on the server."""
        names = self.group_names()
        ranks = {result["group_rank"] for result in results}
        for result in results:
            rank = result.pop("group_rank")
            # A page holding only public records needs no heading.
            if len(ranks) > 1 or rank != PUBLIC:
                result["optgroup"] = names[rank]
            self.describe(result)
            result["html"] = render_to_string(
                "autocomplete/record_option.html",
                {
                    "name": result["name"],
                    "detail": result.pop("detail", ""),
                    "badge": _("Private") if result["private"] else "",
                },
                request=self.request,
            )
        return results

    def describe(self, result):
        """Turn the raw values of one result into what its row shows.

        Args:
            result: The result, changed in place. It gains ``private`` and may gain
                ``detail``, the line shown beneath the name.
        """
        result["private"] = result.pop("visibility") != Visibility.PUBLIC


class DatasetAutocompleteView(RecordAutocompleteView):
    """Offer datasets, starting from every dataset so that private ones can be reached."""

    model = Dataset
    noun_plural = _("datasets")
    search_lookups = ["name__icontains"]
    exact_lookups = ["uuid__iexact"]
    value_fields = ["visibility", "project__name", "project__visibility"]

    def base_queryset(self):
        """Return every dataset, private ones included."""
        return Dataset.all_objects.all()

    def public_q(self):
        """Return the condition for a dataset that is public along with its project."""
        return Q(visibility=Visibility.PUBLIC) & (
            Q(project__isnull=True) | Q(project__visibility=Visibility.PUBLIC)
        )

    def describe(self, result):
        """Show the dataset's project, and mark it private when it or its project is."""
        project_visibility = result.pop("project__visibility")
        project = result.pop("project__name")
        result["project"] = project
        result["detail"] = project or _("No project")
        super().describe(result)
        result["private"] = result["private"] or (
            project_visibility is not None and project_visibility != Visibility.PUBLIC
        )


class ProjectAutocompleteView(RecordAutocompleteView):
    """Offer projects, public by their own visibility."""

    model = Project
    noun_plural = _("projects")
    search_lookups = ["name__icontains"]
    exact_lookups = ["uuid__iexact"]
    value_fields = ["visibility", "status"]

    def describe(self, result):
        """Show the project's status."""
        statuses = dict(Project._meta.get_field("status").flatchoices)
        result["detail"] = str(statuses.get(result.pop("status"), ""))
        super().describe(result)


#: What a row of a sample or a measurement is built from. Each concrete view names it itself,
#: because django-tomselect empties a list that a subclass does not set on its own class.
DATASET_RECORD_FIELDS = ["local_id", "dataset__name", "polymorphic_ctype"]


class DatasetRecordsAutocompleteView(RecordAutocompleteView):
    """Offer samples or measurements, the records that sit inside a dataset.

    A record of these kinds is public when its dataset is public and published.
    """

    allowed_filter_fields = ["dataset", "polymorphic_ctype"]
    preferred_heading = _("%(things)s in this dataset")

    def public_q(self):
        """Return the condition for a record whose dataset is public and published."""
        return Q(dataset__visibility=Visibility.PUBLIC, dataset__published=True)

    def get_value_fields(self):
        """Add the visibility of the record's own dataset, which decides its badge."""
        return [
            *super().get_value_fields(),
            "dataset__visibility",
            "dataset__published",
        ]

    def describe(self, result):
        """Show the record's type, local ID and dataset, and mark it private unless released."""
        kind = ContentType.objects.get_for_id(result.pop("polymorphic_ctype"))
        result["type"] = str(kind.model_class()._meta.verbose_name)
        result["dataset"] = result.pop("dataset__name")
        result["detail"] = " · ".join(
            part
            for part in (result["type"], result["local_id"], result["dataset"])
            if part
        )
        released = result.pop(
            "dataset__visibility"
        ) == Visibility.PUBLIC and result.pop("dataset__published")
        result["private"] = not released


class SampleAutocompleteView(DatasetRecordsAutocompleteView):
    """Offer samples, found by name, local ID or identifier."""

    model = Sample
    noun_plural = _("samples")
    search_lookups = ["name__icontains", "local_id__icontains"]
    exact_lookups = ["local_id__iexact", "uuid__iexact"]
    value_fields = DATASET_RECORD_FIELDS

    def exact_q(self, query):
        """Match the local ID, the UUID and any identifier typed exactly."""
        identified = SampleIdentifier.objects.filter(value__iexact=query)
        return super().exact_q(query) | Q(pk__in=identified.values("related_id"))

    def search(self, queryset, query):
        """Match the text on name and local ID, on an identifier that contains it, and exactly."""
        if not query:
            return queryset
        identified = SampleIdentifier.objects.filter(value__icontains=query)
        matched = (
            self._build_simple_search_q(query)
            | self.exact_q(query)
            | Q(pk__in=identified.values("related_id"))
        )
        return queryset.filter(matched)


class MeasurementAutocompleteView(DatasetRecordsAutocompleteView):
    """Offer measurements, found by name or local ID."""

    model = Measurement
    noun_plural = _("measurements")
    search_lookups = ["name__icontains", "local_id__icontains"]
    exact_lookups = ["local_id__iexact", "uuid__iexact"]
    value_fields = DATASET_RECORD_FIELDS


class ContributorAutocompleteView(LimitedAutocompleteMixin, AutocompleteModelView):
    """Offer the people or the organizations of the portal, those nearest the person searching first.

    A person or an organization is public information, so one address serves everyone and the
    scope plays no part.

    Attributes:
        identifier_type: The identifier on which an exact match is offered first.
        near_heading: The heading of the group listed first.
        far_heading: The heading of the group listed after it.
    """

    identifier_type = ""
    near_heading = ""
    far_heading = ""

    @classmethod
    def for_scope(cls, scope):
        """Return this view, which serves every scope alike.

        Args:
            scope: Ignored.

        Returns:
            The view class.
        """
        return cls

    def base_queryset(self):
        """Return every contributor of the kind, before any rule on who is offered.

        Returns:
            A queryset over the kind's contributors.
        """
        return self.model.objects.all()

    def offered(self, user, *, depends_on=None):
        """Return the contributors offered to a person, before any search or page.

        Args:
            user: The person searching, or an anonymous user.
            depends_on: Not used, since these views allow no filter.

        Returns:
            A queryset of the offered contributors.
        """
        return self.base_queryset()

    def nearby(self, user):
        """Return the primary keys of the contributors listed first for a person.

        Args:
            user: The signed-in person searching.

        Returns:
            A list of primary keys.
        """
        return []

    def exact_q(self, query):
        """Return the condition under which a contributor's identifier is the text typed.

        Args:
            query: The text searched for.

        Returns:
            A ``Q`` object over the kind's contributors.
        """
        identified = ContributorIdentifier.objects.filter(
            type=self.identifier_type, value__iexact=query
        )
        return Q(pk__in=identified.values("related_id"))

    def get_queryset(self):
        """Return the offered contributors, searched, grouped by nearness and ordered."""
        user = self.request.user
        near = self.nearby(user) if user.is_authenticated else []
        queryset = self.offered(user).annotate(
            group_rank=Case(
                When(pk__in=near, then=Value(OWN)),
                default=Value(PUBLIC),
                output_field=IntegerField(),
            )
        )
        queryset = self.apply_filters(self.hook_queryset(queryset))
        ordering = ["group_rank", "name", "pk"]
        if self.query:
            exact = self.exact_q(self.query)
            queryset = queryset.filter(
                self._build_simple_search_q(self.query) | exact
            ).annotate(
                exact_rank=Case(
                    When(exact, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            ordering.insert(0, "exact_rank")
        return queryset.order_by(*ordering)

    def get_value_fields(self):
        """Return the fields the results are built from."""
        return ["id", "name", "group_rank"]

    def loaded(self, ids):
        """Load the contributors of a page with what their rows show.

        Args:
            ids: The primary keys of the page.

        Returns:
            A dict of contributors by primary key.
        """
        return self.model.objects.in_bulk(ids)

    def describe(self, result, contributor):
        """Work out what one row shows.

        Args:
            result: The result, changed in place.
            contributor: The contributor the result stands for.

        Returns:
            The extra context the row is drawn with.
        """
        return {}

    def hook_prepare_results(self, results):
        """Add each result's group heading and its row, drawn on the server."""
        headings = {OWN: self.near_heading, PUBLIC: self.far_heading}
        ranks = {result["group_rank"] for result in results}
        loaded = self.loaded([result["id"] for result in results])
        for result in results:
            rank = result.pop("group_rank")
            # A page holding only the far group needs no heading.
            if len(ranks) > 1 or rank != PUBLIC:
                result["optgroup"] = headings[rank]
            contributor = loaded[result["id"]]
            context = self.describe(result, contributor)
            result["html"] = render_to_string(
                "autocomplete/contributor_option.html",
                {"contributor": contributor, **context},
                request=self.request,
            )
        return results


class PersonAutocompleteView(ContributorAutocompleteView):
    """Offer people, found by name, alternative name or ORCID, collaborators first.

    Superusers and the anonymous placeholder account are never offered. An email address is
    neither searched nor shown.
    """

    model = Person
    identifier_type = "ORCID"
    search_lookups = ["name__icontains", "alternative_names__icontains"]
    value_fields = []
    near_heading = _("People you have worked with")
    far_heading = _("Everyone else")

    def offered(self, user, *, depends_on=None):
        """Offer every person who is not a superuser or the anonymous placeholder."""
        return Person.objects.real()

    def nearby(self, user):
        """Return the people credited on a record that the person searching can open."""
        return list(
            user.get_collaborators(
                contributions=self.openable_credits(user)
            ).values_list("pk", flat=True)
        )

    @staticmethod
    def openable_credits(user):
        """Return the person's credits on the records the person may view.

        A credit on a private record that carries no access to it does not count, so a person
        met only there is not someone the searcher has worked with.

        Args:
            user: The person searching.

        Returns:
            A list of contributions.
        """
        views = (
            ProjectAutocompleteView,
            DatasetAutocompleteView,
            SampleAutocompleteView,
            MeasurementAutocompleteView,
        )
        credits_by_view = {}
        for credit in user.contributions.select_related("content_type"):
            model_class = credit.content_type.model_class()
            view = next(
                (
                    v
                    for v in views
                    if model_class is not None and issubclass(model_class, v.model)
                ),
                None,
            )
            if view is not None:
                credits_by_view.setdefault(view, []).append(credit)
        openable = []
        for view, held in credits_by_view.items():
            records = view.for_scope("view")().offered(user)
            reachable = set(
                records.filter(pk__in=[c.object_id for c in held]).values_list(
                    "pk", flat=True
                )
            )
            openable.extend(c for c in held if int(c.object_id) in reachable)
        return openable

    def loaded(self, ids):
        """Load the people with their identifiers and affiliations."""
        return self.model.objects.prefetch_related(
            "identifiers", "affiliations__organization"
        ).in_bulk(ids)

    def describe(self, result, person):
        """Show the person's primary affiliation and ORCID, and mark one nobody has claimed."""
        affiliation = person.primary_affiliation()
        organization = affiliation.organization if affiliation else None
        result["detail"] = organization.name if organization else ""
        result["unclaimed"] = not person.is_claimed and person.last_login is None
        return {
            "organization": organization,
            "identifier": person.get_default_identifier(),
            "identifier_icon": "orcid",
            "badge": _("Unclaimed") if result["unclaimed"] else "",
        }


class OrganizationAutocompleteView(ContributorAutocompleteView):
    """Offer organizations, found by name, alternative name or ROR, the researcher's own first."""

    model = Organization
    identifier_type = "ROR"
    search_lookups = ["name__icontains", "alternative_names__icontains"]
    value_fields = []
    near_heading = _("Your organizations")
    far_heading = _("Other organizations")

    def nearby(self, user):
        """Return the organizations the person belongs to: verified and not ended."""
        return list(
            Affiliation.objects.current()
            .filter(person=user, type__gt=Affiliation.MembershipType.PENDING)
            .values_list("organization_id", flat=True)
        )

    def describe(self, result, organization):
        """Show where the organization is, and no identifier."""
        place = ", ".join(
            part
            for part in (organization.city, getattr(organization.country, "name", ""))
            if part
        )
        result["detail"] = place
        return {"place": place}


class PublicationAutocompleteView(LimitedAutocompleteMixin, AutocompleteModelView):
    """Offer publications, found by title, author or DOI, a DOI typed exactly first.

    Literature carries no visibility of its own, so one address serves everyone and the scope
    plays no part.
    """

    model = LiteratureItem
    search_lookups = ["title__icontains", "item__author__icontains"]
    value_fields = ["title"]

    @classmethod
    def for_scope(cls, scope):
        """Return this view, which serves every scope alike.

        Args:
            scope: Ignored.

        Returns:
            The view class.
        """
        return cls

    @staticmethod
    def bare_doi(text):
        """Take the DOI out of text that is one, or the address of one.

        Args:
            text: A search term.

        Returns:
            The text without a ``doi:`` or ``https://doi.org/`` prefix.
        """
        text = text.strip()
        for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
            text = text.removeprefix(prefix)
        return text

    def get_queryset(self):
        """Return the publications that match the search, those with the DOI typed first."""
        queryset = self.apply_filters(self.hook_queryset(self.model.objects.all()))
        ordering = ["title", "pk"]
        if self.query:
            exact = Q(item__DOI__iexact=self.bare_doi(self.query))
            queryset = queryset.filter(
                self._build_simple_search_q(self.query) | exact
            ).annotate(
                exact_rank=Case(
                    When(exact, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            ordering.insert(0, "exact_rank")
        return queryset.order_by(*ordering)

    def hook_prepare_results(self, results):
        """Give each result its authors, year and DOI, and its row drawn on the server."""
        items = dict(
            self.model.objects.filter(pk__in=[r["id"] for r in results]).values_list(
                "pk", "item"
            )
        )
        for result in results:
            item = items[result["id"]]
            authors = [
                author.get("family") or author.get("literal") or author.get("name")
                for author in item.get("author") or []
            ]
            result["authors"] = ", ".join(filter(None, authors))
            result["year"] = self.year_of(item)
            result["doi"] = item.get("DOI") or ""
            result["html"] = render_to_string(
                "autocomplete/record_option.html",
                {
                    "name": result["title"],
                    "detail": " · ".join(
                        str(part)
                        for part in (result["authors"], result["year"])
                        if part
                    ),
                    "badge": result["doi"],
                    "badge_outline": True,
                },
                request=self.request,
            )
        return results

    @staticmethod
    def year_of(item):
        """Read the year a publication was issued from its CSL data.

        Args:
            item: The publication's CSL JSON.

        Returns:
            The year, or ``None`` when the data gives none.
        """
        try:
            return int(item["issued"]["date-parts"][0][0])
        except (KeyError, IndexError, TypeError, ValueError):
            return None


class TagAutocompleteView(LimitedAutocompleteMixin, AutocompleteModelView):
    """Offer the tags in use on the records the person searching may reach, found by name.

    Attributes:
        scope: ``"public"`` offers the tags on public records, to everyone. ``"view"`` adds the
            tags on the records the person may view. Fixed by the address and never read from
            the request.
    """

    model = Tag
    search_lookups = ["name__icontains"]
    value_fields = ["name"]
    scope = "view"

    @classmethod
    def for_scope(cls, scope):
        """Return the subclass of this view that serves one scope.

        Args:
            scope: One of ``"public"`` or ``"view"``.

        Returns:
            The view class for that scope.
        """
        return scoped_view(cls, scope)

    def offered(self, user, *, depends_on=None):
        """Return the tags this scope offers a person, before any search or page.

        A tag is offered when it is in use on a project, dataset, sample or measurement that the
        record view of the same scope offers that person, so no tag reveals a record.

        Args:
            user: The person searching, or an anonymous user.
            depends_on: Not used, since this view allows no filter.

        Returns:
            A queryset of tags.
        """
        reachable = Q()
        for view in (
            ProjectAutocompleteView,
            DatasetAutocompleteView,
            SampleAutocompleteView,
            MeasurementAutocompleteView,
        ):
            records = view.for_scope(self.scope)().offered(user)
            # A tag item holds the key as text and the type of the concrete model, and keys of
            # different tables can be equal.
            kinds = ContentType.objects.get_for_models(
                *(m for m in apps.get_models() if issubclass(m, view.model))
            ).values()
            reachable |= Q(
                content_type__in=kinds,
                object_id__in=records.annotate(key=Cast("pk", CharField())).values(
                    "key"
                ),
            )
        return Tag.objects.filter(
            pk__in=TaggedItem.objects.filter(reachable).values("tag_id")
        )

    def get_queryset(self):
        """Return the offered tags, searched and ordered by name."""
        queryset = self.apply_filters(
            self.hook_queryset(self.offered(self.request.user))
        )
        return self.search(queryset, self.query).order_by("name", "pk")


class RorAutocompleteView(LimitedAutocompleteMixin, AutocompleteIterablesView):
    """Offer the organizations of the Research Organization Registry that match the search.

    The registry holds public information, so one address serves everyone and the scope plays
    no part. A search that ROR does not answer is answered with status 503.
    """

    @classmethod
    def for_scope(cls, scope):
        """Return this view, which serves every scope alike.

        Args:
            scope: Ignored.

        Returns:
            The view class.
        """
        return cls

    def get_iterable(self):
        """Search ROR for the text typed, and draw each match as a row.

        Returns:
            A list of ``{"value", "label", "detail", "html"}`` dicts, empty when nothing is typed.

        Raises:
            RegistryUnavailable: ROR could not be asked or answered badly.
        """
        if not self.query.strip():
            return []
        return [
            {
                "value": record["id"],
                "label": record["name"],
                "detail": record["detail"],
                "html": render_to_string(
                    "autocomplete/record_option.html",
                    {
                        "name": record["name"],
                        "detail": record["detail"],
                        "badge": record["shown_id"],
                        "badge_outline": True,
                    },
                    request=self.request,
                ),
            }
            for record in Ror().search(self.query)["results"]
        ]

    def get(self, request, *args, **kwargs):
        """Answer with the matches, or with the failure and nothing else."""
        try:
            data = self.paginate_iterable(self.get_iterable())
        except RegistryUnavailable:
            return self.refusal(503)
        except Exception:
            logger.exception("Error in the ROR autocomplete request")
            return self.refusal(500)
        return JsonResponse(data, encoder=self.get_json_encoder())

    def refusal(self, status):
        """Return an empty answer with a failure status.

        Args:
            status: The HTTP status.

        Returns:
            A ``JsonResponse`` that names no cause.
        """
        return JsonResponse(
            {"results": [], "page": 1, "has_more": False}, status=status
        )
