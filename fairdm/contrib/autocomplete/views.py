"""Autocomplete views for FairDM models."""

import functools
import math

from dal import autocomplete
from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django_tomselect.autocompletes import AutocompleteModelView
from research_vocabs.models import Concept

from fairdm.contrib.autocomplete.throttling import (
    AutocompleteAnonBurstThrottle,
    AutocompleteAnonDailyThrottle,
    AutocompleteUserBurstThrottle,
    AutocompleteUserDailyThrottle,
)
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Contribution, Contributor, Organization
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample, SampleIdentifier
from fairdm.utils.choices import Visibility


class ConceptAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete view for Concept model with vocabulary filtering.

    This view allows filtering concepts by vocabulary to support large vocabularies
    efficiently without loading all concepts into the browser.

    Usage in forms:
        from dal import autocomplete

        field = forms.ModelMultipleChoiceField(
            queryset=Concept.objects.all(),
            widget=autocomplete.ModelSelect2Multiple(
                url='concept-autocomplete',
                forward=['vocabulary_name']  # Pass vocabulary name from another field
            )
        )

    Or with vocabulary specified in URL:
        widget=autocomplete.ModelSelect2Multiple(
            url='concept-autocomplete?vocabulary=gcmd-science-keywords'
        )
    """

    def get_queryset(self):
        """Return concepts filtered by vocabulary and search term, for signed-in users only."""
        if not self.request.user.is_authenticated:
            return Concept.objects.none()

        qs = Concept.objects.all()

        # No vocabulary is forwarded when DAL loads a field's initial values.
        vocabulary = self.forwarded.get("vocabulary", None)
        if not vocabulary:
            vocabulary = self.request.GET.get("vocabulary", None)

        if vocabulary:
            qs = qs.filter(vocabulary__name=vocabulary)

        if self.q:
            qs = qs.filter(Q(label__icontains=self.q) | Q(name__icontains=self.q))

        return qs.order_by("label")


class ContributorAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete view for Contributor model with filtering to exclude existing contributors.

    This view allows searching for contributors while optionally excluding those
    already associated with a specific object.

    Usage in forms:
        from dal import autocomplete, forward

        field = forms.ModelMultipleChoiceField(
            queryset=Contributor.objects.all(),
            widget=autocomplete.ModelSelect2Multiple(
                url='autocomplete:contributor',
                forward=(
                    forward.Const(str(base_object.pk), 'object_id'),
                    forward.Const(ContentType.objects.get_for_model(base_object).pk, 'content_type_id'),
                )
            )
        )
    """

    def get_queryset(self):
        """Return contributors matching the search term, minus those already on the forwarded object."""
        if not self.request.user.is_authenticated:
            return Contributor.objects.none()

        qs = Contributor.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        print(f"DEBUG: forwarded = {self.forwarded}")
        print(f"DEBUG: request.GET = {dict(self.request.GET)}")

        object_id = self.forwarded.get("object_id", None)
        content_type_id = self.forwarded.get("content_type_id", None)

        print(f"DEBUG: object_id = {object_id}, content_type_id = {content_type_id}")

        if object_id and content_type_id:
            existing_contributor_ids = Contribution.objects.filter(
                object_id=object_id, content_type_id=content_type_id
            ).values_list("contributor_id", flat=True)

            print(f"DEBUG: existing_contributor_ids = {list(existing_contributor_ids)}")

            qs = qs.exclude(pk__in=existing_contributor_ids)

        return qs.order_by("name")


class OrganizationAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete view for Organization model.

    This view allows searching for organizations by name.

    Usage in forms:
        from dal import autocomplete

        field = forms.ModelChoiceField(
            queryset=Organization.objects.all(),
            widget=autocomplete.ModelSelect2(url='autocomplete:organization')
        )
    """

    def get_queryset(self):
        """Return organizations matching the search term, for signed-in users only."""
        if not self.request.user.is_authenticated:
            return Organization.objects.none()

        qs = Organization.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by("name")

    def get_result_label(self, result):
        """Return the label to display for each result."""
        return result.label or result.name


#: Scope is part of the address, so a request can never widen what an address offers.
SCOPES = ("public", "view", "edit")

#: The ranks that order a page of records into its groups.
OWN, PUBLIC, OTHER = 0, 1, 2


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
            person may view. ``"edit"`` offers only the records the person may edit. Fixed by
            the address and never read from the request.
        noun_plural: The kind's name in the plural, for the headings of the groups.
        exact_lookups: Lookups on which an exact match is offered first.
    """

    scope = "view"
    exact_lookups: list[str] = []
    noun_plural = ""

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

    def offered(self, user, *, depends_on=None):
        """Return the records this scope offers a person, before any search or page.

        Args:
            user: The person searching, or an anonymous user.
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
        else:
            offered = records.filter(self.public_q()) | records.accessible_to(
                user, ContributionLevel.VIEW
            )
        return offered.filter(**depends_on) if depends_on else offered

    def get_queryset(self):
        """Return the offered records, searched, ranked into groups and ordered."""
        user = self.request.user
        records = self.base_queryset()
        queryset = self.offered(user).annotate(
            group_rank=Case(
                When(
                    pk__in=records.with_level(user, ContributionLevel.VIEW).values(
                        "pk"
                    ),
                    then=Value(OWN),
                ),
                When(
                    pk__in=records.filter(self.public_q()).values("pk"),
                    then=Value(PUBLIC),
                ),
                default=Value(OTHER),
                output_field=IntegerField(),
            )
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
