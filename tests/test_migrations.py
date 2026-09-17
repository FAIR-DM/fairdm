"""
Tests that the migrations in this repository describe the models and can be run.

The rest of the suite builds its database straight from the models
(``--no-migrations``), which is fast but means nothing here ever executes a
migration. Both failures these tests catch are invisible under that setting and
total for anyone starting from an empty database:

- a model change with no migration behind it, so a database built from the
  migrations and one built from the models disagree, and
- a migration that cannot run against the schema the migrations before it left.

Both are checked against the apps that keep their migrations in this
repository. Third-party apps are excluded: their drift is real but it is theirs
to fix, and a failure here would be one nobody reading it can act on.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.apps import apps as global_apps
from django.conf import settings
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.questioner import NonInteractiveMigrationQuestioner
from django.db.migrations.state import ProjectState
from django.test import override_settings

# pytest runs the suite with --no-migrations, which points every app at a
# missing migration module. These tests are the two that need the real ones.
REAL_MIGRATION_MODULES: dict[str, str] = {}


def first_party_app_labels():
    """Return the labels of the apps whose migrations live in this repository."""
    return {
        config.label
        for config in global_apps.get_app_configs()
        if "site-packages" not in Path(config.path).parts
    }


@override_settings(MIGRATION_MODULES=REAL_MIGRATION_MODULES)
def test_every_model_change_has_a_migration():
    """A model change with no migration behind it fails here, naming the app.

    ``makemigrations --check`` run by hand is the same question, but nothing in
    CI asks it, which is how ``identity`` came to carry two constraint changes
    with no migration for them (issue #229).
    """
    loader = MigrationLoader(None, ignore_no_migrations=True)
    autodetector = MigrationAutodetector(
        loader.project_state(),
        ProjectState.from_apps(global_apps),
        NonInteractiveMigrationQuestioner(specified_apps=set(), dry_run=True),
    )
    changes = autodetector.changes(graph=loader.graph)

    ours = sorted(set(changes) & first_party_app_labels())
    assert not ours, (
        f"These apps have model changes with no migration: {', '.join(ours)}. "
        "Run `python manage.py makemigrations <app> --settings=config.settings` "
        "and commit the result."
    )


def run_migrate(tmp_path, *arguments):
    """Run ``manage.py migrate`` against ``tests.migration_settings``.

    A subprocess because this is the command a new installation runs, and
    because the suite's own connection is already built without migrations.
    """
    return subprocess.run(
        [
            sys.executable,
            "manage.py",
            "migrate",
            "--settings=tests.migration_settings",
            "--no-input",
            *arguments,
        ],
        cwd=settings.BASE_DIR,
        env={
            **os.environ,
            "DJANGO_ENV": "development",
            "FAIRDM_MIGRATION_TEST_DIR": str(tmp_path),
        },
        capture_output=True,
        text=True,
        timeout=900,
    )


@pytest.mark.slow
def test_migrations_apply_to_an_empty_database(tmp_path):
    """Every migration applies, in order, to a database that has never held data.

    A migration that cannot run against the schema its predecessors left is
    invisible to everyone already running the project and total for every new
    installation and every fresh deployment (issue #252).
    """
    result = run_migrate(tmp_path)

    assert result.returncode == 0, (
        "`manage.py migrate` failed against an empty database:\n"
        f"{result.stdout}\n{result.stderr}"
    )


@pytest.mark.slow
def test_migrations_read_the_database_they_are_migrating(tmp_path):
    """A data migration reads the database being migrated, not ``default``.

    ``RunPython`` is handed the alias to use as ``schema_editor.connection``.
    A query that ignores it goes to ``default``, which is a different database
    with a different schema in any project that migrates a second one - and the
    query then fails, or worse, quietly reads and writes the wrong data.

    The first run builds ``default`` from empty, so the second run meets exactly
    that: a ``default`` already past the migration doing the asking.
    """
    first = run_migrate(tmp_path)
    assert first.returncode == 0, f"{first.stdout}\n{first.stderr}"

    second = run_migrate(tmp_path, "--database=migration_check")

    assert second.returncode == 0, (
        "`manage.py migrate --database=migration_check` failed while `default` "
        "was already migrated, which means a migration read the wrong "
        f"database:\n{second.stdout}\n{second.stderr}"
    )
    assert (tmp_path / "migrated.sqlite3").exists(), (
        "migrate reported success but produced no database:\n"
        f"{second.stdout}\n{second.stderr}"
    )
