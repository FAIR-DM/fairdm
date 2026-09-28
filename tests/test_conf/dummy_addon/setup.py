"""Setup module for dummy_addon."""

DUMMY_ADDON_INSTALLED = True
DUMMY_ADDON_VERSION = "1.0.0"

INSTALLED_APPS = [*INSTALLED_APPS, "tests.test_conf.dummy_addon"]

MIDDLEWARE = [*MIDDLEWARE, "tests.test_conf.dummy_addon.middleware.DummyMiddleware"]

if "loggers" not in LOGGING:
    LOGGING["loggers"] = {}

LOGGING["loggers"]["dummy_addon"] = {
    "handlers": ["console"],
    "level": "INFO",
    "propagate": False,
}
