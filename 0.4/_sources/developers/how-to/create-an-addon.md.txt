# How to create an addon

An addon is a package that adds settings, apps or middleware to any portal that names it. You create one when several portals need the same setup, so each portal enables it with one line.

## Steps

1. Create a module in your package that holds the addon's settings. The module must be a single file. FairDM runs it with the portal's settings already in scope, so you can read and extend them.

   ```python
   # my_addon/fdm_setup.py

   INSTALLED_APPS = INSTALLED_APPS + ["my_addon"]  # noqa: F821
   MIDDLEWARE = MIDDLEWARE + ["my_addon.middleware.MyMiddleware"]  # noqa: F821

   MY_ADDON_SETTING = "value"
   ```

   Do not call `fairdm.setup()` in the module. Extend a list with `+` or `+=` and change a dictionary by assigning an item, so the entries FairDM put there stay.

2. Name the module in your package's `__init__.py`.

   ```python
   # my_addon/__init__.py

   __fdm_setup_module__ = "my_addon.fdm_setup"
   ```

   The value is the dotted path of the module, not of a package.

3. Enable the addon in the portal.

   ```python
   # config/settings.py
   import fairdm

   fairdm.setup(addons=["my_addon"])
   ```

4. If the addon has URLs, include them in the portal's URLconf.

   ```python
   # config/urls.py
   from django.urls import include, path

   urlpatterns += [path("", include("my_addon.urls"))]
   ```

5. List the layers and check that FairDM applied the addon.

   ```bash
   python manage.py show_config MY_ADDON_SETTING
   ```

## The result

The command prints `MY_ADDON_SETTING = value (addons)`. The addon's settings are layer 3, so a portal can always override them in its [environment override module](add-an-environment-override-module.md) or by [assigning the setting](override-a-fairdm-setting.md) after the `fairdm.setup()` call.

FairDM applies the module to a private copy of the settings and keeps the result only when the module runs to the end, so an addon that fails leaves no half-written settings. When something goes wrong, the outcome depends on the environment. A setup module that cannot be found, or that raises, stops a production portal with an error that names the addon. In any other environment FairDM logs a warning and skips the addon. A package that cannot be imported, or that has no `__fdm_setup_module__`, is skipped in every environment with a log message. The full table is in [Configuration](../reference/configuration.md#addons).
