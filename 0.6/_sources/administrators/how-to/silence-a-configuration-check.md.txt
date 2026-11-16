# How to silence a configuration check

Silencing a check removes it from the report that `manage.py check` prints. You do this for a warning you have decided to accept, so that it stops hiding the problems you have not.

## Before you start

Look the check up in [Configuration checks](../reference/configuration-checks.md). A check marked as stopping a production start still runs at start-up when you silence it, so silencing it does not let the portal start.

## Steps

1. Open the portal's settings module, the one that calls `fairdm.setup()`.

2. After the `fairdm.setup()` call, add the id of the check to `SILENCED_SYSTEM_CHECKS`. Append to the list. FairDM already puts an entry in it, and assigning a new list would remove that entry.

   ```python
   SILENCED_SYSTEM_CHECKS += ["fairdm.W601"]
   ```

   Silencing a Django check works the same way, with its id, such as `security.W004`.

3. Restart the portal, then run the checks.

   ```bash
   python manage.py check --deploy
   ```

## The result

The silenced id no longer appears in the report. The command counts it only in the "silenced" total on its last line.

The check itself still runs in two places. The start-up guard runs the production-critical checks without reading `SILENCED_SYSTEM_CHECKS`, so a portal in production still stops for a failing one. The language check `fairdm.E400` is raised while the settings load and cannot be silenced at all.

Silence a check only when you understand what it protects. A silenced `fairdm.E006` leaves the cookie fault in place, and a silenced `fairdm.W601` leaves the API limits open to a caller who changes the `X-Forwarded-For` header.
