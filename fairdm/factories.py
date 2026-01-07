"""
Convenience module for importing FairDM factories.

Downstream portal developers can use flat imports:
    from fairdm.factories import ProjectFactory, DatasetFactory, UserFactory

Factories are declared in their respective app packages and re-exported here
for convenient access. This module is included in FairDM distributions.

Example (Portal Developer Usage):
    # In your portal project's test file
    from fairdm.factories import ProjectFactory, UserFactory

    def test_my_portal_feature():
        # Create test data using FairDM factories
        user = UserFactory(username="testuser")
        project = ProjectFactory(owner=user, title="Test Project")

        # Test your portal-specific feature
        assert project.owner == user

    def test_with_overrides():
        # Override defaults for specific test scenarios
        private_project = ProjectFactory(
            title="Secret Research",
            visibility="private"
        )
        assert private_project.visibility == "private"

See Also:
    - docs/portal-development/testing-portal-projects.md
    - docs/contributing/testing/fixtures.md
"""

from fairdm.core.factories import (
    DatasetFactory,
    ProjectFactory,
    UserFactory,
)

__all__ = [
    "DatasetFactory",
    "ProjectFactory",
    "UserFactory",
]
