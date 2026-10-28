"""Abstract base models shared by the core records and their related rows."""

import re
from html import unescape

from controlled_vocabularies.fields import MultiConceptField
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db.models import Manager, Model, QuerySet
from django.urls import reverse
from django.utils.decorators import classonlymethod
from django.utils.functional import cached_property
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from model_utils import FieldTracker
from taggit.managers import TaggableManager

from fairdm.contrib.contributors.choices import IdentifierLookup
from fairdm.db import models
from fairdm.db.fields import PartialDateField
from fairdm.db.models import PolymorphicModel
from fairdm.models import TaggedItem
from fairdm.utils import default_image_path, get_inheritance_chain
from fairdm.utils.markdown import markdownify

from .vocabularies import ABSTRACT, ISNI, collection_members


class BaseModel(models.Model):
    """Abstract base for the core records, adding an image, name, keywords, tags and options."""

    image = ThumbnailerImageField(
        verbose_name=_("image"),
        blank=True,
        null=True,
        upload_to=default_image_path,
        resize_source={"size": (2400, 1600), "crop": False},
    )
    name = models.CharField(_("name"), max_length=300, db_index=True)

    keywords = MultiConceptField(
        verbose_name=_("keywords"),
        help_text=_("Controlled keywords for discoverability"),
        blank=True,
    )
    tags = TaggableManager(through=TaggedItem, blank=True)

    options = models.JSONField(
        verbose_name=_("options"),
        null=True,
        blank=True,
    )

    tracker = FieldTracker()

    class Meta:
        abstract = True

    def __str__(self):
        """Use the record's name."""
        return f"{self.name}"

    @property
    def icon(self):
        """Return the icon name for the model."""
        if hasattr(self, "polymorphic_model_marker"):
            return self.type_of._meta.model_name
        return self._meta.model_name

    @property
    def title(self):
        """Return the record's name as its title."""
        return self.name

    def get_non_polymorphic_instance(self):
        """Return the non-polymorphic version of this instance, or the instance itself if it is not polymorphic.

        Returns:
            The non-polymorphic instance.
        """
        from .utils import get_non_polymorphic_instance

        return get_non_polymorphic_instance(self)

    def get_absolute_url(self):
        """Return the URL of the record's detail page."""
        return reverse(f"{self._meta.model_name}-detail", kwargs={"uuid": self.uuid})

    def get_api_url(self):
        """Return the URL of the record's API detail endpoint."""
        return reverse(
            f"api:{self._meta.model_name}-detail", kwargs={"uuid": self.uuid}
        )

    def add_contributor(self, contributor, with_roles=None):
        """Credit a contributor on this object under the given roles.

        A contributor holds one credit per object, carrying every role they have on it,
        so crediting the same contributor again adds the new roles to the credit already
        recorded rather than starting a second one. This matches
        ``Contributor.add_to`` and ``Contribution.add_to``, the other two ways to record
        a credit.

        A person credited here for the first time starts at the view level, as one added from
        the Contributors tab does. An organization holds no level.

        Args:
            contributor: The contributor to credit.
            with_roles: Addresses of the contributor role concepts to add to the credit.

        Returns:
            The contributor's credit on this object.
        """
        from fairdm.contrib.contributors.models import Contribution

        return Contribution.add_to(contributor, self, with_roles)

    def is_contributor(self, user):
        """Return whether the user is credited as a contributor.

        Args:
            user: The user to look for.

        Returns:
            True when the user has a credit on this object.
        """
        return self.contributors.filter(contributor=user).exists()

    def get_direct_contributors(self):
        """Return the people and organizations directly listed as contributors.

        Returns:
            A queryset of contributors with a credit on this object.
        """
        from fairdm.contrib.contributors.models import Contributor

        return Contributor.objects.filter(contributions__object_id=self.pk).distinct()

    def get_affiliated_organizations(self):
        """Return the organizations that appear as affiliations in person contributions.

        Returns:
            A queryset of organizations.
        """
        from fairdm.contrib.contributors.models import Organization, Person

        return Organization.objects.filter(
            pk__in=self.contributors.filter(
                contributor__in=Person.objects.all()
            ).values_list("affiliation_id", flat=True)
        ).distinct()

    def get_all_contributors(self):
        """Return every direct contributor together with the organizations they are affiliated with.

        Returns:
            A queryset of contributors.
        """
        from fairdm.contrib.contributors.models import Contributor

        direct = self.contributors.values_list("contributor_id", flat=True)
        affiliated = self.contributors.exclude(affiliation__isnull=True).values_list(
            "affiliation_id", flat=True
        )

        all_ids = set(direct) | set(affiliated)
        return Contributor.objects.filter(pk__in=all_ids).distinct()

    def get_abstract(self):
        """Return the Abstract description, or ``None``.

        Returns:
            The description of the abstract type, if the record has one.
        """
        # Filtering a related manager always queries, even when prefetched. `all()` reads the
        # prefetch cache, so a list page does not cost one query per record.
        for description in self.descriptions.all():
            if description.type_id == ABSTRACT:
                return description
        return None

    def get_abstract_summary(self):
        """Return the abstract as a bounded run of plain text, or ``""``.

        ``AbstractDescription.value`` is markdown, so a template that prints it
        directly shows the reader ``##`` and ``**``. This renders it through the
        portal's sanitising renderer, drops the tags, collapses whitespace and
        caps the result at 400 characters so one long abstract cannot set the
        height of a card.

        Returns:
            Plain text, not markup. The template layer escapes it like any
            other string, so never mark it safe.
        """
        abstract = self.get_abstract()
        if not abstract or not abstract.value:
            return ""
        html = markdownify(abstract.value)
        # A heading has no terminal punctuation, so stripping tags would run it into the next paragraph.
        html = re.sub(r"</h[1-6]>", " — ", html, flags=re.IGNORECASE)
        # `strip_tags` leaves entities behind, and the summary is escaped again on output.
        text = unescape(strip_tags(html))
        return Truncator(" ".join(text.split())).chars(400, truncate="…")

    def get_meta_description(self):
        """Return the Abstract's full text for the page meta description, or ``None``.

        Unlike ``get_abstract_summary()``, the text is not truncated (#331).

        Returns:
            The abstract's value, if the record has an abstract.
        """
        abstract = self.get_abstract()
        if abstract:
            return abstract.value
        else:
            return None

    @cached_property
    def get_descriptions(self):
        """Return the record's descriptions as a list, cached on first access.

        Returns:
            The list of descriptions.
        """
        descriptions = list(self.descriptions.all())
        return descriptions

    def verbose_name(self):
        """Return the model's singular verbose name.

        Returns:
            The verbose name from the model options.
        """
        return self._meta.verbose_name

    def verbose_name_plural(self):
        """Return the model's plural verbose name.

        Returns:
            The plural verbose name from the model options.
        """
        return self._meta.verbose_name_plural


# PolymorphicModel must be listed first, or polymorphic behaviour breaks across relations and queries.
class BasePolymorphicModel(PolymorphicModel, BaseModel):  # type: ignore[misc]
    """Abstract base for the polymorphic core records (samples and measurements)."""

    @classonlymethod
    def get_inheritance_chain(cls):
        """Return the chain of classes from the concrete model up to its polymorphic base.

        Returns:
            The classes in the inheritance chain.
        """
        return get_inheritance_chain(cls, cls.type_of)

    def get_absolute_url(self):
        """Return the URL of the record's overview page."""
        type_of = self.type_of.__name__.lower()
        return reverse(f"{type_of}:overview", kwargs={"uuid": self.uuid})

    class Meta:
        abstract = True


class GenericModelQuerySet(QuerySet):
    """QuerySet for GenericModel subclasses that provides vocabulary-based ordering."""

    def in_order(self):
        """Order the rows by the order of the collection their ``type`` field offers.

        Rows whose type is not in the collection sort to the end.

        Returns:
            A list of instances in the collection's order.

        Example:
            # Get dataset descriptions in vocabulary order
            dataset.descriptions.in_order()

            # Chain with other queryset methods
            dataset.descriptions.filter(type__in=[ABSTRACT, METHODS]).in_order()
        """
        order = [concept.uri for concept in self.model.get_type_concepts()]

        def sort_key(item):
            try:
                return order.index(item.type_id)
            except ValueError:
                return len(order)

        return sorted(self, key=sort_key)


class GenericModelManager(Manager):
    """Manager for GenericModel subclasses."""

    def get_queryset(self):
        """Return a ``GenericModelQuerySet``."""
        return GenericModelQuerySet(self.model, using=self._db)

    def in_order(self):
        """Return every object in the order of the collection its ``type`` field offers.

        Returns:
            A list of instances in the collection's order.
        """
        return self.get_queryset().in_order()


class GenericModel(Model):
    """Abstract base for the typed rows attached to a record, such as descriptions and dates.

    Each concrete subclass declares ``type`` as a ``ConceptField`` restricted to the
    collection of the vocabulary that its kind of record uses.
    """

    modified = None
    added = None

    objects = GenericModelManager()

    class Meta:
        abstract = True

    @classmethod
    def get_type_concepts(cls):
        """Return the concepts the ``type`` field offers, in its collection's order.

        Returns:
            A list of ``controlled_vocabularies.Record`` concepts.
        """
        return collection_members(cls._meta.get_field("type").collection)

    def __str__(self):
        """Show the type and value."""
        return f"{self.type}: {self.value}"

    def __repr__(self):
        """Wrap the string form in angle brackets."""
        return f"<{self}>"

    def get_update_url(self):
        """Return the URL of the page that edits this row."""
        return reverse(
            f"{self._meta.model_name}-update",
            kwargs={"uuid": self.uuid, "object_id": self.object_id},
        )

    def verbose_name(self):
        """Return the model's singular verbose name.

        Returns:
            The verbose name from the model options.
        """
        return self._meta.verbose_name

    def verbose_name_plural(self):
        """Return the model's plural verbose name.

        Returns:
            The plural verbose name from the model options.
        """
        return self._meta.verbose_name_plural


# Roughly 3,000 words: several times any real abstract, but stops a pasted thesis chapter (#329).
DESCRIPTION_MAX_LENGTH = 20000


class AbstractDescription(GenericModel):
    """Abstract base for a typed free-text description of a record."""

    value = models.TextField(validators=[MaxLengthValidator(DESCRIPTION_MAX_LENGTH)])

    class Meta:
        abstract = True
        verbose_name = _("description")
        verbose_name_plural = _("descriptions")
        default_related_name = "descriptions"
        constraints = [
            models.UniqueConstraint(
                fields=["related", "type"],
                name="%(class)s_unique_type",
            ),
        ]


class AbstractDate(GenericModel):
    """Abstract base for a typed partial date on a record."""

    value = PartialDateField(_("date"))

    class Meta:
        abstract = True
        verbose_name = _("date")
        verbose_name_plural = _("dates")
        ordering = ["value"]
        default_related_name = "dates"
        constraints = [
            models.UniqueConstraint(
                fields=["related", "type"],
                name="%(class)s_unique_type",
            ),
        ]


class AbstractIdentifier(GenericModel):
    """An external identifier attached to a record.

    ``value`` carries ``unique=True``, which is a per-table constraint: since this model is
    abstract, each concrete subclass (dataset, project, sample, measurement) gets its own
    index, so the same value could otherwise name two different kinds of record at once.
    ``clean()`` closes that gap by checking the value against every concrete subclass, not
    only the one being validated.
    """

    value = models.CharField(
        _("identifier"), max_length=255, db_index=True, unique=True
    )

    class Meta:
        abstract = True
        verbose_name = _("identifier")
        verbose_name_plural = _("identifiers")
        default_related_name = "identifiers"
        constraints = [
            models.UniqueConstraint(
                fields=["related", "type"],
                name="%(class)s_unique_type",
            ),
        ]
        verbose_name_plural = _("identifiers")
        default_related_name = "identifiers"

    def clean(self):
        """Reject an identifier value already used by any identifier model."""
        super().clean()
        if not self.value:
            return
        for model in AbstractIdentifier.__subclasses__():
            queryset = model.objects.filter(value=self.value)
            if model is type(self) and self.pk:
                queryset = queryset.exclude(pk=self.pk)
            if queryset.exists():
                raise ValidationError(
                    {
                        "value": _("The identifier '%(value)s' is already in use.")
                        % {"value": self.value}
                    }
                )

    def get_root_url(self):
        """Return the base URL of the identifier's resolver.

        Returns:
            The resolver URL registered for the identifier's type, or None when it has none.
        """
        return IdentifierLookup.get(self.type_id)

    def get_absolute_url(self):
        """Return the URL of the identifier's resolver page.

        Returns:
            The address the identifier resolves to, or None for a type with no resolver.
        """
        root = self.get_root_url()
        if root is None:
            return None
        # An ISNI is written in groups of four, and its resolver takes it without the spaces.
        value = self.value.replace(" ", "") if self.type_id == ISNI else self.value
        return f"{root}{value}"
