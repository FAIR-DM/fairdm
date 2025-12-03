from django.db.models import Manager, QuerySet
from django.urls import reverse
from django.utils.decorators import classonlymethod

# from rest_framework.authtoken.models import Token
from django.utils.functional import cached_property, classproperty
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from model_utils import FieldTracker
from research_vocabs.models import Concept
from taggit.managers import TaggableManager

from fairdm.contrib.contributors.choices import IdentifierLookup
from fairdm.contrib.generic.models import TaggedItem
from fairdm.db import models
from fairdm.db.fields import PartialDateField
from fairdm.db.models import PolymorphicModel
from fairdm.registry import registry
from fairdm.utils import default_image_path, get_inheritance_chain


class BaseModel(models.Model):
    image = ThumbnailerImageField(
        verbose_name=_("image"),
        blank=True,
        null=True,
        upload_to=default_image_path,
    )
    name = models.CharField(_("name"), max_length=255)

    keywords = models.ManyToManyField(
        "research_vocabs.Concept",
        verbose_name=_("keywords"),
        help_text=_("Controlled keywords for enhanced discoverability"),
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
        return f"{self.name}"

    @property
    def icon(self):
        """Returns the icon for the model."""
        if hasattr(self, "polymorphic_model_marker"):
            return self.type_of._meta.model_name
        return self._meta.model_name

    @property
    def title(self):
        return self.name

    def get_non_polymorphic_instance(self):
        """Returns the non-polymorphic version of a given instance. If the model is not polymorphic, simple returns the
        instance."""
        from .utils import get_non_polymorphic_instance

        return get_non_polymorphic_instance(self)

    def get_absolute_url(self):
        return reverse(f"{self._meta.model_name}:overview", kwargs={"uuid": self.uuid})

    def get_api_url(self):
        return reverse(f"api:{self._meta.model_name}-detail", kwargs={"uuid": self.uuid})

    def add_contributor(self, contributor, with_roles=None):
        """Adds a new contributor the object with the specified roles."""

        contribution = self.contributors.create(contributor=contributor)
        roles_qs = Concept.objects.filter(vocabulary__name="fairdm-roles")
        if with_roles:
            contribution.roles.set(roles_qs.filter(name__in=with_roles))
        return contribution

    def is_contributor(self, user):
        """Returns true if the user is a contributor."""

        return self.contributors.filter(contributor=user).exists()

    def get_direct_contributors(self):
        """Get all people and organizations who are directly listed as contributors."""
        from fairdm.contrib.contributors.models import Contributor

        return Contributor.objects.filter(contributions__object_id=self.pk).distinct()

    def get_affiliated_organizations(self):
        """Get all organizations that appear as affiliations in person contributions."""
        from fairdm.contrib.contributors.models import Organization, Person

        return Organization.objects.filter(
            pk__in=self.contributors.filter(contributor__in=Person.objects.all()).values_list(
                "affiliation_id", flat=True
            )
        ).distinct()

    def get_all_contributors(self):
        """Get combined queryset of all direct contributors and affiliated organizations."""
        from fairdm.contrib.contributors.models import Contributor

        direct = self.contributors.values_list("contributor_id", flat=True)
        affiliated = self.contributors.exclude(affiliation__isnull=True).values_list("affiliation_id", flat=True)

        all_ids = set(direct) | set(affiliated)
        return Contributor.objects.filter(pk__in=all_ids).distinct()

    def get_abstract(self):
        """Returns the abstract description of the project."""
        try:
            return self.descriptions.filter(type="Abstract").first()
        except self.DoesNotExist:
            return None

    def get_meta_description(self):
        abstract = self.get_abstract()
        if abstract:
            return abstract.description
        else:
            return None

    @cached_property
    def get_descriptions(self):
        descriptions = list(self.descriptions.all())
        # descriptions.sort(key=lambda x: self.DESCRIPTION_TYPES.values.index(x.type))
        return descriptions

    def verbose_name(self):
        return self._meta.verbose_name

    def verbose_name_plural(self):
        return self._meta.verbose_name_plural


# WARNING: PolymorphicModel must always be listed first in the inheritance list to ensure
# proper polymorphic behavior across relations and queries.
# SEE: https://github.com/jazzband/django-polymorphic/issues/437#issuecomment-677638021
class BasePolymorphicModel(PolymorphicModel, BaseModel):
    @classonlymethod
    def get_inheritance_chain(cls):
        return get_inheritance_chain(cls, cls.type_of)

    def get_absolute_url(self):
        type_of = self.type_of.__name__.lower()
        return reverse(f"{type_of}:overview", kwargs={"uuid": self.uuid})

    def get_collection_url(self):
        """Returns the URL to the collection of this model."""
        slug = self._meta.model_name.lower()
        return reverse(f"{slug}-collection")

    @classproperty
    def config(cls):
        """Gets the FairDM configuration object for a class or instance from the registry."""
        if registry_item := registry.get_for_model(cls):
            return registry_item

    class Meta:
        abstract = True


class GenericModelQuerySet(QuerySet):
    """Custom QuerySet for GenericModel subclasses that provides vocabulary-based ordering."""

    def in_order(self):
        """
        Orders the queryset by the order defined in the model's VOCABULARY attribute.

        Returns:
            List of instances ordered according to VOCABULARY.values

        Example:
            # Get dataset descriptions in vocabulary order
            dataset.descriptions.in_order()

            # Chain with other queryset methods
            dataset.descriptions.filter(type__in=['Abstract', 'Methods']).in_order()
        """
        model = self.model
        if model.VOCABULARY is None:
            msg = f"{model.__name__} does not define a VOCABULARY attribute"
            raise ValueError(msg)

        # Get the ordering from the vocabulary
        vocabulary_order = model.VOCABULARY.values

        # Convert queryset to list and sort by vocabulary order
        # Items not in vocabulary_order go to the end
        items = list(self)

        def sort_key(item):
            try:
                return vocabulary_order.index(item.type)  # type: ignore[attr-defined]
            except ValueError:
                # If type not in vocabulary, sort to end
                return len(vocabulary_order)

        return sorted(items, key=sort_key)


class GenericModelManager(Manager):
    """Custom Manager for GenericModel subclasses."""

    def get_queryset(self):
        return GenericModelQuerySet(self.model, using=self._db)

    def in_order(self):
        """Shortcut to get all objects in vocabulary order."""
        return self.get_queryset().in_order()


class GenericModel(models.Model):
    """A model that can be used to store generic information."""

    VOCABULARY = None
    modified = None
    added = None
    # FOR = None

    objects = GenericModelManager()

    class Meta:
        abstract = True

    # def __new__(cls, *args, **kwargs):
    #     new_class = super().__new__(cls, *args, **kwargs)

    #     if new_class.VOCABULARY is not None:
    #         new_class.type.field.choices = cls.VOCABULARY.choices

    #     if new_class.FOR is not None:
    #         new_class.related = models.ForeignKey(cls.FOR, on_delete=models.CASCADE)

    #         # if not hasattr(cls._meta, "db_table") or cls._meta.db_table is None:
    #         new_class._meta.db_table = f"{cls.FOR._meta.db_table}_{cls.__name__.lower()}"

    #     return new_class

    def __init_subclass__(cls):
        if cls.VOCABULARY is not None:
            cls.type.field.choices = cls.VOCABULARY.choices  # type: ignore[attr-defined]

        # if cls.FOR is not None:
        #     # if not hasattr(cls._meta, "db_table") or cls._meta.db_table is None:
        #     cls._meta.db_table = f"{cls.FOR._meta.db_table}_{cls.__name__.lower()}"

        return super().__init_subclass__()

    def __str__(self):
        return f"{self.type}: {self.value}"  # Display the type and a preview of the text  # type: ignore[attr-defined]

    def __repr__(self):
        return f"<{self}>"

    def get_update_url(self):
        return reverse(
            f"{self._meta.model_name}-update",
            kwargs={"uuid": self.uuid, "object_id": self.object_id},  # type: ignore[attr-defined]
        )

    def verbose_name(self):
        return self._meta.verbose_name

    def verbose_name_plural(self):
        return self._meta.verbose_name_plural


class AbstractDescription(GenericModel):
    type = models.CharField(max_length=50)
    value = models.TextField()

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
    type = models.CharField(max_length=50)
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
    type = models.CharField(max_length=50)
    value = models.CharField(_("identifier"), max_length=255, db_index=True, unique=True)

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

    def get_root_url(self):
        return IdentifierLookup.get(self.type)

    def get_absolute_url(self):
        value = func() if (func := getattr(self, f"slugify_{self.type.lower()}", None)) else self.value
        return f"{self.get_root_url()}{value}"

    def slugify_isni(self):
        return self.value.replace(" ", "")
