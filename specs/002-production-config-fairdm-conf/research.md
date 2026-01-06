# Research: Production-Ready Configuration

> ⚠️ **Architecture Note**: This research document contains exploration of various approaches, some of which were later refined or rejected. The "Split-Settings Inheritance" section below discusses profile inheritance patterns that were ultimately NOT adopted. See `spec.md` "Architecture Clarification" session (2026-01-02) for the final architecture decisions where `fairdm/conf/settings/*` modules ARE the production baseline (no inheritance), with thin environment overlay files (`local.py`, `staging.py`) applied via `fairdm.setup()` orchestration.

## Unknowns & Questions

1. **Split-Settings Inheritance**: How to structure `django-split-settings` so `development` imports `production` which imports `base`, without circular deps or double-loading issues?
2. **Fail-Fast Implementation**: What is the cleanest pattern to implement "fail-fast in Prod, degrade in Dev" for backing services?
3. **Addon Configuration**: How to parse complex addon configurations (e.g., list of dicts) from environment variables using `django-environ`?

## Findings

### 1. Split-Settings Inheritance

*   **Decision**: Use standard Python imports for profiles. `production.py` imports `base.py` symbols or uses `include()`. `development.py` imports `production.py` symbols or uses `include()`.
*   **Rationale**: `django-split-settings` `include()` function is designed for this. We can do `include('base.py')` in `production.py`, and `include('production.py')` in `development.py`.
*   **Alternatives**:
    *   Standard Python `from .production import *`. This is brittle with `split-settings` if we want to use the `include` features for context.
    *   `include()` is safer as it manages the scope.

### 2. Fail-Fast Implementation

*   **Decision**: Create a `validate_services(env_profile: str)` function in `checks.py`.
*   **Rationale**: This function will be called at the end of `setup()`. It will check `DJANGO_ENV`. If `production` or `staging`, it raises `ImproperlyConfigured` on connection errors. If `development`, it logs a warning and maybe sets a dummy backend (e.g., dummy cache).
*   **Alternatives**:
    *   Check inside `settings.py` directly. Messy.
    *   Check in `AppConfig.ready()`. Too late for some settings that are needed at import time (though DB/Cache connections are usually runtime). Actually, `AppConfig.ready()` is better for connection checks, but `settings.py` is better for *configuration* checks (e.g. is the URL set?).
    *   **Refinement**: We will check for *presence* of config in `setup()`. We will check for *connectivity* in `AppConfig.ready()` or a pre-flight check script. The spec says "fail fast ... when required backing services are missing/unreachable". "Unreachable" implies connectivity. Doing this in `settings.py` might slow down CLI commands.
    *   **Refinement 2**: The spec says "startup". We should probably check config presence in `settings.py` and connectivity in a system check (Django System Check framework).
    *   **Decision Update**: Use Django System Checks for connectivity. Use `setup()` for config presence (missing env vars).
    *   **Wait**: Spec says "fail fast ... when required backing services are missing/unreachable". If I use System Checks, it happens after settings are loaded. This is fine.
    *   **However**: For "degrade in development", if the config is missing, we need to set a default (e.g. LocMemCache) *during* settings load. So we need logic in `settings.py` (via `setup()`) to decide: "Is REDIS_URL set? No? If Dev, use LocMem. If Prod, raise Error."

### 3. Addon Configuration

*   **Decision**: Use `django-environ`'s `json` parser for complex structures, or a custom parser for comma-separated lists if simple.
*   **Rationale**: `env.json()` allows passing a JSON string in an env var. This is standard.
*   **Alternatives**:
    *   Separate env vars for each addon: `ADDON_X_ENABLED=true`. Hard to iterate.
    *   `ADDONS=addon1,addon2`. Simple list. Configuration for addons can be separate env vars `ADDON1_SETTING=...`. This is cleaner than a big JSON blob.
    *   **Decision Update**: `ADDONS` env var is a comma-separated list of addon names (or module paths). Each addon then reads its own specific env vars. This decouples the config.
