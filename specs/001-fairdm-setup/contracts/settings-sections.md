# Contract: Settings Sections Layout (fairdm.conf)

**Feature**: specs/002-production-config-fairdm-conf/spec.md
**Date**: 2026-01-02

This contract defines the responsibilities and boundaries of the FairDM configuration sections.

## Canonical section location

- Baseline settings sections live under the FairDM package:
  - `fairdm/conf/settings/*.py`

In user-facing documentation, these may be described as “sections”. If the directory is renamed (e.g., `sections/`), the contract is that FairDM provides a **stable categorized sections surface** and `fairdm.setup()` composes them.

## Responsibility boundaries

FairDM-owned (baseline):

- Environment schema and parsing (`fairdm/conf/environment.py`)
- Default URL configuration (`fairdm/conf/urls.py`)
- Static/media defaults (including reference WhiteNoise/static pipeline integration)
- Database/cache defaults and production-safe patterns
- Background processing defaults (Celery + broker/result backend configuration)
- Authentication/authorization baseline (where core depends on it)
- Addon configuration loading and URL discovery mechanisms

Project-owned (override layer):

- Portal branding and copy
- Domain app models and registration wiring (Sample/Measurement extensions)
- Optional portal-specific installed apps not covered by FairDM baseline
- Custom feature flags and portal-only settings

## Loading order

The baseline loading order MUST be stable and documented. High-level intent:

1. Environment schema is loaded and `env` is available
2. General/base settings load
3. Remaining categorized sections load
4. Environment profile overrides apply (development/staging)
5. Addon settings modules load

## Section import rules (consistency)

### Environment access

- Settings sections MUST NOT create their own `Env(...)` / environment schema.
- When a section needs environment values, it MUST import the shared env instance:

```python
from fairdm.conf.environment import env
```

This ensures a single source of truth for defaults and supported variables.

### Cross-section settings access

- Settings sections SHOULD NOT re-declare shared settings structures (for example, `STORAGES`) if a canonical section already defines them.
- When practical and safe (i.e., no circular imports and no reliance on caller-only globals), sections MAY import shared values from the canonical section module and then extend them.

Example:

```python
from fairdm.conf.settings.file_storage import STORAGES

STORAGES["default"].update({
  # project-specific additions
})
```

If a section relies on values that are only available during `fairdm.setup()` (e.g. `BASE_DIR` set into the caller globals), it should continue to use those runtime-provided values rather than importing the section module outside of setup.
