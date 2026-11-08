# How to change who can open the control room

Every portal comes with the Django Control Room dashboard in its administration interface, with panels for Redis, the cache and Celery. This guide changes who may open it, turns on Redis editing, and removes the dashboard. For what the dashboard shows, see [How to check the portal's services in the control room](../../administrators/how-to/check-the-portals-services-in-the-control-room.md).

By default only superusers can open it, the Redis panel is read-only, the agent interface is off, and nothing leaves the portal. A superuser whose staff flag is cleared is refused, because the panels require both. Every control-room panel package installed in the environment appears on the dashboard, including ones you add yourself.

Each package reads its own settings dictionary. The names are in [Settings](../reference/settings.md#operations-dashboard). Assign a dictionary in your settings module after `fairdm.setup()`, as described in [How to override a FairDM setting](override-a-fairdm-setting.md). Assigning a dictionary replaces FairDM's whole dictionary, so repeat `REQUIRE_SUPERUSER` and, for Redis, `INSTANCES`.

## Let a group open one panel

1. Replace `REQUIRE_SUPERUSER` with `ALLOWED_GROUPS` for that panel. Members of the named groups may open it if their account is also marked as staff. Holding a portal role does not make an account staff, so a role holder who is not staff is still refused. Superusers always can.

   ```python
   # settings.py, after fairdm.setup()
   DJ_CACHE_PANEL_SETTINGS = {
       "REQUIRE_SUPERUSER": False,
       "ALLOWED_GROUPS": ["Portal Administrator"],
   }
   ```

2. Leave `DJ_CONTROL_ROOM_SETTINGS` as it is. The dashboard itself stays limited to superusers, and the group opens the panel at its own address.

## Turn on Redis editing

1. Add a `features` dictionary to the Redis instance. Turn on only what you need.

   ```python
   DJ_REDIS_PANEL_SETTINGS = {
       "REQUIRE_SUPERUSER": True,
       "INSTANCES": {
           "default": {
               "url": CACHES["default"]["LOCATION"],
               "features": {
                   "ALLOW_KEY_EDIT": True,
                   "ALLOW_KEY_DELETE": False,
                   "ALLOW_TTL_UPDATE": False,
               },
           }
       },
   }
   ```

Editing the Redis database changes the cache and the background-task queue under a running portal.

## Remove the dashboard

1. Take the control-room apps out of `INSTALLED_APPS`. The routes go with them. In development, take out the URL and signal panels too, if they are installed.

   ```python
   CONTROL_ROOM_APPS = {
       "dj_control_room_base",
       "dj_redis_panel",
       "dj_cache_panel",
       "dj_celery_panel",
       "dj_control_room",
       "dj_urls_panel",
       "dj_signals_panel",
   }
   INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in CONTROL_ROOM_APPS]
   ```

## Add the URL and signal panels in development

Two more panels, one listing every URL pattern and one listing every Django signal and its receivers, are available while `DJANGO_ENV=development`. They open under the same rule as the others: superusers only.

1. Add both packages to your project's development dependencies, not its main ones.

   ```toml
   # pyproject.toml
   [dependency-groups]
   dev = [
       "dj-urls-panel>=0.5,<1",
       "dj-signals-panel>=0.6,<1",
   ]
   ```

2. Install the group and start the portal with `DJANGO_ENV=development`. The development settings add each panel ahead of the dashboard if its package is importable, so a portal that has not installed one simply goes without it.
3. Open the dashboard in the administration interface. Both panels now appear beside the others.

Do not add either package to `[project].dependencies`, and do not select the `urls` or `signals` extras of `dj-control-room` there. Both panels reveal how the portal is wired, and they belong on a developer's machine, never on a deployed portal. A portal that installs neither package, or runs under any other `DJANGO_ENV`, has no such routes: their addresses answer 404.

The URL panel can send a request to any pattern it lists. FairDM turns that off with `ENABLE_TESTING` set to `False` in `DJ_URLS_PANEL_SETTINGS`, because the request runs on the server with the signed-in superuser's session. The panel still lists and describes the patterns, and its request endpoint answers 403. Turn it on only in a development settings module of your own, after `fairdm.setup()`, and repeat `REQUIRE_SUPERUSER` when you replace the dictionary.

## Why the agent interface stays off

The package can offer an interface through which an AI agent calls the panels' tools. It is off unless `DJ_CONTROL_ROOM_SETTINGS` sets `MCP_ENABLED`, a token and a user name. Turning it on lets whoever holds the token read everything the panels show, including task arguments, as the named user. FairDM sets none of these.
