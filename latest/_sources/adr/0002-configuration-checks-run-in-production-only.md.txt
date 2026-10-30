# ADR 0002 — Configuration checks run automatically in production, and nowhere else

**Status:** accepted

## Decision

The production-critical configuration checks — a production-grade database, a shared cache, a secret
key that is neither absent nor insecure, a non-empty and non-wildcarded allowed-hosts list, and debug
off — run automatically whenever the settings in force are the production baseline, and prevent the
process starting if any fails. Every failure is reported in one message rather than stopping at the
first.

The gate is the settings that were composed, not an exact match on the name `production`. Layer
selection is by file existence (ADR 0001), so `Production`, `prod` and the empty string all load no
override and run on the production baseline — they are production deployments and are checked as
such. **The exemption is narrow: an environment FairDM ships a non-production override module for,
which today means `development` alone.** The full check set, including the recommendations outside
the production-critical subset, stays available on demand through `manage.py check --deploy`, which
assesses against production standards whatever the current environment.

The checks execute from `FairDMConfig.ready()`, not from `fairdm.setup()`. `setup()` runs inside the
settings module, before `django.setup()` has populated the app registry, so the check framework does
not exist yet at the point the entry point returns. `ready()` is the first moment in the boot at
which it does, and raising there stops a server and every management command alike.

There is exactly one configuration-validation path. The previous `validate_services()` function is
deleted rather than deprecated.

## Why

FairDM ran validation on every start in January 2026, found it was noise, and switched it off
entirely — the commit says so: *"Configuration validation no longer runs automatically during
setup"*, alongside *"Changed runtime logging to debug level to reduce development noise"*. The
diagnosis was right and the remedy overshot. The checks were noise **in development**, where they
have nothing useful to say about a machine nobody is deploying. They were never noise in production.

What the intervening months cost is measurable. `settings/database.py` falls back to SQLite when no
database is configured, at debug log level, under a comment reading *"Production will fail validation
if this path is taken"* — naming a validation that had stopped running. `settings/cache.py` degrades
to a local-memory cache the same way. A production portal missing both variables started cleanly on
SQLite and an in-process cache, and said nothing.

Celery is deliberately outside the production-critical subset. A portal may legitimately run without
a worker, and a guard that blocks a boot for a reason operators consider wrong is a guard they learn
to route around.

Keying the exemption on the name `production` rather than on the composed settings is a mistake this
decision made once and corrected: a portal set to `Production` or to an empty string got the strict
baseline from the layering and then skipped every check on it, booting with no secret key and no
database. The two mechanisms have to agree on what "production" means, and file existence is the one
that already decides it.

The consequence to accept: a production box whose configuration is broken cannot run *any* management
command until it is fixed, including `check --deploy` itself. That is what fail-fast means, and the
remedy is always to set the missing variable.

## Revisit if

A deployment target needs to boot into a degraded but running state to be repaired — a recovery mode,
or a platform whose health check must answer before configuration is complete. That is a real
requirement this decision does not serve, and it would need an explicit, narrow escape rather than a
softening of the default.
