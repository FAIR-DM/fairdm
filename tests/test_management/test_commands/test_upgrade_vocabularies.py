"""Tests for ``fairdm/management/commands/upgrade_vocabularies.py``."""

from io import StringIO

import pytest
from controlled_vocabularies.models import ConceptScheme, Record
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.db.models import CharField

from fairdm.contrib.contributors.models import Contribution
from fairdm.core.project.models import ProjectDescription
from fairdm.core.vocabularies import (
    ABSTRACT,
    CREATOR,
    DESCRIPTION_TYPES,
    SAMPLE_STATUS,
)
from fairdm.factories import PersonFactory, ProjectFactory

#: What django-research-vocabs called FairDM's roles vocabulary.
OLD_ROLES = "fairdm-roles"
#: A keyword vocabulary of a portal's own, under the address it was published at.
TOPICS = "https://vocab.example.org/research-topics"


def run(**options):
    """Run the command and return what it printed."""
    # The test's own rows leave deferred constraint checks pending in its transaction, and
    # PostgreSQL alters no table with checks pending. A real upgrade starts with none.
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
    out = StringIO()
    call_command("upgrade_vocabularies", stdout=out, **options)
    return out.getvalue()


def table_columns(table):
    """Return the names of a table's columns."""
    with connection.cursor() as cursor:
        return {
            column.name
            for column in connection.introspection.get_table_description(cursor, table)
        }


def table_exists(table):
    """Say whether the database holds a table."""
    with connection.cursor() as cursor:
        return table in connection.introspection.table_names(cursor)


class LegacyDatabase:
    """A database as django-research-vocabs left it, for the tables these tests use.

    Project descriptions name their type in a column of their own, and the roles of a
    credit and the keywords of a project are rows of django-research-vocabs' tables.
    """

    def __init__(self):
        self.concepts = {}
        self.vocabularies = {}

    def build(self):
        """Put the description, role and keyword tables back in their old shape."""
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        field = ProjectDescription._meta.get_field("type")
        old = CharField(max_length=50)
        old.set_attributes_from_name("type")
        old.model = ProjectDescription
        with connection.schema_editor() as editor:
            editor.alter_field(ProjectDescription, field, old)
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE research_vocabs_vocabulary ("
                " id bigserial PRIMARY KEY, name varchar(255) UNIQUE NOT NULL,"
                " label varchar(255) NOT NULL, description text,"
                " uri varchar(200) UNIQUE NOT NULL, meta jsonb)"
            )
            cursor.execute(
                "CREATE TABLE research_vocabs_concept ("
                " id bigserial PRIMARY KEY, uri varchar(200) UNIQUE NOT NULL,"
                " name varchar(255) NOT NULL, label varchar(255) NOT NULL,"
                " meta jsonb,"
                " vocabulary_id bigint NOT NULL REFERENCES research_vocabs_vocabulary(id))"
            )
            for through, owner, owner_table in (
                (
                    "contributors_contribution_roles",
                    "contribution_id",
                    "contributors_contribution",
                ),
                ("project_project_keywords", "project_id", "project_project"),
            ):
                cursor.execute(f"DROP TABLE {through} CASCADE")
                cursor.execute(
                    f"CREATE TABLE {through} ("
                    f" id bigserial PRIMARY KEY,"
                    f" {owner} bigint NOT NULL REFERENCES {owner_table}(id),"
                    " concept_id bigint NOT NULL REFERENCES research_vocabs_concept(id))"
                )
        recorder = MigrationRecorder(connection)
        recorder.record_applied("research_vocabs", "0001_initial")
        for migration in (
            "0001_initial",
            "0002_indexed_concept_search",
            "0003_record_links",
        ):
            recorder.record_applied("controlled_vocabularies", migration)
        return self

    def concept(self, vocabulary, name, uri):
        """Hold a concept in django-research-vocabs' tables, and return its key."""
        with connection.cursor() as cursor:
            if vocabulary not in self.vocabularies:
                cursor.execute(
                    "INSERT INTO research_vocabs_vocabulary (name, label, uri)"
                    " VALUES (%s, %s, %s) RETURNING id",
                    [vocabulary, vocabulary, f"https://old.example.org/{vocabulary}"],
                )
                self.vocabularies[vocabulary] = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO research_vocabs_concept (uri, name, label, vocabulary_id)"
                " VALUES (%s, %s, %s, %s) RETURNING id",
                [uri, name, name, self.vocabularies[vocabulary]],
            )
            return cursor.fetchone()[0]

    def describe(self, project, type_name, value):
        """Store a description of a project by the old name of its type."""
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO project_projectdescription (related_id, type, value)"
                " VALUES (%s, %s, %s)",
                [project.pk, type_name, value],
            )

    def link(self, table, owner_column, owner_id, concept_id):
        """Link a row to a concept of django-research-vocabs."""
        with connection.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO {table} ({owner_column}, concept_id) VALUES (%s, %s)",  # noqa: S608
                [owner_id, concept_id],
            )


@pytest.fixture
def legacy(db):
    """Return the database in the shape django-research-vocabs left it."""
    return LegacyDatabase().build()


@pytest.fixture
def topics(db):
    """Load a keyword vocabulary of a portal's own, with one concept."""
    scheme = ConceptScheme.objects.create(
        uri=TOPICS,
        default_language="en",
        data={"skos:prefLabel": [{"@value": "Research topics", "@language": "en"}]},
    )
    return Record.objects.create(
        uri=f"{TOPICS}/geothermal-energy",
        scheme=scheme,
        type=Record.Type.CONCEPT,
        data={"skos:prefLabel": [{"@value": "Geothermal energy", "@language": "en"}]},
    )


@pytest.mark.django_db
class TestUpgradeVocabularies:
    def test_a_database_with_nothing_from_the_old_library_is_left_alone(self):
        description = ProjectDescription.objects.create(
            related=ProjectFactory(), type_id=ABSTRACT, value="Kept."
        )

        output = run()

        assert "Nothing to upgrade" in output
        description.refresh_from_db()
        assert description.type_id == ABSTRACT

    def test_a_stored_type_name_becomes_the_address_of_its_concept(self, legacy):
        project = ProjectFactory()
        legacy.describe(project, "Abstract", "An abstract.")
        legacy.describe(project, "Objectives", "Some objectives.")

        run()

        stored = dict(
            ProjectDescription.objects.filter(related=project).values_list(
                "type", "value"
            )
        )
        assert stored == {
            ABSTRACT: "An abstract.",
            f"{DESCRIPTION_TYPES}/objectives": "Some objectives.",
        }

    def test_a_role_of_fairdms_vocabulary_is_matched_by_its_name(self, legacy):
        project = ProjectFactory()
        credit = Contribution.add_to(PersonFactory(), project)
        old = legacy.concept(OLD_ROLES, "Creator", "https://old.example.org/Creator")
        legacy.link(
            "contributors_contribution_roles", "contribution_id", credit.pk, old
        )

        run()

        assert list(credit.roles.values_list("uri", flat=True)) == [CREATOR]

    def test_a_keyword_of_another_vocabulary_is_matched_by_its_address(
        self, legacy, topics
    ):
        project = ProjectFactory()
        old = legacy.concept("demo-research-topics", "geothermal-energy", topics.uri)
        legacy.link("project_project_keywords", "project_id", project.pk, old)

        run()

        assert list(project.keywords.values_list("uri", flat=True)) == [topics.uri]

    def test_a_role_offered_as_a_keyword_is_matched_by_its_name(self, legacy):
        project = ProjectFactory()
        old = legacy.concept(OLD_ROLES, "Creator", "https://old.example.org/Creator")
        legacy.link("project_project_keywords", "project_id", project.pk, old)

        run()

        assert list(project.keywords.values_list("uri", flat=True)) == [CREATOR]

    def test_the_old_tables_and_their_migration_records_are_gone(self, legacy):
        run()

        assert not table_exists("research_vocabs_concept")
        assert not table_exists("research_vocabs_vocabulary")
        assert "type_id" in table_columns("project_projectdescription")
        assert "record_id" in table_columns("contributors_contribution_roles")
        recorder = MigrationRecorder(connection)
        assert not recorder.migration_qs.filter(app="research_vocabs").exists()

    def test_an_unmatched_value_is_listed_and_nothing_is_changed(self, legacy):
        project = ProjectFactory()
        legacy.describe(project, "Abstract", "An abstract.")
        legacy.describe(project, "TableOfContents", "No such type.")
        credit = Contribution.add_to(PersonFactory(), project)
        old = legacy.concept("retired-roles", "Sponsor", "https://old.example.org/x")
        legacy.link(
            "contributors_contribution_roles", "contribution_id", credit.pk, old
        )

        with pytest.raises(CommandError) as refused:
            run()

        message = str(refused.value)
        assert "project.ProjectDescription.type: 'TableOfContents'" in message
        assert "contributors.Contribution.roles: 'Sponsor'" in message
        assert "type" in table_columns("project_projectdescription")
        assert table_exists("research_vocabs_concept")

    def test_it_refuses_while_fairdms_vocabularies_are_not_loaded(self):
        ConceptScheme.objects.filter(uri=SAMPLE_STATUS).delete()
        LegacyDatabase().build()

        with pytest.raises(CommandError) as refused:
            run()

        assert SAMPLE_STATUS in str(refused.value)
        assert "type" in table_columns("project_projectdescription")

    def test_a_table_already_in_the_new_shape_is_left_as_it_is(self, legacy):
        before = table_columns("dataset_dataset_keywords")

        run()

        assert table_columns("dataset_dataset_keywords") == before
