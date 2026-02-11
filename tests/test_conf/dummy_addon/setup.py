"""
Setup module for dummy_addon.

This module is imported by fairdm.setup() when dummy_addon is included
in the addons list. It demonstrates how addons can inject settings.
"""

# Inject custom settings
DUMMY_ADDON_INSTALLED = True
DUMMY_ADDON_VERSION = "1.0.0"

# Add a custom app to INSTALLED_APPS
INSTALLED_APPS = [*INSTALLED_APPS, "tests.test_conf.dummy_addon"]

# Add custom middleware
MIDDLEWARE = [*MIDDLEWARE, "tests.test_conf.dummy_addon.middleware.DummyMiddleware"]

# Add custom logging configuration
if "loggers" not in LOGGING:
    LOGGING["loggers"] = {}

LOGGING["loggers"]["dummy_addon"] = {
    "handlers": ["console"],
    "level": "INFO",
    "propagate": False,
}
