# API Contract: fairdm.conf

## `fairdm.setup()`

The primary entry point for configuring a FairDM portal.

```python
def setup(
    addons: list[str] | None = None,
    env_file: str | Path | None = None,
    **overrides
) -> None:
    """
    Initialize FairDM configuration.

    Args:
        addons: List of addon package names to enable.
        env_file: Path to .env file (optional).
        **overrides: Additional settings to apply immediately (though explicit overrides
                     after this call are preferred).
    """
```

## Addon Protocol

Addons must adhere to this protocol to be configurable via `fairdm.setup()`.

```python
# In addon/__init__.py
__fdm_setup_module__ = "my_addon.conf"

# In addon/conf.py
INSTALLED_APPS = ["my_addon"]
MIDDLEWARE = ["my_addon.middleware.MyMiddleware"]
MY_ADDON_SETTING = "default"
```
