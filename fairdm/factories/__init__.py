"""FairDM Test Factories.

This package provides factory_boy factories for creating test instances of FairDM models.
All factories follow an **opt-in pattern** for related metadata objects.

Quick Start
-----------

Import factories from this module::

    from fairdm.factories import ProjectFactory, DatasetFactory, SampleFactory

Create instances with minimal fields::

    project = ProjectFactory()  # No descriptions/dates
    dataset = DatasetFactory(project=project)

Opt-in to metadata creation::

    project = ProjectFactory(
        descriptions=2,  # Create 2 descriptions
        dates=1,  # Create 1 date
    )

Specify custom types (validated against model VOCABULARY)::

    project = ProjectFactory(
        descriptions=3, descriptions__types=["Abstract", "Introduction", "Objectives"]
    )

Available Factories
-------------------

Core Models:
    - ProjectFactory - Create Project instances
    - DatasetFactory - Create Dataset instances
    - SampleFactory - Abstract. Subclass it to build a concrete specimen type, e.g.
      ``fairdm_demo.factories.RockSampleFactory``.
    - MeasurementFactory - Abstract. Subclass it to build a concrete measurement type, e.g.
      ``fairdm_demo.factories.ExampleMeasurementFactory``. ``sample`` has no default; pass a
      concrete specimen instance.

Contributors:
    - UserFactory - Create User instances
    - PersonFactory - Create Person contributor instances
    - OrganizationFactory - Create Organization contributor instances
    - ContributorFactory - Generic contributor factory
    - ContributorIdentifierFactory - Create contributor identifiers (ORCID, ROR, ...)

Relations:
    - SampleIdentifierFactory - Create sample identifiers
    - SampleRelationFactory - Create sample-to-sample relationships
    - MeasurementDescriptionFactory - Create measurement descriptions
    - MeasurementDateFactory - Create measurement dates
    - MeasurementIdentifierFactory - Create measurement identifiers

All core model factories support opt-in metadata via:
    - descriptions=<int>, descriptions__types=[...]
    - dates=<int>, dates__types=[...]

Documentation
-------------

Portal Developers:
    See docs/portal-development/testing-portal-projects.md

Framework Contributors:
    See docs/contributing/testing/

API Reference:
    See fairdm.factories.core module docstring
"""

from .contributors import (
    AffiliationFactory,
    ContributionFactory,
    ContributorFactory,
    ContributorIdentifierFactory,
    OrganizationFactory,
    PersonFactory,
    UserFactory,
)
from .core import (
    DatasetDateFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    DatasetLiteratureRelationFactory,
    LiteratureItemFactory,
    MeasurementDateFactory,
    MeasurementDescriptionFactory,
    MeasurementFactory,
    MeasurementIdentifierFactory,
    PointFactory,
    ProjectDateFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    SampleDateFactory,
    SampleDescriptionFactory,
    SampleFactory,
    SampleIdentifierFactory,
    SampleRelationFactory,
)

__all__ = [
    "AffiliationFactory",
    "ContributionFactory",
    "ContributorFactory",
    "ContributorIdentifierFactory",
    "DatasetDateFactory",
    "DatasetDescriptionFactory",
    "DatasetFactory",
    "DatasetIdentifierFactory",
    "DatasetLiteratureRelationFactory",
    "LiteratureItemFactory",
    "MeasurementDateFactory",
    "MeasurementDescriptionFactory",
    "MeasurementFactory",
    "MeasurementIdentifierFactory",
    "OrganizationFactory",
    "PersonFactory",
    "PointFactory",
    "ProjectDateFactory",
    "ProjectDescriptionFactory",
    "ProjectFactory",
    "ProjectIdentifierFactory",
    "SampleDateFactory",
    "SampleDescriptionFactory",
    "SampleFactory",
    "SampleIdentifierFactory",
    "SampleRelationFactory",
    "UserFactory",
]
