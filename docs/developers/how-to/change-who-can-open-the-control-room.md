# How to change who can open the control room

Every portal comes with the Django Control Room dashboard in its administration interface, with panels for Redis, the cache and Celery. This guide changes who may open it, turns on Redis editing, and removes the dashboard. For what the dashboard shows, see [How to check the portal's services in the control room](../../administrators/how-to/check-the-portals-services-in-the-control-room.md).

By default only superusers can open it, the Redis panel is read-only, the agent interface is off, and nothing leaves the portal. A superuser whose staff flag is cleared is refused, because the panels require both. Every control-room panel package installed in the environment appears on the dashboard, including ones you add yourself.

Each package reads its own settings dictionary. The names are in [Settings](../reference/settings.md#operations-dashboard). Assign a dictionary in your settings module after `fairdm.setup()`, as described in [How to override a FairDM setting](override-a-fairdm-setting.md). Assigning a dictionary replaces FairDM's whole dictionary, so repeat `REQUIRE_SUPERUSER` and, for Redis, `INSTANCES`.

## Let a group open one panel

1. Replace `REQUIRE_SUPERUSER` with `ALLOWED_GROUPS` for that panel. Members of the named groups, who must also be staff, may open it. Superusers always can.

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

1. Take the five control-room apps out of `INSTALLED_APPS`. The routes go with them.

   ```python
   CONTROL_ROOM_APPS = {
       "dj_control_room_base",
       "dj_redis_panel",
       "dj_cache_panel",
       "dj_celery_panel",
       "dj_control_room",
   }
   INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in CONTROL_ROOM_APPS]
   ```

## Why the agent interface stays off

The package can offer an interface through which an AI agent calls the panels' tools. It is off unless `DJ_CONTROL_ROOM_SETTINGS` sets `MCP_ENABLED`, a token and a user name. Turning it on lets whoever holds the token read everything the panels show, including task arguments, as the named user. FairDM sets none of these.
