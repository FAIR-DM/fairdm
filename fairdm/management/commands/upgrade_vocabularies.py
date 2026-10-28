"""Move a database from django-research-vocabs to terms stored by their vocabulary addresses."""

from controlled_vocabularies.fields import ConceptField, MultiConceptField
from controlled_vocabularies.models import ConceptScheme, Record
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections, router, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder
from django.db.migrations.state import ProjectState
from django.db.models import CharField

from fairdm.core.vocabularies import (
    CONTRIBUTOR_ROLES,
    DATE_TYPES,
    DESCRIPTION_TYPES,
    IDENTIFIER_TYPES,
    SAMPLE_STATUS,
    notation,
)

#: The vocabulary each of FairDM's own vocabularies was held under in django-research-vocabs,
#: and the address it is published at now.
FAIRDM_VOCABULARIES = {
    "fairdm-roles": CONTRIBUTOR_ROLES,
    "fairdm-descriptions": DESCRIPTION_TYPES,
    "fairdm-dates": DATE_TYPES,
    "fairdm-identifiers": IDENTIFIER_TYPES,
    "fairdm-sample-status": SAMPLE_STATUS,
}

#: The tables django-research-vocabs kept its vocabularies in.
LEGACY_TABLES = ("research_vocabs_concept", "research_vocabs_vocabulary")


class Command(BaseCommand):
    """Convert a database that stored terms with django-research-vocabs.

    django-research-vocabs stored a term in a model's own column by its name, such as
    ``Abstract`` or ``unknown``, and kept keywords and roles in its own tables. This command
    stores each term as the address of the same concept in the vocabularies the site has
    loaded, matching a stored name to a concept's ``skos:notation``. A keyword or role from
    one of FairDM's own vocabularies is matched by notation too, and one from any other
    vocabulary by the address django-research-vocabs held for it.

    Every stored value is matched before anything is written. If any value has no match,
    the command lists them all and changes nothing. Run it before ``migrate``. A database
    created with this release needs none of it.
    """

    help = (
        "Store the terms django-research-vocabs held as the addresses of the same concepts. "
        "Load the vocabularies with sync_vocabularies first, and run this before migrate."
    )

    def add_arguments(self, parser):
        """Add ``--database``."""
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="The database to upgrade. Defaults to 'default'.",
        )

    def handle(self, *args, database, **options):
        """Upgrade the database in one transaction, or change nothing."""
        connection = connections[database]
        recorder = MigrationRecorder(connection)
        applied = {app for app, name in recorder.applied_migrations()}
        if "research_vocabs" not in applied:
            self.stdout.write(
                "Nothing to upgrade: the database holds no terms from django-research-vocabs."
            )
            return

        if "controlled_vocabularies" not in applied:
            self.create_vocabulary_tables(connection)
            self.stdout.write("Created the tables of django-controlled-vocabularies.")

        missing = sorted(
            set(FAIRDM_VOCABULARIES.values())
            - set(ConceptScheme.objects.using(database).values_list("uri", flat=True))
        )
        if missing:
            raise CommandError(
                "These vocabularies are not loaded: "
                + ", ".join(missing)
                + ". Load them with `python manage.py sync_vocabularies`, then run "
                "upgrade_vocabularies again. No stored term was changed."
            )

        columns = self.legacy_columns(connection, database)
        fields = [(model, field) for model, field, length in columns]
        tables = self.legacy_tables(connection, database)
        with connection.cursor() as cursor:
            column_updates, unmatched = self.match_columns(cursor, database, fields)
            rows, unmatched_rows = self.match_tables(cursor, database, tables)
        unmatched += unmatched_rows
        if unmatched:
            raise CommandError(
                "These stored terms match no concept, so nothing was changed:\n"
                + "\n".join(unmatched)
            )

        with transaction.atomic(using=database):
            with connection.schema_editor() as editor:
                for model, field, length in columns:
                    self.widen(editor, model, field, length)
            with connection.cursor() as cursor:
                for model, field, mapping in column_updates:
                    table = connection.ops.quote_name(model._meta.db_table)
                    column = connection.ops.quote_name(field.name)
                    for old, new in mapping.items():
                        cursor.execute(
                            f"UPDATE {table} SET {column} = %s WHERE {column} = %s",  # noqa: S608
                            [new, old],
                        )
            with connection.schema_editor() as editor:
                for model, field in fields:
                    editor.alter_field(model, self.wide_column(model, field), field)
                for field in tables:
                    through = field.remote_field.through
                    editor.execute(
                        editor.sql_delete_table
                        % {"table": editor.quote_name(through._meta.db_table)}
                    )
                    editor.create_model(through)
                for table in LEGACY_TABLES:
                    editor.execute(
                        editor.sql_delete_table % {"table": editor.quote_name(table)}
                    )
            for field, links in rows.items():
                through = field.remote_field.through
                owner, concept = self.through_columns(field)
                through.objects.using(database).bulk_create(
                    through(**{owner: owner_id, concept: uri})
                    for owner_id, uri in links
                )
            recorder.migration_qs.filter(app="research_vocabs").delete()

        for model, field in fields:
            self.stdout.write(f"Stored {model._meta.label}.{field.name} by address.")
        for field in tables:
            self.stdout.write(
                f"Moved {field.model._meta.label}.{field.name} to the loaded vocabularies."
            )

    def create_vocabulary_tables(self, connection):
        """Apply django-controlled-vocabularies' own migrations, which nothing else needs.

        ``migrate`` refuses this database while its FairDM migrations are recorded and the
        ones they now depend on are not, so the tables the vocabularies load into are made
        here, from an empty state, as ``migrate`` would.

        Args:
            connection: The connection to the database being upgraded.
        """
        executor = MigrationExecutor(connection)
        executor.migrate(
            executor.loader.graph.leaf_nodes("controlled_vocabularies"),
            state=ProjectState(),
        )

    def models_to_upgrade(self, database):
        """Yield every installed model this database holds a table for.

        Args:
            database: The alias of the database being upgraded.

        Yields:
            Each managed, concrete model migrations would create on it.
        """
        for model in apps.get_models():
            if model._meta.managed and router.allow_migrate_model(database, model):
                yield model

    def legacy_columns(self, connection, database):
        """Find each concept field whose column still holds a term's name.

        Args:
            connection: The connection to the database being upgraded.
            database: Its alias.

        Returns:
            One ``(model, field, length)`` triple per field, ``length`` being the old
            column's size.
        """
        found = []
        with connection.cursor() as cursor:
            for model in self.models_to_upgrade(database):
                fields = [
                    field
                    for field in model._meta.local_fields
                    if isinstance(field, ConceptField)
                ]
                if not fields:
                    continue
                description = {
                    column.name: column
                    for column in connection.introspection.get_table_description(
                        cursor, model._meta.db_table
                    )
                }
                for field in fields:
                    old = description.get(field.name)
                    if old is not None and field.column not in description:
                        found.append((model, field, old.internal_size))
        return found

    def legacy_tables(self, connection, database):
        """Find each concept set whose table still points at django-research-vocabs.

        Args:
            connection: The connection to the database being upgraded.
            database: Its alias.

        Returns:
            The ``MultiConceptField`` of each such table.
        """
        found = []
        with connection.cursor() as cursor:
            for model in self.models_to_upgrade(database):
                for field in model._meta.local_many_to_many:
                    if not isinstance(field, MultiConceptField):
                        continue
                    columns = {
                        column.name
                        for column in connection.introspection.get_table_description(
                            cursor, field.remote_field.through._meta.db_table
                        )
                    }
                    if "concept_id" in columns:
                        found.append(field)
        return found

    def admitted(self, field, database):
        """Return the concepts a field admits, as ``{notation: address}`` and a set of addresses.

        Args:
            field: A ``ConceptField`` or ``MultiConceptField``.
            database: The alias of the database being upgraded.

        Returns:
            A ``(by_notation, addresses)`` pair over the concepts the field may hold.
        """
        concepts = list(
            Record.objects.using(database).filter(field.get_limit_choices_to())
        )
        return (
            {notation(concept): concept.uri for concept in concepts},
            {concept.uri for concept in concepts},
        )

    def match_columns(self, cursor, database, fields):
        """Match every distinct value of each old column to a concept the field admits.

        Args:
            cursor: A cursor on the database being upgraded.
            database: Its alias.
            fields: The ``(model, field)`` pairs whose columns still hold names.

        Returns:
            The ``(model, field, {old: address})`` updates, and one line per value with no
            match.
        """
        updates, unmatched = [], []
        for model, field in fields:
            by_notation = self.admitted(field, database)[0]
            column = cursor.db.ops.quote_name(field.name)
            table = cursor.db.ops.quote_name(model._meta.db_table)
            cursor.execute(
                f"SELECT {column}, COUNT(*) FROM {table} GROUP BY {column}"  # noqa: S608
            )
            mapping = {}
            for value, count in cursor.fetchall():
                if value is None or value == "":
                    continue
                if value in by_notation:
                    mapping[value] = by_notation[value]
                else:
                    unmatched.append(
                        f"{model._meta.label}.{field.name}: {value!r} ({count} rows)"
                    )
            updates.append((model, field, mapping))
        return updates, unmatched

    def match_tables(self, cursor, database, tables):
        """Match every keyword and role held in django-research-vocabs' tables to a concept.

        Args:
            cursor: A cursor on the database being upgraded.
            database: Its alias.
            tables: The fields from :meth:`legacy_tables`.

        Returns:
            ``{field: [(owner id, address)]}``, and one line per term with no match.
        """
        rows, unmatched = {}, []
        notations = {
            (concept.scheme.uri, notation(concept)): concept.uri
            for concept in Record.objects.using(database)
            .filter(
                scheme__uri__in=FAIRDM_VOCABULARIES.values(),
                type=Record.Type.CONCEPT,
            )
            .select_related("scheme")
        }
        for field in tables:
            addresses = self.admitted(field, database)[1]
            owner = self.through_columns(field)[0]
            table = cursor.db.ops.quote_name(field.remote_field.through._meta.db_table)
            cursor.execute(
                f"SELECT link.{cursor.db.ops.quote_name(owner)}, c.name, c.uri, v.name"  # noqa: S608
                f" FROM {table} link"
                " JOIN research_vocabs_concept c ON c.id = link.concept_id"
                " JOIN research_vocabs_vocabulary v ON v.id = c.vocabulary_id"
                " ORDER BY link.id"
            )
            links = []
            for owner_id, name, uri, vocabulary in cursor.fetchall():
                if vocabulary in FAIRDM_VOCABULARIES:
                    found = notations.get((FAIRDM_VOCABULARIES[vocabulary], name))
                else:
                    found = uri
                if found in addresses:
                    links.append((owner_id, found))
                else:
                    unmatched.append(
                        f"{field.model._meta.label}.{field.name}: {name!r} from "
                        f"{vocabulary!r} ({uri})"
                    )
            rows[field] = links
        return rows, unmatched

    def through_columns(self, field):
        """Name the columns of a concept set's table: the owner's and the concept's.

        Args:
            field: A ``MultiConceptField``.

        Returns:
            The ``(owner column, concept column)`` pair.
        """
        through = field.remote_field.through
        owner = next(
            f.column
            for f in through._meta.local_fields
            if f.is_relation and f.related_model is field.model
        )
        concept = next(
            f.column
            for f in through._meta.local_fields
            if f.is_relation and f.related_model is Record
        )
        return owner, concept

    def wide_column(self, model, field):
        """Return the old column as text wide enough for an address.

        Args:
            model: The model the field belongs to.
            field: The concept field.

        Returns:
            An unsaved ``CharField`` on the old column, the size of an address.
        """
        column = CharField(max_length=Record._meta.get_field("uri").max_length)
        column.set_attributes_from_name(field.name)
        column.model = model
        column.null = field.null
        return column

    def widen(self, editor, model, field, length):
        """Make the old column wide enough to hold an address.

        Args:
            editor: The schema editor to alter the table with.
            model: The model the field belongs to.
            field: The concept field.
            length: The old column's size.
        """
        old = CharField(max_length=length)
        old.set_attributes_from_name(field.name)
        old.model = model
        old.null = field.null
        editor.alter_field(model, old, self.wide_column(model, field))
