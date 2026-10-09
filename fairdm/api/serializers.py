"""Serializer base classes for projects, datasets, samples, measurements and contributors."""

import copy
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Model, Prefetch, Q
from django.db.models.manager import BaseManager
from django.urls import NoReverseMatch
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from research_vocabs.models import Concept
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import get_error_detail
from rest_framework.reverse import reverse

from fairdm.api.filters import FairDMVisibilityFilter, _get_public_filter
from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import (
    Contribution,
    Contributor,
    Organization,
    Person,
)
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.models import Dataset, Measurement, Project, Sample

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class CreatorCreditMixin:
    """Credit the person who creates a record through the API, and hold back what needs manage.

    Visibility and the record a record sits under decide who can get in, so changing either needs
    the manage level on the record, as on the update forms.

    Attributes:
        manager_only_fields: The names of the fields only someone who can manage the record may
            change.
    """

    manager_only_fields = ("visibility", "owner", "project", "dataset", "sample")

    def get_fields(self):
        """Offer as a parent only the records the requesting user holds the edit level on.

        The same choices the forms give for a project, dataset or sample field, so a record can
        only be created or moved into a parent the user may edit. A record being updated also
        keeps its current parent as a choice, so a request that repeats it is not refused.

        Returns:
            The serializer's fields.
        """
        from fairdm.core.models import Dataset, Project, Sample

        fields = super().get_fields()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        stored = self.instance if isinstance(self.instance, Model) else None
        for name, manager in (
            ("project", Project.objects),
            ("dataset", Dataset.all_objects),
            ("sample", Sample.objects),
        ):
            field = fields.get(name)
            if not isinstance(field, serializers.RelatedField) or field.read_only:
                continue
            choices = manager.accessible_to(user, ContributionLevel.EDIT)
            current = getattr(stored, f"{name}_id", None)
            if current is not None:
                choices = manager.filter(Q(pk__in=choices.values("pk")) | Q(pk=current))
            field.queryset = choices
        return fields

    @staticmethod
    def differs(instance, name, value) -> bool:
        """Say whether a value sent for a field is not what the record already holds.

        A parent is compared by primary key: the field offers a sample as its base class and
        the record holds it as its own type, which Django does not call equal.

        Args:
            instance: The record being updated.
            name: The name of the field.
            value: The validated value sent for it.

        Returns:
            True when the value would change the record.
        """
        if isinstance(value, Model):
            return bool(value.pk != getattr(instance, f"{name}_id", None))
        return bool(value != getattr(instance, name, None))

    def create(self, validated_data):
        """Create the record, then list the requesting user on it at the manage level.

        Args:
            validated_data: The validated fields of the new record.

        Returns:
            The new record.
        """
        record = super().create(validated_data)
        Crediting(record).make_creator(self.context["request"].user)
        return record

    def update(self, instance, validated_data):
        """Update the record, refusing what only a manager may change, or a move that strands it.

        Args:
            instance: The record to update.
            validated_data: The validated fields to set.

        Returns:
            The updated record.

        Raises:
            PermissionDenied: When a manager-only field would change and the requesting user
                cannot manage the record.
            serializers.ValidationError: When the new project or dataset would leave nobody who
                can sign in able to manage the record.
        """
        changed = [
            name
            for name in self.manager_only_fields
            if name in validated_data
            and self.differs(instance, name, validated_data[name])
        ]
        if changed and not RecordAccess(instance).can_manage(
            self.context["request"].user
        ):
            raise PermissionDenied(
                _("Changing %(fields)s needs the manage level on this record.")
                % {"fields": ", ".join(changed)},
                code="manage_level_required",
            )
        for name in ("project", "dataset"):
            if name in changed:
                moved = copy.copy(instance)
                setattr(moved, name, validated_data[name])
                try:
                    RecordAccess(moved).refuse_move_without_manager(name)
                except DjangoValidationError as error:
                    raise serializers.ValidationError(
                        get_error_detail(error)
                    ) from error
        return super().update(instance, validated_data)


@extend_schema_field(
    {
        "type": "object",
        "nullable": True,
        "properties": {
            "uuid": {"type": "string"},
            "url": {"type": "string", "format": "uri", "nullable": True},
        },
    }
)
class RecordReferenceField(serializers.SlugRelatedField):
    """Refer to a record by its short identifier and its address in the API.

    A record is returned as ``{"uuid": ..., "url": ...}``, or as ``None`` when the requesting
    user may not see it, by the rule :class:`~fairdm.api.filters.FairDMVisibilityFilter` applies
    to a list. A bare identifier or the returned object is accepted. A database number is
    refused, like any identifier that names no record.

    A page of records is checked in one query: :class:`RecordListSerializer` calls
    :meth:`prime` with the page before it is serialized.
    """

    def __init__(self, **kwargs):
        """Look records up by ``uuid`` unless told otherwise.

        Args:
            **kwargs: Passed to ``SlugRelatedField``. A ``queryset`` makes the field writable.
        """
        kwargs.setdefault("slug_field", "uuid")
        super().__init__(**kwargs)
        self.checked = frozenset()
        self.visible = frozenset()

    @staticmethod
    def route_name(record) -> str:
        """Return the name of the route that serves one record.

        Args:
            record: A project, dataset, sample, measurement or contributor.

        Returns:
            The route name in the ``api`` namespace.
        """
        from fairdm.api.viewsets import _model_to_slug

        real_class = getattr(record, "get_real_instance_class", None)
        model = (real_class() if real_class else None) or type(record)
        if issubclass(model, Contributor):
            return "api:contributor-detail"
        if issubclass(model, Sample):
            return f"api:samples-{_model_to_slug(model)}-detail"
        if issubclass(model, Measurement):
            return f"api:measurements-{_model_to_slug(model)}-detail"
        return f"api:{model._meta.model_name}-detail"

    def visible_pks(self, model, pks) -> set:
        """Say which of the records the requesting user may see.

        Args:
            model: The model, or a subclass of it, the records belong to.
            pks: The primary keys to check.

        Returns:
            The primary keys the user may see.
        """
        core = getattr(model, "type_of", None) or model
        if issubclass(core, Contributor):
            # Asked once per request: the accounts it holds are few, the references many.
            context = cast("dict[str, Any]", self.context)
            if "hidden_contributors" not in context:
                hidden = FairDMVisibilityFilter.hidden_contributors()
                context["hidden_contributors"] = set(
                    hidden.values_list("pk", flat=True)
                )
            hidden_pks: set = context["hidden_contributors"]
            return set(pks) - hidden_pks
        if not _get_public_filter(core):
            return set(pks)
        manager = getattr(core, "all_objects", core._default_manager)
        queryset = manager.filter(pk__in=pks)
        if hasattr(queryset, "non_polymorphic"):
            queryset = queryset.non_polymorphic()
        request = self.context.get("request") or SimpleNamespace(user=AnonymousUser())
        visible = FairDMVisibilityFilter().filter_queryset(
            cast("Request", request), queryset, cast("APIView", None)
        )
        return set(visible.values_list("pk", flat=True))

    def prime(self, records, many: str | None = None) -> None:
        """Check the records this field refers to in a page of records, in one query.

        Args:
            records: The page of records about to be serialized.
            many: The name of the many-to-many relation this field is the child of, if it is.
        """
        if many:
            name = many
            pks = {
                related.pk
                for record in records
                for related in getattr(record, name).all()
            }
        elif len(self.source_attrs) == 1 and records:
            name = self.source_attrs[0]
            pks = {getattr(record, f"{name}_id", None) for record in records} - {None}
        else:
            return
        if not pks:
            return
        self.checked = frozenset(pks)
        self.visible = frozenset(
            self.visible_pks(records[0]._meta.get_field(name).related_model, pks)
        )

    def is_visible(self, record) -> bool:
        """Say whether the requesting user may see a record.

        Args:
            record: The record referred to.

        Returns:
            True when the user may see it.
        """
        if record.pk in self.checked:
            return record.pk in self.visible
        return record.pk in self.visible_pks(type(record), [record.pk])

    def to_internal_value(self, data):
        """Accept an identifier, or an object carrying one as ``uuid``."""
        if isinstance(data, dict):
            data = data.get("uuid")
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)

    def to_representation(self, record):
        """Return the record's identifier and address, or ``None`` when it is hidden."""
        if not self.is_visible(record):
            return None
        try:
            url = reverse(
                self.route_name(record),
                kwargs={"uuid": record.uuid},
                request=self.context.get("request"),
            )
        except NoReverseMatch:
            url = None
        return {"uuid": record.uuid, "url": url}

    def get_choices(self, cutoff=None):
        """Key the choices by identifier, as the browsable pages need a hashable key."""
        queryset = self.get_queryset()
        if queryset is None:
            return {}
        if cutoff is not None:
            queryset = queryset[:cutoff]
        return {record.uuid: self.display_value(record) for record in queryset}


class RecordURLField(serializers.HyperlinkedIdentityField):
    """The address of a record in the API, whatever type the record is."""

    def __init__(self, **kwargs):
        """Look the record up by ``uuid``; the route comes from the record itself.

        Args:
            **kwargs: Passed to ``HyperlinkedIdentityField``.
        """
        kwargs.setdefault("lookup_field", "uuid")
        super().__init__(view_name="", **kwargs)

    def get_url(self, obj, view_name, request, format):  # noqa: A002
        """Build the address from the route that serves this record's type."""
        return reverse(
            RecordReferenceField.route_name(obj),
            kwargs={"uuid": obj.uuid},
            request=request,
            format=format,
        )


class PortalPageField(serializers.ReadOnlyField):
    """The address of a record's own page on the portal's website.

    The address is absolute when the serializer has a request, and the path alone when it has
    none.
    """

    def __init__(self, **kwargs):
        """Read the whole record, as the address comes from its method.

        Args:
            **kwargs: Passed to ``ReadOnlyField``.
        """
        kwargs["source"] = "*"
        super().__init__(**kwargs)

    def to_representation(self, value) -> str:
        """Return the address of the record's page.

        Args:
            value: The record or contributor.

        Returns:
            The absolute address, or the path when there is no request.
        """
        path: str = value.get_absolute_url()
        request = self.context.get("request")
        address: str = request.build_absolute_uri(path) if request else path
        return address


class RecordListSerializer(serializers.ListSerializer):
    """List serializer that checks every reference on a page of records at once."""

    def to_representation(self, data):
        """Prime each reference field with the whole page, then serialize each record."""
        records = list(data.all() if isinstance(data, BaseManager) else data)
        for name, field in self.child.fields.items():
            if isinstance(field, RecordReferenceField):
                field.prime(records)
            elif isinstance(field, serializers.ManyRelatedField) and isinstance(
                field.child_relation, RecordReferenceField
            ):
                field.child_relation.prime(records, many=name)
        return [self.child.to_representation(record) for record in records]


class DescriptionSerializer(serializers.Serializer):
    """A typed description of a record."""

    type = serializers.CharField(read_only=True)
    value = serializers.CharField(read_only=True)


class DateSerializer(serializers.Serializer):
    """A typed key date of a record, as a year, a month or a day."""

    type = serializers.CharField(read_only=True)
    value = serializers.CharField(read_only=True)


class IdentifierSerializer(serializers.Serializer):
    """A typed external identifier of a record."""

    type = serializers.CharField(read_only=True)
    value = serializers.CharField(read_only=True)


class KeywordSerializer(serializers.Serializer):
    """A controlled keyword of a record and the vocabulary it comes from."""

    name = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)  # type: ignore[assignment]
    uri = serializers.CharField(read_only=True)
    vocabulary = serializers.CharField(source="vocabulary.name", read_only=True)


class RoleSerializer(serializers.Serializer):
    """A role a contributor holds on a record."""

    name = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)  # type: ignore[assignment]


class ContributionSerializer(serializers.Serializer):
    """A credit on a record: who, in what roles, and from which organisation.

    The access level a credit carries is not shown, as the record's page does not show it.
    """

    contributor = RecordReferenceField(read_only=True)
    roles = RoleSerializer(many=True, read_only=True)
    affiliation = RecordReferenceField(read_only=True)


class LicenseSerializer(serializers.Serializer):
    """The licence a dataset is published under."""

    name = serializers.CharField(read_only=True)
    url = serializers.CharField(source="canonical_url", read_only=True)


class RecordSerializer(CreatorCreditMixin, serializers.ModelSerializer):
    """Serializer for a project, dataset, sample or measurement.

    Adds what every record carries: its address, identifier and dates of change, and the five
    kinds of metadata, which are read-only.

    Attributes:
        metadata_fields: The metadata every record carries.
        parents: The relations to load with the record, so a list costs no query per record.
    """

    metadata_fields = (
        "descriptions",
        "dates",
        "identifiers",
        "keywords",
        "contributors",
    )
    parents: tuple[str, ...] = ()

    url = RecordURLField(read_only=True)
    html_url = PortalPageField()
    descriptions = DescriptionSerializer(many=True, read_only=True)
    dates = DateSerializer(many=True, read_only=True)
    identifiers = IdentifierSerializer(many=True, read_only=True)
    keywords = KeywordSerializer(many=True, read_only=True)
    contributors = ContributionSerializer(many=True, read_only=True)

    class Meta:
        list_serializer_class = RecordListSerializer

    @classmethod
    def load_related(cls, queryset):
        """Load the parents and metadata a serialized record reads.

        Args:
            queryset: The records about to be serialized.

        Returns:
            The queryset with its parents selected and its metadata prefetched.
        """
        credits_ = Contribution.objects.select_related(
            "contributor", "affiliation"
        ).prefetch_related("roles")
        return queryset.select_related(*cls.parents).prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
            Prefetch("keywords", queryset=Concept.objects.select_related("vocabulary")),
            Prefetch("contributors", queryset=credits_),
        )


class ProjectSerializer(RecordSerializer):
    """A project with its owner and its metadata."""

    parents = ("owner",)

    owner = RecordReferenceField(
        queryset=Organization.objects.all(), allow_null=True, required=False
    )

    class Meta(RecordSerializer.Meta):
        model = Project
        fields = [
            "url",
            "html_url",
            "uuid",
            "name",
            "image",
            "status",
            "visibility",
            "funding",
            "owner",
            "added",
            "modified",
            *RecordSerializer.metadata_fields,
        ]
        read_only_fields = ["image"]


class DatasetSerializer(RecordSerializer):
    """A dataset with its project, its licence and its metadata."""

    parents = ("project", "license")

    project = RecordReferenceField(
        queryset=Project.objects.all(), allow_null=True, required=False
    )
    license = LicenseSerializer(read_only=True)

    class Meta(RecordSerializer.Meta):
        model = Dataset
        fields = [
            "url",
            "html_url",
            "uuid",
            "name",
            "image",
            "project",
            "visibility",
            "published",
            "license",
            "added",
            "modified",
            *RecordSerializer.metadata_fields,
        ]
        read_only_fields = ["image", "published"]


class BaseSampleSerializer(RecordSerializer):
    """Base DRF serializer for all Sample subtypes.

    All auto-generated serializers for registered :class:`~fairdm.core.sample.models.Sample`
    subclasses inherit from this class.  When a portal developer provides a custom
    ``serializer_class`` via the registry config it MUST subclass this class; otherwise
    :func:`generate_viewset` raises :exc:`~django.core.exceptions.ImproperlyConfigured`.

    Attributes:
        common_fields: The fields every sample carries, whatever its type declares.
    """

    common_fields = (
        "url",
        "html_url",
        "uuid",
        "name",
        "local_id",
        "status",
        "dataset",
        "added",
        "modified",
    )
    parents = ("dataset",)

    dataset = RecordReferenceField(queryset=Dataset.all_objects.all())

    class Meta(RecordSerializer.Meta):
        model = Sample
        fields = [
            "url",
            "html_url",
            "uuid",
            "name",
            "local_id",
            "status",
            "dataset",
            "added",
            "modified",
            *RecordSerializer.metadata_fields,
        ]


class BaseMeasurementSerializer(RecordSerializer):
    """Base DRF serializer for all Measurement subtypes.

    All auto-generated serializers for registered
    :class:`~fairdm.core.measurement.models.Measurement` subclasses inherit from this class.
    When a portal developer provides a custom ``serializer_class`` via the registry config
    it MUST subclass this class; otherwise :func:`generate_viewset` raises
    :exc:`~django.core.exceptions.ImproperlyConfigured`.

    Attributes:
        common_fields: The fields every measurement carries, whatever its type declares.
    """

    common_fields = (
        "url",
        "html_url",
        "uuid",
        "name",
        "sample",
        "dataset",
        "added",
        "modified",
    )
    parents = ("sample", "dataset")

    sample = RecordReferenceField(queryset=Sample.objects.non_polymorphic())
    dataset = RecordReferenceField(queryset=Dataset.all_objects.all())

    class Meta(RecordSerializer.Meta):
        model = Measurement
        fields = [
            "url",
            "html_url",
            "uuid",
            "name",
            "sample",
            "dataset",
            "added",
            "modified",
            *RecordSerializer.metadata_fields,
        ]


class ContributorIdentifierSerializer(serializers.Serializer):
    """An identifier of a contributor, such as an ORCID iD, and the address it resolves to."""

    type = serializers.CharField(read_only=True)
    value = serializers.CharField(read_only=True)
    link = serializers.CharField(source="resolver_url", read_only=True)


class ContributorSerializer(serializers.ModelSerializer):
    """A person or an organisation, as far as their public profile page shows.

    Nothing about the account behind a person is returned: no email address, credential, flag
    or sign-in date.
    """

    url = RecordURLField(read_only=True)
    html_url = PortalPageField()
    type = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)
    identifiers = ContributorIdentifierSerializer(many=True, read_only=True)
    links = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    affiliation = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    organization_type = serializers.SerializerMethodField()

    class Meta:
        model = Contributor
        fields = (
            "url",
            "html_url",
            "uuid",
            "type",
            "name",
            "image",
            "profile",
            "identifiers",
            "links",
            "languages",
            "affiliation",
            "location",
            "organization_type",
        )
        read_only_fields = fields

    def get_type(self, contributor) -> str:
        """Say whether the contributor is a person or an organisation."""
        return "organization" if contributor.is_organization else "person"

    def get_links(self, contributor) -> list[str]:
        """List the web links the profile page draws."""
        return [entry["url"] for entry in contributor.get_links_display()]

    def get_languages(self, contributor) -> list[str]:
        """Name the languages in the active language."""
        return [str(name) for name in contributor.get_language_names()]

    def get_affiliation(self, contributor) -> dict | None:
        """Refer to the organisation the profile names: a person's primary, an organisation's parent."""
        if isinstance(contributor, Person):
            organisation = next(
                (
                    affiliation.organization
                    for affiliation in contributor.get_affiliation_history()["current"]
                    if affiliation.is_primary
                ),
                None,
            )
        else:
            organisation = getattr(contributor, "parent", None)
        if organisation is None:
            return None
        field = RecordReferenceField(read_only=True)
        field.bind(field_name="affiliation", parent=self)
        reference: dict | None = field.to_representation(organisation)
        return reference

    def get_location(self, contributor) -> str | None:
        """Give the city and country the profile page shows."""
        return contributor.get_location_display() or None

    def get_organization_type(self, contributor) -> str | None:
        """Give an organisation's type, and nothing for a person."""
        if not contributor.is_organization or not contributor.type:
            return None
        return str(contributor.get_type_display())


class CatalogueEntrySerializer(serializers.Serializer):
    """One registered sample or measurement type, as a catalogue lists it."""

    name = serializers.CharField(read_only=True)
    verbose_name = serializers.CharField(read_only=True)
    verbose_name_plural = serializers.CharField(read_only=True)
    endpoint = serializers.URLField(read_only=True)
    count = serializers.IntegerField(read_only=True)


class CatalogueSerializer(serializers.Serializer):
    """The registered types of one kind, as a catalogue lists them."""

    types = CatalogueEntrySerializer(many=True, read_only=True)


def _validate_sample_serializer(cls: type) -> None:
    """Require a custom Sample serializer to subclass :class:`BaseSampleSerializer`.

    Args:
        cls: The custom serializer class to validate.

    Raises:
        ImproperlyConfigured: When *cls* is not a subclass of ``BaseSampleSerializer``.
    """
    if not (isinstance(cls, type) and issubclass(cls, BaseSampleSerializer)):
        raise ImproperlyConfigured(
            f"Custom serializer_class '{cls.__name__}' for a Sample type must subclass "
            f"'fairdm.api.serializers.BaseSampleSerializer'."
        )


def _validate_measurement_serializer(cls: type) -> None:
    """Require a custom Measurement serializer to subclass its base serializer.

    Args:
        cls: The custom serializer class to validate.

    Raises:
        ImproperlyConfigured: When *cls* is not a subclass of ``BaseMeasurementSerializer``.
    """
    if not (isinstance(cls, type) and issubclass(cls, BaseMeasurementSerializer)):
        raise ImproperlyConfigured(
            f"Custom serializer_class '{cls.__name__}' for a Measurement type must subclass "
            f"'fairdm.api.serializers.BaseMeasurementSerializer'."
        )


class BaseSerializerMixin:
    """Mixin that adds a ``url`` hyperlinked field to a serializer that sets its ``view_name``.

    The ``url`` field uses ``lookup_field="uuid"`` to match the viewset's lookup.
    """

    url = serializers.HyperlinkedIdentityField(
        view_name="",  # Set by the serializer that uses the mixin
        lookup_field="uuid",
        read_only=True,
    )
