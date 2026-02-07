# Contract: Python API & Addon Integration (fairdm.setup)

**Feature**: specs/002-production-config-fairdm-conf/spec.md
**Date**: 2026-01-02

This contract defines the stable Python integration points for portal projects and addons.

## Portal Integration: `fairdm.setup(...)`

### Signature (conceptual)

- `fairdm.setup(apps: list[str] = [], addons: list[str] = [], base_dir: Path | None = None) -> None`

### Required behavior

- MUST populate the caller settings module global namespace with FairDM baseline settings.
- MUST select an environment profile based on `DJANGO_ENV`.
- MUST load environment variables through `fairdm/conf/environment.py`.
- MUST include all baseline settings sections required for a production-ready portal.
- MUST accept `apps` as portal-provided apps to be integrated into `INSTALLED_APPS` via baseline configuration.
- MUST accept `addons` as optional addon packages to be enabled.

## Addon Integration

### Addon settings module

An addon package MUST define:

- `__fdm_setup_module__`: a Python import path to a module file containing settings contributions.

Example:

- `__fdm_setup_module__ = "my_addon.fairdm_setup"`

### Addon URLs (optional)

If the addon provides a `<addon>.urls` module:

- FairDM MUST discover it and include it into the portal URL configuration.

## Compatibility notes

- Addon configuration should not require portal maintainers to manually edit many settings lists.
- If an addon does not define `__fdm_setup_module__`, FairDM will skip it and warn.
