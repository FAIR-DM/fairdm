"""Tests for GenericModel and its QuerySet ordering functionality (fairdm/core/abstract.py)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import connection

from fairdm.core.abstract import DESCRIPTION_MAX_LENGTH
from fairdm.core.dataset.models import DatasetDescription
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import ProjectDate
from fairdm.core.sample.models import Sample
from fairdm.core.vocabularies import (
    CONTRIBUTOR_ROLES,
    DATE_TYPES,
    DESCRIPTION_TYPES,
    IDENTIFIER_TYPES,
)
from fairdm.factories import PersonFactory
from fairdm.factories.contributors import ContributorIdentifierFactory
from fairdm.factories.core import (
    DatasetDescriptionFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
)


@pytest.mark.django_db
class TestGenericModelQuerySet:
    def test_description_queryset_in_order(self):
        dataset = DatasetFactory.create()

        DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="This is the abstract",
        )
        DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/other",
            value="Some other info",
        )
        DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/methods",
            value="The methods used",
        )
        DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/technical-info",
            value="Technical details",
        )

        ordered = dataset.descriptions.in_order()

        expected_types = [
            f"{DESCRIPTION_TYPES}/abstract",
            f"{DESCRIPTION_TYPES}/methods",
            f"{DESCRIPTION_TYPES}/technical-info",
            f"{DESCRIPTION_TYPES}/other",
        ]
        actual_types = [d.type_id for d in ordered]

        assert actual_types == expected_types

    def test_manager_in_order(self):
        dataset1 = DatasetFactory.create()
        dataset2 = DatasetFactory.create()

        DatasetDescriptionFactory.create(
            related=dataset1, type_id=f"{DESCRIPTION_TYPES}/other", value="Other 1"
        )
        DatasetDescriptionFactory.create(
            related=dataset1,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="Abstract 1",
        )
        DatasetDescriptionFactory.create(
            related=dataset2, type_id=f"{DESCRIPTION_TYPES}/methods", value="Methods 1"
        )

        ordered = DatasetDescription.objects.in_order()

        assert [d.type_id for d in ordered] == [
            f"{DESCRIPTION_TYPES}/abstract",
            f"{DESCRIPTION_TYPES}/methods",
            f"{DESCRIPTION_TYPES}/other",
        ]


@pytest.mark.django_db
class TestAddContributor:
    def test_second_credit_adds_its_role_to_the_first(self):
        dataset = DatasetFactory.create()
        person = PersonFactory()

        first = dataset.add_contributor(
            person, with_roles=[f"{CONTRIBUTOR_ROLES}/data-collector"]
        )
        second = dataset.add_contributor(
            person, with_roles=[f"{CONTRIBUTOR_ROLES}/researcher"]
        )

        assert second.pk == first.pk
        assert {role.uri for role in second.roles.all()} == {
            f"{CONTRIBUTOR_ROLES}/data-collector",
            f"{CONTRIBUTOR_ROLES}/researcher",
        }
        assert dataset.contributors.filter(contributor=person).count() == 1

    def test_a_repeated_role_is_not_recorded_twice(self):
        dataset = DatasetFactory.create()
        person = PersonFactory()

        dataset.add_contributor(
            person, with_roles=[f"{CONTRIBUTOR_ROLES}/data-collector"]
        )
        contribution = dataset.add_contributor(
            person, with_roles=[f"{CONTRIBUTOR_ROLES}/data-collector"]
        )

        assert [role.uri for role in contribution.roles.all()] == [
            f"{CONTRIBUTOR_ROLES}/data-collector"
        ]

    def test_crediting_without_roles_leaves_existing_roles_alone(self):
        dataset = DatasetFactory.create()
        person = PersonFactory()

        dataset.add_contributor(
            person, with_roles=[f"{CONTRIBUTOR_ROLES}/data-collector"]
        )
        contribution = dataset.add_contributor(person)

        assert {role.uri for role in contribution.roles.all()} == {
            f"{CONTRIBUTOR_ROLES}/data-collector"
        }


@pytest.mark.django_db
class TestAbstractSummary:
    """The summary and meta description come from any record's abstract."""

    @staticmethod
    def abstract_of(value):
        dataset = DatasetFactory()
        DatasetDescriptionFactory(
            related=dataset, type_id=f"{DESCRIPTION_TYPES}/abstract", value=value
        )
        return dataset

    def test_the_summary_is_empty_when_the_record_has_no_abstract(self):
        assert DatasetFactory().get_abstract_summary() == ""

    def test_the_summary_is_empty_when_the_only_description_is_another_type(self):
        dataset = DatasetFactory()
        DatasetDescriptionFactory(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/methods",
            value="Not the abstract.",
        )

        assert dataset.get_abstract_summary() == ""

    def test_the_summary_is_plain_text_on_one_line(self):
        dataset = self.abstract_of(
            "## Background\n\nRock & **roll** geochemistry, see [the paper](https://example.org):\n\n"
            "- one\n- two <script>alert(1)</script>"
        )

        summary = dataset.get_abstract_summary()

        assert (
            summary == "Background — Rock & roll geochemistry, see the paper: one two"
        )

    def test_a_long_summary_is_capped_at_400_characters_and_ends_with_an_ellipsis(self):
        summary = self.abstract_of("word " * 300).get_abstract_summary()

        assert len(summary) <= 400
        assert summary.endswith("…")

    def test_a_short_summary_is_returned_whole(self):
        assert self.abstract_of("A short abstract.").get_abstract_summary() == (
            "A short abstract."
        )

    def test_the_meta_description_is_the_abstracts_full_text(self):
        text = "word " * 300

        assert self.abstract_of(text).get_meta_description() == text

    def test_the_meta_description_is_none_without_an_abstract(self):
        assert DatasetFactory().get_meta_description() is None


@pytest.mark.django_db
class TestNameIndex:
    # Asserted on Sample/Measurement's own table: a polymorphic child such as
    # RockSample does not hold `name` in its own table.
    def _has_index_on_name(self, table_name: str) -> bool:
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, table_name)
        return any(
            details["columns"] == ["name"] and (details["index"] or details["unique"])
            for details in constraints.values()
        )

    def test_every_registered_types_default_search_field_is_indexed(self):
        from fairdm.registry import registry

        for model_class in [*registry.samples, *registry.measurements]:
            config = registry.get_for_model(model_class)
            if config.search_fields:
                continue
            assert config.get_search_fields() == ["name"]

        assert self._has_index_on_name(Sample._meta.db_table)
        assert self._has_index_on_name(Measurement._meta.db_table)


@pytest.mark.django_db
class TestDescriptionMaxLength:
    def test_value_at_the_ceiling_is_valid(self):
        description = ProjectDescriptionFactory.build(
            related=ProjectFactory(), value="x" * DESCRIPTION_MAX_LENGTH
        )

        description.full_clean()

    def test_value_one_character_over_the_ceiling_is_rejected(self):
        description = ProjectDescriptionFactory.build(
            related=ProjectFactory(), value="x" * (DESCRIPTION_MAX_LENGTH + 1)
        )

        with pytest.raises(ValidationError) as excinfo:
            description.full_clean()

        assert "value" in excinfo.value.message_dict


@pytest.mark.django_db
class TestIdentifierAddress:
    def test_a_type_with_a_resolver_gives_its_address(self):
        identifier = ContributorIdentifierFactory(
            related=PersonFactory(),
            type_id=f"{IDENTIFIER_TYPES}/wikidata",
            value="Q42",
        )

        assert identifier.get_absolute_url() == "https://www.wikidata.org/wiki/Q42"

    def test_a_type_with_no_resolver_gives_no_address(self):
        identifier = ProjectIdentifierFactory(
            related=ProjectFactory(),
            type_id=f"{IDENTIFIER_TYPES}/grant-number",
            value="EAR-1234567",
        )

        assert identifier.get_absolute_url() is None


@pytest.mark.django_db
class TestIdentifierUniqueness:
    """An identifier value names one record, whichever kind of record carries it."""

    def test_a_value_held_by_another_kind_of_record_is_refused(self):
        ProjectIdentifierFactory(
            related=ProjectFactory(),
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.1/shared",
        )
        taken = DatasetIdentifierFactory.build(
            related=DatasetFactory(),
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.1/shared",
        )

        with pytest.raises(ValidationError) as excinfo:
            taken.clean()

        assert "value" in excinfo.value.message_dict

    def test_a_stored_identifier_does_not_clash_with_itself(self):
        stored = ProjectIdentifierFactory(
            related=ProjectFactory(),
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.1/mine",
        )

        stored.clean()


@pytest.mark.django_db
class TestEndDateNotBeforeStart:
    """The rule every record's dates share.

    ``ProjectDate`` stands for any record that sets ``START_TYPE`` and ``END_TYPE``.
    """

    @pytest.fixture
    def project(self):
        return ProjectFactory()

    @staticmethod
    def start(project, value):
        return ProjectDate.objects.create(
            related=project, type_id=ProjectDate.START_TYPE, value=value
        )

    @staticmethod
    def end(project, value):
        return ProjectDate(related=project, type_id=ProjectDate.END_TYPE, value=value)

    def test_an_end_before_the_start_is_refused_naming_both_dates(self, project):
        self.start(project, "2020-06-01")

        with pytest.raises(ValidationError) as exc_info:
            self.end(project, "2019-05-01").full_clean()

        message = str(exc_info.value)
        assert "2020-06-01" in message
        assert "2019-05-01" in message

    def test_moving_the_start_after_an_existing_end_is_refused(self, project):
        start = self.start(project, "2020-01-01")
        self.end(project, "2020-12-31").save()

        start.value = "2021-01-01"
        with pytest.raises(ValidationError):
            start.full_clean()

    def test_an_end_with_no_start_is_accepted(self, project):
        self.end(project, "2024-06-15").full_clean()

    def test_the_comparison_stops_at_the_coarser_precision(self, project):
        self.start(project, "2020-06")

        self.end(project, "2020").full_clean()

        with pytest.raises(ValidationError):
            self.end(project, "2020-03").full_clean()

    def test_a_date_of_another_type_is_never_compared(self, project):
        self.start(project, "2020-06-01")
        other = ProjectDate(
            related=project, type_id=f"{DATE_TYPES}/created", value="2019-01-01"
        )

        other.clean()
