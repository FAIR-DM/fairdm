"""Tests for FairDM configuration setup and environment loading."""

import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest


@pytest.fixture
def clean_env():
    original_env = os.environ.copy()
    for key in list(os.environ.keys()):
        if key.startswith(("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_")):
            del os.environ[key]

    yield

    os.environ.clear()
    os.environ.update(original_env)


class TestResolvedEnvironment:
    def test_missing_django_env_resolves_to_production(
        self, clean_env, settings_module
    ):
        module = settings_module()

        assert module.DJANGO_ENV == "production"

    def test_empty_string_django_env_is_looked_up_literally(
        self, clean_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = ""

        module = settings_module()

        assert module.DJANGO_ENV == ""
        assert module.DEBUG is False

    def test_environment_name_differing_only_in_case_is_not_normalised(
        self, clean_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "Development"

        module = settings_module()

        assert module.DJANGO_ENV == "Development"
        assert module.DEBUG is False


class TestLayerOrder:
    def test_layers_apply_in_declared_order(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"
        (tmp_path / "development.py").write_text("PORTAL_OVERRIDE_MARKER = 'portal'\n")

        module = settings_module(
            setup_call="fairdm.setup(addons=['tests.test_conf.dummy_addon'])",
            after="POST_CALL_MARKER = 'post'",
            directory=tmp_path,
        )

        assert module.SESSION_COOKIE_HTTPONLY is True
        assert module.DEBUG is True
        assert module.DUMMY_ADDON_INSTALLED is True
        assert module.PORTAL_OVERRIDE_MARKER == "portal"
        assert module.POST_CALL_MARKER == "post"

    def test_override_module_selected_by_existence_not_allowlist(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        (tmp_path / "qa.py").write_text("QA_OVERRIDE_MARKER = True\n")

        module = settings_module(directory=tmp_path)

        assert module.QA_OVERRIDE_MARKER is True

    def test_environment_with_no_shipped_module_resolves_to_baseline_unchanged(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module(directory=tmp_path)

        assert module.DEBUG is False

    def test_fairdm_and_portal_overrides_for_the_same_environment_both_apply(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"
        # FairDM ships development.py (sets DEBUG = True). The portal's own
        # development.py, applied after, must win.
        (tmp_path / "development.py").write_text("DEBUG = 'portal-wins'\n")

        module = settings_module(directory=tmp_path)

        assert module.DEBUG == "portal-wins"


class TestProvenance:
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
        assert "SESSION_COOKIE_HTTPONLY" in baseline.settings
        assert "DEBUG" in fairdm_override.settings
        assert "DUMMY_ADDON_INSTALLED" in addons.settings
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

        all_settings = {name for layer in record.layers() for name in layer.settings}
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
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module(directory=tmp_path)

        from fairdm.conf import record

        assert "django_browser_reload" in module.INSTALLED_APPS

        for setting in ("INSTALLED_APPS", "MIDDLEWARE"):
            producer = record.producer(setting)
            assert producer is not None, setting
            assert producer.name == "fairdm override", setting


class TestProvenanceCoversEverySetting:
    # Bookkeeping keys ``setup()`` injects itself, not settings any layer names.
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
    # Settings neither the production baseline nor development.py branches on. Resolving them
    # identically in both environments is what "layered on top of" means.
    UNCHANGED_BETWEEN_ENVIRONMENTS = ["AUTH_USER_MODEL", "TIME_ZONE", "SITE_ID"]

    def test_development_overrides_debug_and_security_settings(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module(directory=tmp_path)

        assert module.DEBUG is True
        assert module.ALLOWED_HOSTS == ["*"]
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
                (
                    "DJANGO_",
                    "DATABASE_",
                    "REDIS_",
                    "POSTGRES_",
                    "EMAIL_",
                    "S3_",
                    "SENTRY_",
                )
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
        os.environ["DJANGO_ENV"] = "qa"

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
    # The only place the portal-override layer runs end to end against the real baseline.
    @pytest.mark.parametrize("environment", ["production", "development"])
    def test_example_portal_passes_django_checks(self, environment):
        repo_root = Path(__file__).resolve().parents[2]
        # Built from a sanitised copy of the ambient environment: a stray DATABASE_URL or REDIS_URL from
        # the shell, or leaked by an earlier test, would decide whether production passes the boot checks.
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(
                (
                    "DJANGO_",
                    "DATABASE_",
                    "REDIS_",
                    "POSTGRES_",
                    "EMAIL_",
                    "S3_",
                    "SENTRY_",
                )
            )
        }
        env |= {
            "DJANGO_ENV": environment,
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_SECRET_KEY": "b" * 60,
            "DJANGO_SITE_DOMAIN": "example.com",
            "DJANGO_ALLOWED_HOSTS": "example.com",
            # Production refuses SQLite and a per-process cache, so both are supplied. Neither is connected to.
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
    # pytest-env supplies DJANGO_ENV, so the suite never proves tests.settings starts without it. The mypy
    # plugin, IDEs and plain shells get the production default.
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
    def test_rejects_settings_keyword_arguments(self):
        with pytest.raises(TypeError):
            import fairdm

            fairdm.setup(SOME_RANDOM_SETTING="value")


class TestEnvFiles:
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

        assert os.environ["MARKER_BASE"] == "from-stack-env"
        assert os.environ["MARKER_ENV"] == "from-stack-development-env"
        assert os.environ["MARKER_EXPLICIT"] == "from-explicit-env"
        # stack.env / stack.<environment>.env respect a variable already set in
        # the process, but the explicit env_file overwrites it regardless.
        assert os.environ["MARKER_PROCESS"] == "from-explicit-env"


class TestProductionSetup:
    def test_production_loads_with_complete_config(self, production_env, tmp_path):
        settings_module = tmp_path / "test_settings.py"
        settings_module.write_text(
            """
import fairdm

fairdm.setup(apps=["test_app"])
"""
        )

        import sys

        sys.path.insert(0, str(tmp_path))

        try:
            with mock.patch(
                "fairdm.conf.setup.include"
            ):  # Mock include to avoid loading actual files
                caller_namespace = {"__file__": str(settings_module)}

                with mock.patch("fairdm.conf.setup.inspect") as mock_inspect:
                    mock_inspect.stack.return_value = [(None, [caller_namespace])]

        finally:
            sys.path.remove(str(tmp_path))


@pytest.fixture
def clean_production_env():
    original_env = os.environ.copy()

    for key in list(os.environ.keys()):
        if key.startswith(
            ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
        ):
            del os.environ[key]

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

    os.environ.clear()
    os.environ.update(original_env)


class TestPostSetupAssignments:
    def test_post_setup_assignments_work(self, clean_production_env, tmp_path):
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup()

CUSTOM_APP_SETTING = "my_value"
ANOTHER_OVERRIDE = 123
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_3", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        assert hasattr(test_settings, "CUSTOM_APP_SETTING")
        assert test_settings.CUSTOM_APP_SETTING == "my_value"
        assert hasattr(test_settings, "ANOTHER_OVERRIDE")
        assert test_settings.ANOTHER_OVERRIDE == 123

    def test_overrides_can_modify_lists(self, clean_production_env, tmp_path):
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup()

INSTALLED_APPS = INSTALLED_APPS + ["my_portal_app"]
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_4", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        assert "my_portal_app" in test_settings.INSTALLED_APPS

    def test_overrides_can_modify_dicts(self, clean_production_env, tmp_path):
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup()

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

        assert "my_app" in test_settings.LOGGING["loggers"]
        assert test_settings.LOGGING["loggers"]["my_app"]["level"] == "DEBUG"


class TestPostSetupOverridesEveryBaselineModule:
    # One representative, non-composed setting per baseline module, read straight out of
    # fairdm/conf/settings/*.py (api's lives in fairdm/api/settings.py, which settings/api.py re-exports).
    SETTING_BY_MODULE = {
        "addons": "SOLO_CACHE",
        "api": "FAIRDM_API_TITLE",
        "apps": "WSGI_APPLICATION",
        "auth": "AUTH_USER_MODEL",
        "cache": "COLLECTFASTA_CACHE",
        "celery": "CELERY_TASK_SERIALIZER",
        "database": "DEFAULT_AUTO_FIELD",
        "email": "EMAIL_TIMEOUT",
        "logging": "SENTRY_LOG_LEVEL",
        "security": "SESSION_COOKIE_HTTPONLY",
        "static_media": "STATIC_URL",
    }

    # The portal's override for each is a different value, and where practical a different type, so an
    # equal-by-coincidence pass is ruled out.
    PORTAL_VALUE_BY_MODULE = {
        "addons": "portal-solo-cache",
        "api": "Portal Research API",
        "apps": "portal.wsgi.application",
        "auth": "portal.PortalUser",
        "cache": "portal-collectfasta",
        "celery": "pickle",
        "database": "django.db.models.AutoField",
        "email": 30,
        "logging": 40,
        "security": False,
        "static_media": "/portal-static/",
    }

    def test_every_baseline_module_setting_survives_post_setup_override(
        self, clean_production_env, settings_module
    ):
        assert set(self.SETTING_BY_MODULE) == {
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
        }, "must cover all eleven baseline modules, not a subset"

        baseline_module = settings_module(filename="baseline_settings.py")

        after = "\n".join(
            f"{setting} = {self.PORTAL_VALUE_BY_MODULE[stem]!r}"
            for stem, setting in self.SETTING_BY_MODULE.items()
        )
        portal_module = settings_module(after=after, filename="portal_settings.py")

        for stem, setting in self.SETTING_BY_MODULE.items():
            baseline_value = getattr(baseline_module, setting)
            portal_value = getattr(portal_module, setting)
            expected = self.PORTAL_VALUE_BY_MODULE[stem]

            assert baseline_value != expected, (
                f"{stem}.{setting}: the baseline already holds the portal's "
                "test value — pick a different override so the comparison "
                "below is meaningful"
            )
            assert portal_value == expected, (
                f"{stem}.{setting}: portal override did not survive "
                f"resolution (baseline was {baseline_value!r}, resolved to "
                f"{portal_value!r})"
            )


class TestComposedSettingsCanBeFullyRebound:
    def test_installed_apps_can_be_fully_rebound(
        self, clean_production_env, settings_module
    ):
        baseline_module = settings_module(filename="baseline_settings.py")
        assert "django.contrib.auth" in baseline_module.INSTALLED_APPS

        portal_module = settings_module(
            after='INSTALLED_APPS = ["only_this_app"]',
            filename="portal_settings.py",
        )

        assert portal_module.INSTALLED_APPS == ["only_this_app"]

    def test_logging_can_be_fully_rebound(self, clean_production_env, settings_module):
        baseline_module = settings_module(filename="baseline_settings.py")
        assert "loggers" in baseline_module.LOGGING

        portal_module = settings_module(
            after='LOGGING = {"version": 1, "disable_existing_loggers": True}',
            filename="portal_settings.py",
        )

        assert portal_module.LOGGING == {
            "version": 1,
            "disable_existing_loggers": True,
        }


class TestEnvFileParameter:
    def test_custom_env_file_is_loaded(self, clean_production_env, tmp_path):
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

        assert (
            test_settings.SECRET_KEY
            == "custom_secret_key_from_file_123456789012345678901234567890"
        )
        assert "custom.example.com" in test_settings.ALLOWED_HOSTS

    @pytest.mark.skip(
        reason="Windows path escaping issue in dynamically generated settings file"
    )
    def test_env_file_takes_precedence(self, clean_production_env, tmp_path):
        pass

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

        assert (
            test_settings.SECRET_KEY
            == "override_secret_key_from_file_1234567890123456789012345"
        )


class TestBaselineModuleAudit:
    # fairdm/conf/settings/*.py, minus __init__.py.
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

    # Variables that once drove environment-shaped branching in the baseline. Named explicitly rather
    # than forbidding every `if`: feature-detection on portal-supplied values (S3 credentials,
    # DJANGO_DEFAULT_FROM_EMAIL) stays legitimate.
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
        return {
            stem: settings_dir / f"{stem}.py" for stem in self.EXPECTED_MODULE_STEMS
        }

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
                offending = (
                    referenced_names(node.test) & self.FORBIDDEN_BRANCH_VARIABLES
                )
                assert not offending, (
                    f"{stem}.py:{node.lineno} branches on {offending} — "
                    "environment-derived state, not feature detection (FR-003)"
                )


class TestNoSecondValidationPath:
    def test_setup_is_the_only_public_export(self):
        import fairdm.conf

        assert fairdm.conf.__all__ == ["setup"]

    def test_no_validate_services_function_remains(self):
        import fairdm.conf.checks

        assert not hasattr(fairdm.conf.checks, "validate_services")
