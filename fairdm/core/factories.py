"""
Factory-boy factories for fairdm.core models.

Factories are declared here (near models) and re-exported via fairdm/factories.py
for convenient downstream imports. Portal developers can import factories using:

    from fairdm.factories import UserFactory, ProjectFactory, DatasetFactory

This module provides factories for core FairDM models, following these principles:
1. Sensible defaults for all required fields
2. Unique values using factory.Sequence
3. Relationships using factory.SubFactory
4. Comprehensive docstrings with usage examples
5. Fully-featured covering all model fields

Usage:
    from fairdm.factories import UserFactory, ProjectFactory

    # Create with defaults
    project = ProjectFactory()

    # Override specific fields at runtime
    project = ProjectFactory(title="Custom Title", visibility="private")

    # Build without saving to database (for unit tests)
    project = ProjectFactory.build()

    # Create batch
    projects = ProjectFactory.create_batch(5)

See Also:
    - docs/contributing/testing/fixtures.md
    - docs/developer-guide/testing-portal-projects.md
    - docs/contributing/testing/examples/fixture-factory-example.md
"""

import factory
from django.contrib.auth import get_user_model

from fairdm.core.models import Dataset, Project

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating User instances.

    Default behavior:
    - Generates unique usernames (user0, user1, ...)
    - Generates email from username
    - Sets default first/last name
    - Sets usable password

    Usage:
        # Create with defaults
        user = UserFactory()

        # Override specific fields
        user = UserFactory(username="alice", email="alice@example.com")

        # Build without saving to database (for unit tests)
        user = UserFactory.build()

        # Create multiple users
        users = UserFactory.create_batch(5)

    Portal Developer Examples:
        >>> # In your portal project tests
        >>> from fairdm.factories import UserFactory
        >>> user = UserFactory()
        >>> print(user.username)
        user0
        >>> print(user.email)
        user0@example.com
        >>> assert user.check_password("password123")

        >>> # Override for portal-specific needs
        >>> admin_user = UserFactory(username="admin", is_staff=True, is_superuser=True)
    """

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
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


class ProjectFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Project instances.

    Default behavior:
    - Creates a unique owner (UserFactory)
    - Generates unique title and slug
    - Sets default description
    - Sets visibility to PUBLIC

    Usage:
        # Create with defaults (automatically creates owner)
        project = ProjectFactory()

        # Use existing user
        user = UserFactory()
        project = ProjectFactory(owner=user)

        # Override fields
        project = ProjectFactory(
            title="Custom Project",
            visibility=Project.Visibility.PRIVATE
        )

        # Build without saving
        project = ProjectFactory.build()

    Portal Developer Examples:
        >>> # In your portal project tests
        >>> from fairdm.factories import ProjectFactory, UserFactory
        >>> project = ProjectFactory()
        >>> print(project.title)
        'Project 0'
        >>> print(project.owner.username)
        'user0'
        >>> assert project.pk is not None
        >>> assert project.visibility == Project.Visibility.PUBLIC

        >>> # Customize for portal-specific tests
        >>> my_user = UserFactory(username="researcher")
        >>> my_project = ProjectFactory(
        ...     owner=my_user, title="Portal Research Project", visibility="private"
        ... )
    """

    class Meta:
        model = Project

    owner = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Project {n}")
    slug = factory.Sequence(lambda n: f"project-{n}")
    description = factory.LazyAttribute(lambda obj: f"Description for {obj.title}")
    visibility = "public"  # Default visibility


class DatasetFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Dataset instances.

    Default behavior:
    - Creates parent Project (with owner)
    - Generates unique title

    Usage:
        # Create with defaults (creates project and owner)
        dataset = DatasetFactory()

        # Use existing project
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)

        # Create multiple datasets for one project
        project = ProjectFactory()
        datasets = DatasetFactory.create_batch(3, project=project)

    Portal Developer Examples:
        >>> # In your portal project tests
        >>> from fairdm.factories import DatasetFactory, ProjectFactory
        >>> dataset = DatasetFactory()
        >>> print(dataset.title)
        'Dataset 0'
        >>> assert dataset.project is not None
        >>> assert dataset.project.owner is not None

        >>> # Create multiple datasets for testing
        >>> project = ProjectFactory(title="My Research")
        >>> datasets = DatasetFactory.create_batch(
        ...     3, project=project, title=factory.Sequence(lambda n: f"Experiment {n}")
        ... )
        >>> assert len(datasets) == 3
        >>> assert all(d.project == project for d in datasets)
    """

    class Meta:
        model = Dataset

    project = factory.SubFactory(ProjectFactory)
    title = factory.Sequence(lambda n: f"Dataset {n}")
