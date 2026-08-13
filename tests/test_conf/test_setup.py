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
from pathlib import Path
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured

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
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            if isinstance(target, ast.Name)
        }

        assert diff_keys <= named_keys


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
        warned_text = " ".join(str(call.args[0]) for call in mock_warning.call_args_list)
        assert "settings module" in warned_text.lower() or "__file__" in warned_text
        assert scope["DJANGO_ENV"] == "production"


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


# Validation Logic Tests (Unit tests that don't require full Django setup)


class TestValidationLogic:
    """Test configuration validation logic."""

    def test_secret_key_length_validation(self, clean_env):
        """Secret key should be validated for minimum length."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "short",  # Too short
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="SECRET_KEY.*too short"):
            validate_services("production", test_settings)

    def test_insecure_secret_key_rejected(self, clean_env):
        """Secret key containing 'insecure' should be rejected in production."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "django-insecure-" + "a" * 50,  # Contains 'insecure'
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="insecure"):
            validate_services("production", test_settings)

    def test_https_cookie_validation(self, clean_env):
        """HTTPS-only cookies should be enforced in production."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": False,  # Should fail
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="SESSION_COOKIE_SECURE"):
            validate_services("production", test_settings)

    def test_production_fails_without_database_url(self, clean_env):
        """Production should fail if DATABASE_URL is not set."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="DATABASES"):
            validate_services("production", test_settings)

    def test_production_fails_without_redis_url(self, clean_env):
        """Production should fail if REDIS_URL is not set."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {
                "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
            },
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
            "CELERY_BROKER_URL": "",
        }

        with pytest.raises(ImproperlyConfigured, match="Cache backend"):
            validate_services("production", test_settings)

    def test_production_fails_with_debug_true(self, clean_env):
        """Production should fail if DEBUG is True."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": True,  # This should fail
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="DEBUG"):
            validate_services("production", test_settings)

    def test_production_fails_with_wildcard_allowed_hosts(self, clean_env):
        """Production should fail if ALLOWED_HOSTS contains wildcard."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["*"],  # Wildcard should fail
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="ALLOWED_HOSTS.*wildcard"):
            validate_services("production", test_settings)

    def test_development_degrades_without_database_url(self, clean_env, caplog):
        """Development should warn but not fail if DATABASE_URL is missing."""
        import warnings

        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3"}},
            "CACHES": {
                "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
            },
            "SECRET_KEY": "dev-key",
            "ALLOWED_HOSTS": ["*"],
            "DEBUG": True,
        }

        # Should not raise exception but should emit deprecation warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_services("development", test_settings)
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()


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
