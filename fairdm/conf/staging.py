"""
Staging configuration overrides.

This file overrides the production baseline for staging environments.
Applied after loading settings/* modules when DJANGO_ENV=staging.
Staging is production-like but may have enhanced logging or relaxed constraints.
"""

# =============================================================================
# STAGING-SPECIFIC OVERRIDES
# =============================================================================

# More verbose logging for staging environments
LOGGING = globals().get("LOGGING", {})
if "root" in LOGGING:
    LOGGING["root"]["level"] = "DEBUG"
if "loggers" in LOGGING:
    if "fairdm" in LOGGING["loggers"]:
        LOGGING["loggers"]["fairdm"]["level"] = "DEBUG"
    if "django" in LOGGING["loggers"]:
        LOGGING["loggers"]["django"]["level"] = "DEBUG"

# Allow Sentry to be optional in staging
env = globals()["env"]
SENTRY_DSN = env("SENTRY_DSN", default="")
