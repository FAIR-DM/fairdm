"""SKETCH ONLY. The views behind the record autocomplete fields, built to show the screens.

Untested, and rebuilt test-first once the screens are approved. See
``specs/032-record-search-fields/sketch.md`` for what is faked here.
"""

from django.db.models import Case, IntegerField, Q, Value, When
from django.utils.translation import gettext as _
from django_tomselect.autocompletes import AutocompleteIterablesView, AutocompleteModelView
from literature.models import LiteratureItem

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Organization, Person
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.utils.choices import Visibility

HIDDEN = "hidden"
PRIVATE_BADGE = "badge badge-sm badge-ghost shrink-0"

# Ranks that order results into their groups.
OWN, PUBLIC, OTHER = 0, 1, 2


class InheritLookups:
    """Keep list attributes a subclass does not set.

    django-tomselect's ``__init_subclass__`` gives every subclass empty ``search_lookups`` and
    ``value_fields`` unless it declares its own, so a shared base class loses them.
    """

    def __init_subclass__(cls, **kwargs):
        names = ("search_lookups", "value_fields")
        own = {name for name in names if name in cls.__dict__}
        inherited = {name: list(getattr(cls, name, [])) for name in names}
        super().__init_subclass__(**kwargs)
        for name in names:
            if name not in own:
                setattr(cls, name, inherited[name])


class RecordAutocomplete(InheritLookups, AutocompleteModelView):
    """Offer public records and, by scope, the private ones the person may reach.

    ``scope`` is fixed per address, never read from the request: ``public`` offers public records
    to everyone, ``view`` adds private records the person may view, ``edit`` offers only records
    the person may edit.
    """

    scope = "view"
    skip_authorization = True
    allow_anonymous = True
    page_size = 20
    search_lookups = ["name__icontains"]
    exact_lookups: list[str] = []
    noun_plural = ""

    def base_queryset(self):
        return self.model.objects.all()

    def public_q(self):
        return Q(visibility=Visibility.PUBLIC)

    def get_queryset(self):
        user = self.request.user
        records = self.base_queryset()
        public = records.filter(self.public_q())
        if self.scope == "public":
            offered = public
        elif self.scope == "edit":
            offered = records.accessible_to(user, ContributionLevel.EDIT)
        else:
            offered = (
                public | records.accessible_to(user, ContributionLevel.VIEW)
            ).distinct()
        own_ids = records.with_level(user, ContributionLevel.VIEW).values("pk")
        public_ids = public.values("pk")
        offered = offered.annotate(
            group_rank=Case(
                When(pk__in=own_ids, then=Value(OWN)),
                When(pk__in=public_ids, then=Value(PUBLIC)),
                default=Value(OTHER),
                output_field=IntegerField(),
            )
        )
        offered = self.hook_queryset(offered)
        offered = self.apply_filters(offered)
        offered = self.search(offered, self.query)
        return self.order(offered)

    def order(self, queryset):
        exact = Q()
        for lookup in self.exact_lookups:
            if self.query:
                exact |= Q(**{lookup: self.query})
        if exact:
            queryset = queryset.annotate(
                exact_rank=Case(
                    When(exact, then=Value(0)), default=Value(1), output_field=IntegerField()
                )
            ).distinct()
            return queryset.order_by("exact_rank", "group_rank", "name", "pk")
        return queryset.order_by("group_rank", "name", "pk")

    def get_value_fields(self):
        return ["id", "name", "group_rank", *self.value_fields]

    def group_names(self):
        return {
            OWN: _("Your %(things)s") % {"things": self.noun_plural},
            PUBLIC: _("Public %(things)s") % {"things": self.noun_plural},
            OTHER: _("Other %(things)s") % {"things": self.noun_plural},
        }

    def hook_prepare_results(self, results):
        names = self.group_names()
        ranks = {r["group_rank"] for r in results}
        for result in results:
            rank = result.pop("group_rank")
            # A list of one group needs no heading.
            if self.scope != "public" and (len(ranks) > 1 or rank != PUBLIC):
                result["optgroup"] = names[rank]
            self.describe(result)
        return results

    def describe(self, result):
        result.setdefault("detail", "")
        result.setdefault("badge", "")
        result["badge_class"] = PRIVATE_BADGE if result["badge"] else HIDDEN


class ProjectAutocomplete(RecordAutocomplete):
    model = Project
    noun_plural = _("projects")
    value_fields = ["visibility", "status"]

    def describe(self, result):
        private = result.pop("visibility") == Visibility.PRIVATE
        statuses = dict(Project._meta.get_field("status").flatchoices)
        result["detail"] = str(statuses.get(result.pop("status"), ""))
        result["badge"] = _("Private") if private else ""
        super().describe(result)


class DatasetAutocomplete(RecordAutocomplete):
    model = Dataset
    noun_plural = _("datasets")
    value_fields = ["visibility", "project__name", "project__visibility"]

    def base_queryset(self):
        return Dataset.all_objects.all()

    def public_q(self):
        return Q(visibility=Visibility.PUBLIC) & (
            Q(project__isnull=True) | Q(project__visibility=Visibility.PUBLIC)
        )

    def describe(self, result):
        private = result.pop("visibility") == Visibility.PRIVATE or (
            result.pop("project__visibility") == Visibility.PRIVATE
        )
        project = result.pop("project__name")
        result["detail"] = project or _("No project")
        result["badge"] = _("Private") if private else ""
        super().describe(result)


class TypedRecordAutocomplete(RecordAutocomplete):
    """Samples and measurements: public means a public, published dataset."""

    search_lookups = ["name__icontains", "local_id__icontains", "identifiers__value__iexact"]
    exact_lookups = ["local_id__iexact", "identifiers__value__iexact"]
    value_fields = [
        "local_id",
        "polymorphic_ctype__model",
        "dataset__name",
        "dataset__visibility",
        "dataset__published",
    ]

    def public_q(self):
        return Q(dataset__visibility=Visibility.PUBLIC, dataset__published=True)

    def app_label_for(self, model_name):
        from fairdm.registry import registry

        for model in [*registry.samples, *registry.measurements]:
            if model._meta.model_name == model_name:
                return model._meta.app_label
        return None

    def search(self, queryset, query):
        return super().search(queryset, query).distinct()

    def describe(self, result):
        from django.contrib.contenttypes.models import ContentType

        model = result.pop("polymorphic_ctype__model")
        app_label = self.app_label_for(model)
        model_class = (
            ContentType.objects.get_by_natural_key(app_label, model).model_class()
            if app_label
            else None
        )
        type_name = str(model_class._meta.verbose_name) if model_class else model
        local_id = result.pop("local_id")
        parts = [type_name.capitalize()]
        if local_id:
            parts.append(local_id)
        parts.append(result.pop("dataset__name"))
        result["detail"] = " · ".join(parts)
        private = not (
            result.pop("dataset__visibility") == Visibility.PUBLIC
            and result.pop("dataset__published")
        )
        result["badge"] = _("Private") if private else ""
        super().describe(result)


class SampleAutocomplete(TypedRecordAutocomplete):
    model = Sample
    noun_plural = _("samples")


class MeasurementAutocomplete(TypedRecordAutocomplete):
    model = Measurement
    noun_plural = _("measurements")
    search_lookups = ["name__icontains", "local_id__icontains"]
    exact_lookups = ["local_id__iexact"]


class ContributorAutocomplete(InheritLookups, AutocompleteModelView):
    """People or organizations, grouped by how the person searching relates to them."""

    skip_authorization = True
    allow_anonymous = True
    page_size = 20
    search_lookups = ["name__icontains", "alternative_names__icontains"]
    exact_lookups = ["identifiers__value__iexact"]
    near_label = ""
    far_label = ""

    def near_ids(self, user):
        return []

    def get_queryset(self):
        user = self.request.user
        queryset = self.model.objects.all()
        near = self.near_ids(user) if user.is_authenticated else []
        queryset = queryset.annotate(
            group_rank=Case(
                When(pk__in=near, then=Value(OWN)),
                default=Value(PUBLIC),
                output_field=IntegerField(),
            ),
        )
        if self.query:
            queryset = queryset.annotate(
                exact_rank=Case(
                    When(identifiers__value__iexact=self.query, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
        else:
            queryset = queryset.annotate(exact_rank=Value(1, output_field=IntegerField()))
        queryset = self.apply_filters(queryset)
        if self.query:
            terms = Q(identifiers__value__iexact=self.query)
            for lookup in self.search_lookups:
                terms |= Q(**{lookup: self.query})
            queryset = queryset.filter(terms)
        return queryset.distinct().order_by("exact_rank", "group_rank", "name", "pk")

    def get_value_fields(self):
        return ["id", "name", "group_rank"]

    def hook_prepare_results(self, results):
        objects = self.model.objects.in_bulk([r["id"] for r in results])
        ranks = {r["group_rank"] for r in results}
        for result in results:
            rank = result.pop("group_rank")
            if len(ranks) > 1 or rank == OWN:
                result["optgroup"] = self.near_label if rank == OWN else self.far_label
            self.describe(result, objects[result["id"]])
        return results

    def avatar(self, result, contributor):
        image = ""
        try:
            if contributor.image:
                image = contributor.image.url
        except ValueError:
            image = ""
        result["image"] = image
        result["image_class"] = "size-8 rounded-full shrink-0" if image else HIDDEN
        result["initials"] = contributor.get_initials()
        result["initials_class"] = (
            HIDDEN
            if image
            else "size-8 rounded-full shrink-0 bg-neutral text-neutral-content "
            "text-xs flex items-center justify-center"
        )


class PersonAutocomplete(ContributorAutocomplete):
    model = Person
    near_label = _("People you have worked with")
    far_label = _("Everyone else")

    def get_queryset(self):
        # Ghost profiles are listed too, marked as unclaimed. Accounts that are not people
        # (inactive staff shells) are not filtered out here: see sketch.md.
        return super().get_queryset()

    def near_ids(self, user):
        try:
            return [c.pk for c in user.get_collaborators(limit=200)]
        except Exception:  # noqa: BLE001 - sketch
            return []

    def describe(self, result, person):
        self.avatar(result, person)
        affiliation = person.primary_affiliation()
        orcid = person.orcid()
        parts = []
        if affiliation:
            parts.append(affiliation.organization.name)
        if orcid:
            parts.append(f"ORCID {orcid.value}")
        result["detail"] = " · ".join(parts) or _("No affiliation")
        unclaimed = not person.is_claimed and person.last_login is None
        result["badge"] = _("Unclaimed") if unclaimed else ""
        result["badge_class"] = PRIVATE_BADGE if unclaimed else HIDDEN


class OrganizationAutocomplete(ContributorAutocomplete):
    model = Organization
    near_label = _("Your organizations")
    far_label = _("Other organizations")

    def near_ids(self, user):
        return list(
            user.affiliations.filter(end_date__isnull=True).values_list(
                "organization_id", flat=True
            )
        )

    def describe(self, result, organization):
        self.avatar(result, organization)
        result["image_class"] = result["image_class"].replace("rounded-full", "rounded-box")
        result["initials_class"] = result["initials_class"].replace(
            "rounded-full", "rounded-box"
        ).replace("bg-neutral text-neutral-content", "bg-base-300")
        place = ", ".join(
            p for p in [organization.city, getattr(organization.country, "name", "")] if p
        )
        ror = organization.identifiers.filter(type="ROR").first()
        parts = [p for p in [place, f"ROR {ror.value}" if ror else ""] if p]
        result["detail"] = " · ".join(parts) or _("No location")
        result["badge"] = ""
        result["badge_class"] = HIDDEN


class PublicationAutocomplete(AutocompleteModelView):
    """The portal's literature, by title, author or DOI."""

    model = LiteratureItem
    skip_authorization = True
    allow_anonymous = True
    page_size = 20

    def get_queryset(self):
        queryset = LiteratureItem.objects.all()
        if self.query:
            queryset = queryset.filter(
                Q(title__icontains=self.query)
                | Q(item__author__icontains=self.query)
                | Q(item__DOI__iexact=self.query)
            ).annotate(
                exact_rank=Case(
                    When(item__DOI__iexact=self.query, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            ).order_by("exact_rank", "-issued", "pk")
        else:
            queryset = queryset.order_by("-issued", "pk")
        return queryset

    def get_value_fields(self):
        return ["id", "title"]

    def hook_prepare_results(self, results):
        items = LiteratureItem.objects.in_bulk([r["id"] for r in results])
        for result in results:
            item = items[result["id"]]
            data = item.item or {}
            authors = [
                a.get("family") or a.get("literal") or ""
                for a in data.get("author", [])
                if isinstance(a, dict)
            ]
            names = ", ".join(a for a in authors[:2] if a)
            if len(authors) > 2:
                names += _(" et al.")
            year = str(item.issued)[:4] if item.issued else ""
            result["name"] = result.pop("title") or _("Untitled")
            result["detail"] = " · ".join(str(p) for p in [names, year] if p)
            doi = data.get("DOI", "")
            result["badge"] = doi
            result["badge_class"] = "badge badge-sm badge-outline shrink-0" if doi else HIDDEN
        return results


class TagAutocomplete(AutocompleteIterablesView):
    """Tags already used in the portal."""

    skip_authorization = True
    allow_anonymous = True
    page_size = 20

    def get_iterable(self):
        from taggit.models import Tag

        tags = Tag.objects.order_by("name")
        if self.query:
            tags = tags.filter(name__icontains=self.query)
        return [{"value": t.name, "label": t.name} for t in tags[:200]]
