import factory
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from factory.declarations import LazyAttribute, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker

from fairdm.contrib.contributors.models import (
    Contribution,
    Organization,
    OrganizationMember,
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
    """Factory for creating Contributor instances (creates Person as default)."""

    class Meta:
        model = Person  # Use Person as the concrete implementation

    image = factory.django.ImageField(width=400, height=400, color="blue")
    name = Faker("name")
    profile = Faker("text", max_nb_chars=300)
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    email = LazyAttribute(lambda o: f"{o.first_name}.{o.last_name}@fakeuser.org")


class PersonFactory(DjangoModelFactory):
    """Factory for creating Person instances."""

    class Meta:
        model = Person
        django_get_or_create = ["email"]

    image = factory.django.ImageField(width=400, height=400, color="blue")
    profile = Faker("text", max_nb_chars=300)
    name = LazyAttribute(lambda o: f"{o.first_name} {o.last_name}")
    email = LazyAttribute(lambda o: f"{o.first_name}.{o.last_name}@fakeuser.org")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    is_active = Faker("boolean", chance_of_getting_true=80)


class OrganizationFactory(DjangoModelFactory):
    """Factory for creating Organization instances."""

    class Meta:
        model = Organization

    image = factory.django.ImageField(width=400, height=400, color="blue")
    profile = Faker("text", max_nb_chars=300)
    name = Faker("company")


class OrganizationMembershipFactory(DjangoModelFactory):
    """Factory for creating OrganizationMember instances."""

    class Meta:
        model = OrganizationMember

    person = SubFactory(PersonFactory)
    organization = SubFactory(OrganizationFactory)


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
