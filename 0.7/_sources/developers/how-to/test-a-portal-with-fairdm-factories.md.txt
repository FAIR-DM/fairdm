# How to test a portal with FairDM factories

FairDM ships factories for its core records, so a portal's tests do not build projects, datasets and people by hand. You use them to set up exactly the records a test needs, and nothing else.

## Before you start

- Your portal has pytest and pytest-django set up, and its tests run with `uv run pytest`.
- The factories ship with FairDM, so a portal that depends on FairDM already has them. Import them from `fairdm.factories`.

## Steps

1. Create a record with the defaults. A factory fills in every required field and creates the parents the record needs.

   ```python
   import pytest

   from fairdm.factories import DatasetFactory, ProjectFactory


   @pytest.mark.django_db
   def test_a_dataset_belongs_to_a_project():
       project = ProjectFactory()
       dataset = DatasetFactory(project=project)

       assert dataset.project == project
       assert project.owner is not None
       assert project.descriptions.count() == 0
   ```

   The project has no descriptions or dates, because a factory creates metadata only when you ask.

2. Override the fields your test cares about. Pass any field of the model as a keyword argument. A project's owner is an organization.

   ```python
   from fairdm.factories import OrganizationFactory, ProjectFactory
   from fairdm.utils.choices import Visibility


   @pytest.mark.django_db
   def test_a_project_with_chosen_fields():
       institute = OrganizationFactory(name="Research Institute")
       project = ProjectFactory(
           name="Funded project", owner=institute, visibility=Visibility.PUBLIC
       )

       assert project.owner.name == "Research Institute"
   ```

3. Ask for metadata when the test needs it. `descriptions` and `dates` take the number to create, and `descriptions__types` and `dates__types` choose their types.

   ```python
   @pytest.mark.django_db
   def test_a_project_with_metadata():
       project = ProjectFactory(
           descriptions=2,
           descriptions__types=["Abstract", "Objectives"],
           dates=1,
       )

       assert project.descriptions.count() == 2
       assert project.dates.count() == 1
   ```

   A type that is not in the record's vocabulary raises `ValueError`, and the message lists the valid ones. They are in the [factories reference](../reference/factories.md).

4. Create several records at once with `create_batch`.

   ```python
   private_projects = ProjectFactory.create_batch(3, visibility=Visibility.PRIVATE)
   ```

5. Create samples and measurements with the factory for your own type. `SampleFactory` and `MeasurementFactory` are abstract, because the base `Sample` and `Measurement` cannot be created. See [How to add a factory for a portal model](add-a-factory-for-a-portal-model.md).

6. Give a person a level on a record, and test what they can do. A person who signs in needs `is_active=True` and `is_claimed=True`. `ContributionFactory` credits them on any record.

   ```python
   from django.urls import reverse
   from rest_framework.test import APIClient

   from fairdm.contrib.contributors.choices import ContributionLevel
   from fairdm.factories import ContributionFactory, DatasetFactory, PersonFactory


   @pytest.mark.django_db
   def test_a_private_dataset_is_open_only_to_its_team():
       dataset = DatasetFactory()
       person = PersonFactory(is_active=True, is_claimed=True)
       ContributionFactory(
           content_object=dataset, contributor=person, level=ContributionLevel.VIEW
       )
       address = reverse("api:dataset-detail", kwargs={"uuid": dataset.uuid})

       assert APIClient().get(address).status_code == 404

       client = APIClient()
       client.force_authenticate(person)
       assert client.get(address).status_code == 200
   ```

7. Put set-ups you repeat into a fixture.

   ```python
   # conftest.py
   import pytest

   from fairdm.factories import DatasetFactory, ProjectFactory


   @pytest.fixture
   def project_with_datasets():
       project = ProjectFactory()
       DatasetFactory.create_batch(3, project=project)
       return project
   ```

   ```python
   @pytest.mark.django_db
   def test_the_project_has_its_datasets(project_with_datasets):
       assert project_with_datasets.datasets.count() == 3
   ```

8. Run the tests.

   ```bash
   uv run pytest
   ```

## The result

Each test builds only the records it names. The tests pass without hand-written setup, and a change to a FairDM model's required fields reaches them through the factory, not through every test.

Override at the call, as above, and avoid a subclass for each scenario. A factory is for tests. Do not call one in a view or any other portal code.

Why metadata is opt-in is explained in [Why factories create metadata only when asked](../explanation/why-factories-create-metadata-only-when-asked.md). Every factory and its arguments are in the [factories reference](../reference/factories.md).
