import factory
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from factory.declarations import LazyAttribute, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker

from fairdm.contrib.contributors.models import (
    Affiliation,
    Contribution,
    Contributor,
    ContributorIdentifier,
    Organization,
    Person,
)

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating Django User instances.

    Note: Person model uses email as USERNAME_FIELD, not username.
    The username field is set to __str__ property in Person model.
    """

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = "Test"
    last_name = "User"
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after user creation."""
        if not create:
            return
        password = extracted if extracted else "password123"
        obj.set_password(password)
        obj.save()


class ContributorFactory(DjangoModelFactory):
    """Factory for the fields common to every concrete contributor type.

    PersonFactory and OrganizationFactory build on this rather than duplicating
    these declarations; the preferred name is a sequence, not a random Faker
    value, so that ordering by name is stable across a test run.
    """

    class Meta:
        model = Contributor

    image = factory.django.ImageField(width=400, height=400, color="blue")
    name = factory.Sequence(lambda n: f"Contributor {n}")
    profile = Faker("text", max_nb_chars=300)


class PersonFactory(ContributorFactory):
    """Factory for creating Person instances.

    Defaults to an unclaimed instance with an unusable password - a contributor
    added for attribution alone is the common case (Article X, issue #227). Pass
    `password=...` for a claimed-looking instance, or set `is_claimed`/`is_active`
    explicitly.
    """

    class Meta:
        model = Person
        django_get_or_create = ["email"]

    email = LazyAttribute(lambda o: f"{o.first_name}.{o.last_name}@fakeuser.org")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set the given password, or leave the instance with an unusable one."""
        if not create:
            return
        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_unusable_password()
        obj.save()


class OrganizationFactory(ContributorFactory):
    """Factory for creating Organization instances."""

    class Meta:
        model = Organization


class ContributorIdentifierFactory(DjangoModelFactory):
    """Factory for creating ContributorIdentifier instances.

    ``AbstractIdentifier.value`` carries a database-level uniqueness constraint across
    every identifier-bearing record, not just other ContributorIdentifiers, so it is a
    sequence rather than a fixed or random value (Article X).
    """

    class Meta:
        model = ContributorIdentifier

    type = "ORCID"  # Default identifier type - a member of the contributor identifier collection
    value = factory.Sequence(lambda n: f"0000-0001-{n:04d}-{n:04d}")
    # related field has no default - pass e.g. ContributorIdentifierFactory(related=person)


class AffiliationFactory(DjangoModelFactory):
    """Factory for creating Affiliation instances.

    Defaults to a current, plain member membership: a start date is set and
    no end date, and the type is the plain member level rather than pending,
    admin or owner.
    """

    class Meta:
        model = Affiliation

    person = SubFactory(PersonFactory)
    organization = SubFactory(OrganizationFactory)
    type = Affiliation.MembershipType.MEMBER
    start_date = "2020"


class ContributionFactory(DjangoModelFactory):
    """Factory for creating Contribution instances.

    The content_object can optionally be provided when creating a Contribution.
    If not provided, a default Project will be created.

    Example:
        contribution = ContributionFactory()  # Creates with default Project
        contribution = ContributionFactory(content_object=my_dataset)  # Custom object
    """

    class Meta:
        model = Contribution
        exclude = ["content_object"]

    contributor = SubFactory(PersonFactory)

    # Create a default Project if content_object is not provided
    @factory.lazy_attribute
    def content_object(self):
        from fairdm.factories import ProjectFactory

        return ProjectFactory()

    # These will be set based on content_object
    @factory.lazy_attribute
    def content_type(self):
        if self.content_object:
            return ContentType.objects.get_for_model(self.content_object)
        return None

    @factory.lazy_attribute
    def object_id(self):
        if self.content_object:
            return self.content_object.id
        return None
