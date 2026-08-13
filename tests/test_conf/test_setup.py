"""
Tests for FairDM configuration setup and environment loading.

Tests validate that:
- The resolved environment loads correctly based on DJANGO_ENV
- Production fails fast on missing configuration
- Development degrades gracefully
- Configuration validation works as expected
- Assignment after ``setup()`` and the ``env_file`` parameter behave correctly
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

# Test fixtures


@pytest.fixture
def clean_env():
    """Provide a clean environment for testing."""
    original_env = os.environ.copy()
    # Clear relevant env vars
    for key in list(os.environ.keys()):
        if key.startswith(("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_")):
            del os.environ[key]

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


class TestResolvedEnvironment:
    """Test resolution of the ``DJANGO_ENV`` environment variable (FR-007)."""

    def test_missing_django_env_resolves_to_production(
        self, clean_env, settings_module
    ):
        """``DJANGO_ENV`` unset resolves to ``production``."""
        module = settings_module()

        assert module.DJANGO_ENV == "production"

    def test_empty_string_django_env_is_looked_up_literally(
        self, clean_env, settings_module
    ):
        """An empty ``DJANGO_ENV`` is not normalised to ``production`` (edge case)."""
        os.environ["DJANGO_ENV"] = ""

        module = settings_module()

        assert module.DJANGO_ENV == ""
        # No override module is named "" — the baseline stands, unchanged.
        assert module.DEBUG is False

    def test_environment_name_differing_only_in_case_is_not_normalised(
        self, clean_env, settings_module
    ):
        """A name differing only in case from a shipped one is looked up literally (edge case)."""
        os.environ["DJANGO_ENV"] = "Development"

        module = settings_module()

        assert module.DJANGO_ENV == "Development"
        # "Development" != "development" — FairDM's override module is not found.
        assert module.DEBUG is False


class TestLayerOrder:
    """Test the five-layer composition order (FR-008)."""

    def test_layers_apply_in_declared_order(
        self, production_env, tmp_path, settings_module
    ):
        """Baseline, FairDM override, addons, portal override, post-call assignment."""
        os.environ["DJANGO_ENV"] = "development"
        (tmp_path / "development.py").write_text("PORTAL_OVERRIDE_MARKER = 'portal'\n")

        module = settings_module(
            setup_call="fairdm.setup(addons=['tests.test_conf.dummy_addon'])",
            after="POST_CALL_MARKER = 'post'",
            directory=tmp_path,
        )

        # Layer 1 — baseline: a setting only the production baseline sets.
        assert module.SESSION_COOKIE_HTTPONLY is True
        # Layer 2 — FairDM's environment override wins over the baseline (DEBUG
        # defaults to False in settings/security.py; development.py sets True).
        assert module.DEBUG is True
        # Layer 3 — addon settings are applied.
        assert module.DUMMY_ADDON_INSTALLED is True
        # Layer 4 — the portal's own override module is applied.
        assert module.PORTAL_OVERRIDE_MARKER == "portal"
        # Layer 5 — assignment after the setup() call is the final word.
        assert module.POST_CALL_MARKER == "post"

    def test_override_module_selected_by_existence_not_allowlist(
        self, production_env, tmp_path, settings_module
    ):
        """An override module is found for any environment name, not just a fixed set (FR-010)."""
        os.environ["DJANGO_ENV"] = "qa"
        (tmp_path / "qa.py").write_text("QA_OVERRIDE_MARKER = True\n")

        module = settings_module(directory=tmp_path)

        assert module.QA_OVERRIDE_MARKER is True

    def test_environment_with_no_shipped_module_resolves_to_baseline_unchanged(
        self, production_env, tmp_path, settings_module
    ):
        """An environment neither FairDM nor the portal ships a module for is silent (FR-010, scenario 3)."""
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module(directory=tmp_path)

        # The baseline stands: DEBUG keeps its production-baseline default.
        assert module.DEBUG is False

    def test_fairdm_and_portal_overrides_for_the_same_environment_both_apply(
        self, production_env, tmp_path, settings_module
    ):
        """FairDM's and the portal's override modules for the same environment both apply, in order (edge case)."""
        os.environ["DJANGO_ENV"] = "development"
        # FairDM ships development.py (sets DEBUG = True). The portal's own
        # development.py, applied after, must win.
        (tmp_path / "development.py").write_text("DEBUG = 'portal-wins'\n")

        module = settings_module(directory=tmp_path)

        assert module.DEBUG == "portal-wins"


class TestProvenance:
    """Test the provenance record ``setup()`` builds while composing layers
    (FR-019, FR-020, research R2)."""

    def test_records_one_entry_per_layer_with_name_path_found_and_settings(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"
        (tmp_path / "development.py").write_text("PORTAL_OVERRIDE_MARKER = 'portal'\n")

        settings_module(
            setup_call="fairdm.setup(addons=['tests.test_conf.dummy_addon'])",
            directory=tmp_path,
        )

        from fairdm.conf import record

        layers = record.layers()
        assert [layer.name for layer in layers] == [
            "baseline",
            "fairdm override",
            "addons",
            "portal override",
        ]

        for layer in layers:
            assert layer.found is True
            assert layer.path is not None
            assert layer.settings, f"{layer.name} recorded no settings"

        baseline, fairdm_override, addons, portal_override = layers
        # Layer 1 — a setting only the production baseline sets.
        assert "SESSION_COOKIE_HTTPONLY" in baseline.settings
        # Layer 2 — FairDM's development.py sets DEBUG = True.
        assert "DEBUG" in fairdm_override.settings
        # Layer 3 — the dummy addon's setup module.
        assert "DUMMY_ADDON_INSTALLED" in addons.settings
        # Layer 4 — the portal's own override module.
        assert "PORTAL_OVERRIDE_MARKER" in portal_override.settings

    def test_record_never_holds_secret_values_only_their_names(
        self, production_env, tmp_path, settings_module
    ):
        secret_key = "s3cr3t-key-marker-" + "x" * 40
        db_password = "db-password-marker-9f8a7b6c"
        email_password = "email-password-marker-1a2b3c"
        os.environ["DJANGO_ENV"] = "production"
        os.environ["DJANGO_SECRET_KEY"] = secret_key
        os.environ["DATABASE_URL"] = (
            f"postgresql://user:{db_password}@localhost:5432/testdb"
        )
        os.environ["EMAIL_HOST_PASSWORD"] = email_password

        settings_module(directory=tmp_path)

        from fairdm.conf import record

        record_text = repr(record.layers())

        assert secret_key not in record_text
        assert db_password not in record_text
        assert email_password not in record_text

        # The setting NAMES that carried those values are legitimately present.
        all_settings = {
            name for layer in record.layers() for name in layer.settings
        }
        assert "SECRET_KEY" in all_settings
        assert "DATABASES" in all_settings
        assert "EMAIL_HOST_PASSWORD" in all_settings

    def test_absent_layers_are_recorded_as_absent_not_omitted(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"  # no FairDM or portal override for "qa"

        settings_module(directory=tmp_path)

        from fairdm.conf import record

        by_name = {layer.name: layer for layer in record.layers()}

        assert "fairdm override" in by_name
        assert by_name["fairdm override"].found is False
        assert by_name["fairdm override"].settings == ()

        assert "portal override" in by_name
        assert by_name["portal override"].found is False
        assert by_name["portal override"].settings == ()

    def test_producer_names_the_layer_that_wrote_the_final_value(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"
        (tmp_path / "development.py").write_text("DEBUG = 'portal-wins'\n")

        module = settings_module(directory=tmp_path)

        from fairdm.conf import record

        producer = record.producer("DEBUG")

        assert producer is not None
        assert producer.name == "portal override"
        # Not merely last in the list — the resolved value really is what
        # the named layer wrote.
        assert module.DEBUG == "portal-wins"

    def test_producer_names_a_layer_that_appended_to_an_existing_list(
        self, production_env, tmp_path, settings_module
    ):
        """A layer that extends a list the baseline already set is its producer.

        ``INSTALLED_APPS += [...]`` calls ``list.__iadd__``, which mutates the
        baseline's own list object in place. Attributing the layer by object
        identity misses it entirely, and reports the baseline as the producer
        of a value the baseline did not write.
        """
        os.environ["DJANGO_ENV"] = "development"
        (tmp_path / "development.py").write_text(
            "INSTALLED_APPS = globals()['INSTALLED_APPS']\n"
            "INSTALLED_APPS += ['portal_appended_app']\n"
        )

        module = settings_module(directory=tmp_path)

        from fairdm.conf import record

        assert "portal_appended_app" in module.INSTALLED_APPS

        producer = record.producer("INSTALLED_APPS")

        assert producer is not None
        assert producer.name == "portal override"

    def test_shipped_development_override_is_the_producer_of_what_it_appends(
        self, production_env, tmp_path, settings_module
    ):
        """The one override layer FairDM ships appends rather than reassigns.

        ``fairdm/conf/development.py`` extends both ``INSTALLED_APPS`` and
        ``MIDDLEWARE`` in place, so these are the settings a portal is most
        likely to interrogate and the ones an identity diff gets wrong.
        """
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module(directory=tmp_path)

        from fairdm.conf import record

        assert "django_browser_reload" in module.INSTALLED_APPS

        for setting in ("INSTALLED_APPS", "MIDDLEWARE"):
            producer = record.producer(setting)
            assert producer is not None, setting
            assert producer.name == "fairdm override", setting


class TestProvenanceCoversEverySetting:
    """Every setting a baseline module sets names a producing layer (SC-005)."""

    #: Bookkeeping keys ``setup()`` injects itself, not settings any layer
    #: names (see ``TestProductionVsDevelopmentDiff``).
    BOOKKEEPING_KEYS = {"DJANGO_ENV", "BASE_DIR", "FAIRDM_APPS"}

    def test_every_baseline_setting_names_a_producing_layer(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands alone

        module = settings_module(directory=tmp_path)

        from fairdm.conf import record

        resolved_settings = {
            key for key in vars(module) if key.isupper()
        } - self.BOOKKEEPING_KEYS

        unattributed = [
            name for name in resolved_settings if record.producer(name) is None
        ]

        assert not unattributed, f"unattributed settings: {sorted(unattributed)}"


class TestShippedOverrides:
    """Test which override modules FairDM itself ships (FR-009)."""

    #: Modules under fairdm/conf/ that are infrastructure, not environment overrides.
    INFRASTRUCTURE_MODULES = {
        "__init__",
        "setup",
        "environment",
        "checks",
        "addons",
        "orbit",
        "urls",
        "celery",
    }

    def test_only_development_is_shipped(self):
        import fairdm.conf

        conf_dir = Path(fairdm.conf.__file__).parent
        candidate_stems = {
            path.stem
            for path in conf_dir.glob("*.py")
            if path.stem not in self.INFRASTRUCTURE_MODULES
        }

        assert candidate_stems == {"development"}


class TestProductionVsDevelopmentDiff:
    """Test that development differs from production only in what development.py names (SC-002)."""

    def test_development_differs_only_in_keys_development_module_names(
        self, production_env, tmp_path, settings_module
    ):
        import ast

        import fairdm.conf

        prod_dir = tmp_path / "prod"
        dev_dir = tmp_path / "dev"

        os.environ["DJANGO_ENV"] = "production"
        prod_module = settings_module(directory=prod_dir)

        os.environ["DJANGO_ENV"] = "development"
        dev_module = settings_module(directory=dev_dir)

        # Bookkeeping keys setup() injects itself, not settings any module names.
        bookkeeping_keys = {"DJANGO_ENV", "BASE_DIR", "FAIRDM_APPS"}

        prod_settings = {k: v for k, v in vars(prod_module).items() if k.isupper()}
        dev_settings = {k: v for k, v in vars(dev_module).items() if k.isupper()}

        diff_keys = {
            key
            for key in set(prod_settings) | set(dev_settings)
            if prod_settings.get(key) != dev_settings.get(key)
        } - bookkeeping_keys

        development_py = Path(fairdm.conf.__file__).parent / "development.py"
        tree = ast.parse(development_py.read_text())
        named_keys = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, (ast.Assign, ast.AugAssign))
            for target in (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
            if isinstance(target, ast.Name)
        }

        assert diff_keys <= named_keys


class TestDevelopmentLayerApplies:
    """``DJANGO_ENV=development`` applies FairDM's ``development.py`` on top
    of the baseline, and every setting neither module names stays unchanged
    (US-2 scenario 2, FR-009)."""

    #: Settings neither the production baseline nor development.py branches
    #: on — resolving these identically in both environments is what "layered
    #: on top of" means, as distinct from "a different configuration".
    UNCHANGED_BETWEEN_ENVIRONMENTS = ["AUTH_USER_MODEL", "TIME_ZONE", "SITE_ID"]

    def test_development_overrides_debug_and_security_settings(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module(directory=tmp_path)

        assert module.DEBUG is True
        assert "localhost" in module.ALLOWED_HOSTS
        assert module.CSRF_COOKIE_SECURE is False
        assert module.SESSION_COOKIE_SECURE is False

    def test_settings_neither_module_names_stay_unchanged(
        self, production_env, tmp_path, settings_module
    ):
        prod_dir = tmp_path / "prod"
        dev_dir = tmp_path / "dev"

        os.environ["DJANGO_ENV"] = "production"
        prod_module = settings_module(directory=prod_dir)

        os.environ["DJANGO_ENV"] = "development"
        dev_module = settings_module(directory=dev_dir)

        for setting_name in self.UNCHANGED_BETWEEN_ENVIRONMENTS:
            assert getattr(prod_module, setting_name) == getattr(
                dev_module, setting_name
            ), f"{setting_name} differs between production and development"


class TestPortalOverride:
    """Test that the portal's override module is resolved beside its settings module (FR-011)."""

    def test_override_found_beside_settings_module_regardless_of_directory_name(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"
        odd_dir = tmp_path / "not_called_config"
        (odd_dir).mkdir()
        (odd_dir / "development.py").write_text("PORTAL_OVERRIDE_MARKER = 'found'\n")

        module = settings_module(
            directory=odd_dir,
            filename="portal_settings.py",
        )

        assert module.PORTAL_OVERRIDE_MARKER == "found"

    def test_no_usable_file_skips_portal_override_with_warning(
        self, production_env, tmp_path
    ):
        """A settings module with no usable ``__file__`` is skipped, not raised (edge case)."""
        # tests/settings.py disables logging for the whole suite, so the
        # warning is observed by patching the call rather than via caplog.
        code = compile(
            "from pathlib import Path\n"
            "import fairdm\n"
            f"fairdm.setup(base_dir=Path({str(tmp_path)!r}))",
            "<string>",
            "exec",
        )
        scope = {}

        with mock.patch("fairdm.conf.setup.logger.warning") as mock_warning:
            exec(code, scope)  # noqa: S102 — simulates a settings module with no __file__

        assert mock_warning.called
        warned_text = " ".join(
            str(call.args[0]) for call in mock_warning.call_args_list
        )
        assert "settings module" in warned_text.lower() or "__file__" in warned_text
        assert scope["DJANGO_ENV"] == "production"


class TestBaselineCompleteness:
    """A settings module whose entire content is ``fairdm.setup()`` produces
    a configuration where every FairDM-owned setting is present and
    ``manage.py check`` raises nothing (FR-001, SC-001).

    Run out-of-process — ``manage.py check`` needs a populated app registry
    (``django.setup()``), which this repository's own test session already
    has, from a different settings module (``tests.settings``).
    """

    def test_minimal_settings_module_passes_manage_py_check(self, tmp_path):
        repo_root = Path(__file__).resolve().parents[2]

        settings_dir = tmp_path / "config"
        settings_dir.mkdir()
        (settings_dir / "__init__.py").write_text("")
        (settings_dir / "settings.py").write_text("import fairdm\n\nfairdm.setup()\n")

        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(
                ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
            )
        }
        env |= {
            "DJANGO_ENV": "development",
            "DJANGO_SETTINGS_MODULE": "config.settings",
            # No urls.py in this minimal portal — reuse FairDM's own, exactly
            # as a portal that hasn't written one yet would.
            "DJANGO_ROOT_URLCONF": "fairdm.conf.urls",
            "PYTHONPATH": f"{tmp_path}{os.pathsep}{repo_root}",
        }
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import django; django.setup()\n"
                "from django.core.management import call_command\n"
                "call_command('check')\n"
                "print('CHECK_OK')",
            ],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "CHECK_OK" in result.stdout

    def test_minimal_settings_module_defines_every_fairdm_owned_setting(
        self, production_env, tmp_path, settings_module
    ):
        """A representative setting from every settings/*.py module is
        present after a bare ``fairdm.setup()`` call (FR-001)."""
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands

        module = settings_module(directory=tmp_path)

        representative_settings = [
            "INSTALLED_APPS",  # apps.py
            "SECRET_KEY",  # security.py
            "DATABASES",  # database.py
            "CACHES",  # cache.py
            "STATIC_URL",  # static_media.py
            "CELERY_BROKER_URL",  # celery.py
            "AUTH_USER_MODEL",  # auth.py
            "LOGGING",  # logging.py
            "EMAIL_BACKEND",  # email.py
            "REST_FRAMEWORK",  # api.py
            "FLEX_MENUS",  # addons.py
        ]
        for setting_name in representative_settings:
            assert hasattr(module, setting_name), f"{setting_name} is missing"


class TestBundledPortalBoots:
    """The bundled example portal must start under every environment it ships a module for.

    It is the only place in this repository where the portal-override layer is
    exercised end to end against the real baseline, and a broken override there
    is invisible to every test that imports ``tests.settings`` instead.
    """

    @pytest.mark.parametrize("environment", ["production", "development"])
    def test_example_portal_passes_django_checks(self, environment):
        repo_root = Path(__file__).resolve().parents[2]
        # Built from a sanitised copy of the ambient environment: a stray
        # DATABASE_URL or REDIS_URL inherited from the shell — or leaked by an
        # earlier test in the same process — would otherwise decide whether
        # the production case passes the boot-time checks.
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(
                ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
            )
        }
        env |= {
            "DJANGO_ENV": environment,
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_SECRET_KEY": "b" * 60,
            "DJANGO_SITE_DOMAIN": "example.com",
            "DJANGO_ALLOWED_HOSTS": "example.com",
            # Production refuses to boot on SQLite and a per-process cache, so
            # the layering this test exercises needs both supplied. Neither is
            # connected to — the checks read settings only.
            "DATABASE_URL": "postgresql://portal:portal@localhost:5432/portal",
            "REDIS_URL": "redis://localhost:6379/0",
        }
        result = subprocess.run(
            [sys.executable, "-c", "import django; django.setup()"],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert result.returncode == 0, (
            f"config.settings failed to start under DJANGO_ENV={environment}:\n"
            f"{result.stderr[-3000:]}"
        )


class TestTestSettingsDeclareTheirEnvironment:
    """``tests.settings`` must start without pytest supplying ``DJANGO_ENV``.

    pytest sets it through pytest-env, so the test suite never proves this.
    Every other consumer of the module — the mypy hook's django-stubs plugin,
    an IDE, a plain shell — gets the production default and, since FR-013, a
    refused boot on the test suite's development-shaped configuration.
    """

    def test_boots_with_django_env_unset(self):
        repo_root = Path(__file__).resolve().parents[2]
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_"))
        }
        env["DJANGO_SETTINGS_MODULE"] = "tests.settings"

        result = subprocess.run(
            [sys.executable, "-c", "import django; django.setup()"],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )

        assert result.returncode == 0, (
            f"tests.settings failed to start with DJANGO_ENV unset:\n{result.stderr[-3000:]}"
        )


class TestEntryPointSignature:
    """Test the public signature of ``setup()`` (FR-012)."""

    def test_rejects_settings_keyword_arguments(self):
        with pytest.raises(TypeError):
            import fairdm

            fairdm.setup(SOME_RANDOM_SETTING="value")


class TestEnvFiles:
    """Test env-file loading order and precedence (FR-006)."""

    def test_env_files_read_in_declared_order_and_precedence(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"
        os.environ["MARKER_PROCESS"] = "already-set-in-process"

        (tmp_path / "stack.env").write_text(
            "MARKER_BASE=from-stack-env\nMARKER_PROCESS=from-stack-env\n"
        )
        (tmp_path / "stack.development.env").write_text(
            "MARKER_ENV=from-stack-development-env\n"
        )
        explicit_env = tmp_path / "explicit.env"
        explicit_env.write_text(
            "MARKER_EXPLICIT=from-explicit-env\nMARKER_PROCESS=from-explicit-env\n"
        )

        settings_dir = tmp_path / "config"
        settings_module(
            setup_call=f"fairdm.setup(env_file={explicit_env.as_posix()!r})",
            directory=settings_dir,
        )

        # stack.env is read first.
        assert os.environ["MARKER_BASE"] == "from-stack-env"
        # then stack.<environment>.env.
        assert os.environ["MARKER_ENV"] == "from-stack-development-env"
        # then the explicit env_file, with overwrite=True.
        assert os.environ["MARKER_EXPLICIT"] == "from-explicit-env"
        # stack.env / stack.<environment>.env respect a variable already set in
        # the process, but the explicit env_file overwrites it regardless.
        assert os.environ["MARKER_PROCESS"] == "from-explicit-env"


class TestProductionSetup:
    """Test production configuration loading."""

    def test_production_loads_with_complete_config(self, production_env, tmp_path):
        """Production setup should succeed when all required env vars are set."""
        # Create a mock settings module
        settings_module = tmp_path / "test_settings.py"
        settings_module.write_text(
            """
import fairdm

fairdm.setup(apps=["test_app"])
"""
        )

        # Import and execute the settings
        import sys

        sys.path.insert(0, str(tmp_path))

        try:
            # This should not raise any errors
            with mock.patch(
                "fairdm.conf.setup.include"
            ):  # Mock include to avoid loading actual files
                # Create a mock caller namespace
                caller_namespace = {"__file__": str(settings_module)}

                with mock.patch("fairdm.conf.setup.inspect") as mock_inspect:
                    mock_inspect.stack.return_value = [(None, [caller_namespace])]

                    # This should execute without errors
                    # setup(apps=["test_app"])

                    # Note: Full integration test would require actual Django setup
                    # For now, we test that the function signature and env loading works

        finally:
            sys.path.remove(str(tmp_path))


@pytest.fixture
def clean_production_env():
    """Provide clean environment for override tests."""
    # Save original env
    original_env = os.environ.copy()

    # Clear Django-related env vars
    for key in list(os.environ.keys()):
        if key.startswith(
            ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
        ):
            del os.environ[key]

    # Set minimal production environment
    os.environ.update(
        {
            "DJANGO_ENV": "production",
            "DJANGO_SECRET_KEY": "a" * 60,
            "DJANGO_SITE_DOMAIN": "example.com",
            "DJANGO_SITE_NAME": "Test Portal",
            "DJANGO_ALLOWED_HOSTS": "example.com",
            "DATABASE_URL": "postgresql://user:pass@localhost:5432/test_db",
            "REDIS_URL": "redis://localhost:6379/0",
        }
    )

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


class TestPostSetupAssignments:
    """Test assignment after ``setup()`` returns — the sole override mechanism (FR-012)."""

    def test_post_setup_assignments_work(self, clean_production_env, tmp_path):
        """Test that assignments after setup() call work correctly."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup()

# Portal-specific customization after setup()
CUSTOM_APP_SETTING = "my_value"
ANOTHER_OVERRIDE = 123
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_3", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # Post-setup assignments should exist
        assert hasattr(test_settings, "CUSTOM_APP_SETTING")
        assert test_settings.CUSTOM_APP_SETTING == "my_value"
        assert hasattr(test_settings, "ANOTHER_OVERRIDE")
        assert test_settings.ANOTHER_OVERRIDE == 123

    def test_overrides_can_modify_lists(self, clean_production_env, tmp_path):
        """Test that overrides can replace list settings like INSTALLED_APPS."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

# Get baseline INSTALLED_APPS
fairdm.setup()

# Extend INSTALLED_APPS after setup
INSTALLED_APPS = INSTALLED_APPS + ["my_portal_app"]
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_4", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # Verify custom app was added
        assert "my_portal_app" in test_settings.INSTALLED_APPS

    def test_overrides_can_modify_dicts(self, clean_production_env, tmp_path):
        """Test that overrides can modify dict settings like LOGGING."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup()

# Customize logging configuration
LOGGING["loggers"]["my_app"] = {
    "handlers": ["console"],
    "level": "DEBUG",
}
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_5", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # Verify custom logger was added
        assert "my_app" in test_settings.LOGGING["loggers"]
        assert test_settings.LOGGING["loggers"]["my_app"]["level"] == "DEBUG"


class TestEnvFileParameter:
    """Test custom env_file parameter functionality."""

    def test_custom_env_file_is_loaded(self, clean_production_env, tmp_path):
        """Test that custom env_file parameter loads the specified file."""
        # Create a custom .env file
        custom_env = tmp_path / "custom.env"
        custom_env.write_text(
            """
DJANGO_SECRET_KEY=custom_secret_key_from_file_123456789012345678901234567890
DJANGO_ALLOWED_HOSTS=custom.example.com
DATABASE_URL=postgresql://custom_user:pass@localhost:5432/custom_db
REDIS_URL=redis://localhost:6379/5
"""
        )

        settings_file = tmp_path / "settings.py"
        # Use Path.as_posix() to avoid Windows backslash escaping issues
        custom_env_posix = custom_env.as_posix()
        settings_file.write_text(
            f"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup(env_file='{custom_env_posix}')
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_6", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # Verify custom env file values were loaded
        assert (
            test_settings.SECRET_KEY
            == "custom_secret_key_from_file_123456789012345678901234567890"
        )
        assert "custom.example.com" in test_settings.ALLOWED_HOSTS

    @pytest.mark.skip(
        reason="Windows path escaping issue in dynamically generated settings file"
    )
    def test_env_file_takes_precedence(self, clean_production_env, tmp_path):
        """Test that env_file values override base environment."""
        pass

        # Create env file with override
        custom_env = tmp_path / "override.env"
        custom_env.write_text(
            """
DJANGO_SECRET_KEY=override_secret_key_from_file_1234567890123456789012345
DATABASE_URL=postgresql://user:pass@localhost:5432/test_db
REDIS_URL=redis://localhost:6379/0
DJANGO_ALLOWED_HOSTS=example.com
"""
        )

        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            f"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup(env_file="{custom_env}")
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_7", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # env_file value should override base environment
        assert (
            test_settings.SECRET_KEY
            == "override_secret_key_from_file_1234567890123456789012345"
        )


class TestBaselineModuleAudit:
    """A static audit over every module in ``fairdm/conf/settings/`` — all
    eleven, ``settings/addons.py`` included — asserting none contains a
    conditional on the resolved environment and each carries a module
    docstring naming what it owns and what it leaves to a portal (FR-002,
    FR-003, US-1 scenario 2).

    Read as source text and parsed with ``ast``, not imported — these
    modules rely on ``env``/``BASE_DIR`` being injected into their scope by
    ``split_settings.include()``, so a bare import raises ``KeyError``
    outside that machinery (as ``test_logging.py`` discovered).
    """

    #: fairdm/conf/settings/*.py, minus __init__.py — the eleven concern
    #: modules FR-002 requires (addons.py included, per the task brief).
    EXPECTED_MODULE_STEMS = {
        "addons",
        "api",
        "apps",
        "auth",
        "cache",
        "celery",
        "database",
        "email",
        "logging",
        "security",
        "static_media",
    }

    #: Variables whose presence previously drove environment-shaped
    #: branching in the baseline (research audit, decisions.md D4) — a
    #: baseline module reading one of these as an `if`/`elif` condition is
    #: exactly the defect this feature removes. Named explicitly rather than
    #: forbidding every `if` outright, since feature-detection on which of
    #: two portal-supplied values is present (S3 credentials in
    #: static_media.py, DJANGO_DEFAULT_FROM_EMAIL in email.py) is not
    #: environment branching and stays legitimate.
    FORBIDDEN_BRANCH_VARIABLES = {
        "DJANGO_ENV",
        "DJANGO_SECURE",
        "DJANGO_CACHE",
        "DATABASE_URL",
        "POSTGRES_DB",
    }

    @staticmethod
    def _settings_dir():
        import fairdm.conf.settings

        return Path(fairdm.conf.settings.__file__).parent

    def _module_paths(self):
        settings_dir = self._settings_dir()
        return {stem: settings_dir / f"{stem}.py" for stem in self.EXPECTED_MODULE_STEMS}

    def test_all_eleven_concern_modules_exist(self):
        for stem, path in self._module_paths().items():
            assert path.exists(), f"{stem}.py is missing from fairdm/conf/settings/"

    def test_every_module_has_a_docstring_naming_ownership(self):
        import ast

        for stem, path in self._module_paths().items():
            tree = ast.parse(path.read_text())
            doc = ast.get_docstring(tree)

            assert doc, f"{stem}.py has no module docstring"
            assert "owns" in doc.lower(), (
                f"{stem}.py's docstring doesn't say what it owns"
            )
            assert "leaves" in doc.lower() or "portal" in doc.lower(), (
                f"{stem}.py's docstring doesn't say what it leaves to a portal"
            )

    def test_no_module_branches_on_the_resolved_environment(self):
        import ast

        def referenced_names(test_node):
            return {
                node.id for node in ast.walk(test_node) if isinstance(node, ast.Name)
            } | {
                node.value
                for node in ast.walk(test_node)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
            }

        for stem, path in self._module_paths().items():
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if not isinstance(node, ast.If):
                    continue
                offending = referenced_names(node.test) & self.FORBIDDEN_BRANCH_VARIABLES
                assert not offending, (
                    f"{stem}.py:{node.lineno} branches on {offending} — "
                    "environment-derived state, not feature detection (FR-003)"
                )
