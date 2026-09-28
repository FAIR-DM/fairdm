"""Package-level health checks: the migrations describe the models and can be run."""

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

# The suite runs with --no-migrations, so these tests need the real migration modules back.
REAL_MIGRATION_MODULES: dict[str, str] = {}


def first_party_app_labels():
    """Return the labels of the apps whose migrations live in this repository."""
    return {
        config.label
        for config in global_apps.get_app_configs()
        if "site-packages" not in Path(config.path).parts
    }


def run_migrate(tmp_path, *arguments):
    """Run ``manage.py migrate`` in a subprocess against ``tests.migration_settings``."""
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


class TestMigrations:
    @override_settings(MIGRATION_MODULES=REAL_MIGRATION_MODULES)
    def test_every_model_change_has_a_migration(self):
        # Nothing in CI ran `makemigrations --check`, so #229 shipped model changes with no migration.
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

    @pytest.mark.slow
    def test_migrations_apply_to_an_empty_database(self, tmp_path):
        # A migration that cannot run on the schema its predecessors left breaks every fresh install (#252).
        result = run_migrate(tmp_path)

        assert result.returncode == 0, (
            "`manage.py migrate` failed against an empty database:\n"
            f"{result.stdout}\n{result.stderr}"
        )

    @pytest.mark.slow
    def test_migrations_read_the_database_they_are_migrating(self, tmp_path):
        # RunPython gets the alias as schema_editor.connection; a query on `default` reads the wrong schema.
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
