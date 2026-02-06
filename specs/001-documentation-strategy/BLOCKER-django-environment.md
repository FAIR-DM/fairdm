# Django Environment Blocker for Documentation Builds

**Issue**: Sphinx documentation builds fail due to Django import error
**Created**: 2026-01-07
**Status**: Blocking T011-T012 in Phase 2

## Error Summary

```
ImportError: cannot import name 'AppMenu' from 'mvp.menus'
(C:\Users\jennings\Documents\repos\django-mvp\mvp\menus.py)
```

**Location**: `fairdm/menus/menus.py:5`

```python
from mvp.menus import AppMenu
```

## Root Cause

The FairDM documentation build depends on Django setup (`docs/conf.py` imports Django settings and calls `django.setup()`). During Django app initialization, `fairdm.apps.FairdmConfig.ready()` calls `autodiscover_modules("plugins")`, which triggers imports of all plugin modules, including `fairdm/menus/menus.py`.

This module tries to import `AppMenu` from `mvp.menus`, but that import fails, likely because:

1. `django-mvp` is a local development package not installed in the environment
2. The `mvp.menus` module doesn't export `AppMenu`
3. There's a version mismatch between what FairDM expects and what's installed

## Impact

- **T011**: Cannot test documentation build with strict validation
- **T012**: Cannot test linkcheck functionality
- All Sphinx builds fail (html, linkcheck, etc.)

## Workaround Options

### Option 1: Fix the mvp import (Recommended)

Check if `django-mvp` is properly installed and has the expected API:

```powershell
poetry show django-mvp
# or
poetry run python -c "from mvp.menus import AppMenu; print(AppMenu)"
```

If missing, install or update:

```powershell
poetry add git+https://github.com/path/to/django-mvp.git
```

If API changed, update `fairdm/menus/menus.py` to match current API.

### Option 2: Make import optional

Modify `fairdm/menus/menus.py` to gracefully handle missing mvp:

```python
try:
    from mvp.menus import AppMenu
except ImportError:
    # Provide a fallback for documentation builds
    from flex_menu import Menu
    AppMenu = Menu("main")
```

### Option 3: Skip menu initialization during docs build

Modify `fairdm/apps.py` to skip autodiscover when building docs:

```python
def ready(self):
    # Skip plugin discovery during documentation builds
    if os.environ.get("SPHINX_BUILD"):
        return
    autodiscover_modules("plugins")
```

Then set `SPHINX_BUILD=1` in `docs/conf.py`.

### Option 4: Use DJANGO_SETTINGS_MODULE that disables menus

Create a minimal `docs/settings.py` that doesn't include menu-related apps:

```python
from tests.settings import *

INSTALLED_APPS = [app for app in INSTALLED_APPS if 'menu' not in app.lower()]
```

Update `docs/conf.py`:

```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "docs.settings")
```

## Next Steps

1. Investigate which option is most appropriate
2. Implement fix
3. Re-run T011 and T012
4. Complete Phase 2 validation

## Related Tasks

- T011: Test documentation build with strict validation
- T012: Test linkcheck functionality
- Phase 2: Foundational Infrastructure (blocked)

## Notes

This issue surfaced during Phase 2 implementation when attempting to run Sphinx builds. The validation scripts (T003-T005) and tests (T008) are complete and working - only the actual Sphinx build is blocked.
