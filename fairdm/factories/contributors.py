import factory
from django.contrib.contenttypes.models import ContentType
from factory.declarations import LazyAttribute, SelfAttribute, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker

from fairdm.contrib.contributors.models import (
    Contribution,
    Organization,
    OrganizationMember,
    Person,
)


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
    """Factory for creating Contribution instances."""

    class Meta:
        model = Contribution

    contributor = SubFactory(PersonFactory)

    content_object = LazyAttribute(lambda obj: _create_project_for_contribution())
    content_type = LazyAttribute(lambda o: ContentType.objects.get_for_model(o.content_object))
    object_id = SelfAttribute("content_object.id")


def _create_project_for_contribution():
    """Helper function to create a Project for contributions, avoiding circular imports."""
    from fairdm.factories.core import ProjectFactory

    return ProjectFactory()
