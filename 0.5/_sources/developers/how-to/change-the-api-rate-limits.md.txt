# How to change the API rate limits

The API limits how often one caller may ask, so that a crawler or a runaway script cannot overload a small server. You change a limit when the figures a portal starts with are too tight for its users or too loose for its server.

## Before you start

You need to edit the portal's settings module and restart the portal. The settings are described in [Settings](../reference/settings.md), which also gives the values a portal starts with.

## Steps

1. Open the settings module that calls `fairdm.setup()`.

2. After the `fairdm.setup()` call, change the entries you want in `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`.

   ```python
   import fairdm

   fairdm.setup()

   REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user_day"] = "100000/day"
   REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon_burst"] = "60/minute"
   ```

   A rate is a number, a slash and a period: `second`, `minute`, `hour` or `day`. The API uses four names: `anon_burst`, `anon_day`, `user_burst` and `user_day`. The search boxes use four of their own: `autocomplete_anon_burst`, `autocomplete_anon_day`, `autocomplete_user_burst` and `autocomplete_user_day`.

3. To remove a limit, set its rate to `None`.

   ```python
   REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon_day"] = None
   ```

4. Restart the portal.

## The result

The API documentation page at `/api/v1/docs/` lists the rates the portal runs with, one line for each name in the dictionary, so it matches the settings. A caller over a limit is answered `429 Too Many Requests` with a `Retry-After` header.

Change entries of the dictionary rather than replacing it. If you replace the whole dictionary, include all four API names, or API requests fail with a server error. A search-box name you leave out keeps its starting value, so a replaced dictionary does not break the search boxes.

The limits count callers by network address, so they protect a portal only once the portal knows how many proxies stand in front of it. See [How to count API callers behind a proxy](count-api-callers-behind-a-proxy.md). To change how many records a page holds, see `PAGE_SIZE` and `FAIRDM_API_MAX_PAGE_SIZE` in [Settings](../reference/settings.md). Why there are two limits for each caller is explained in [How API callers are limited](../explanation/how-api-callers-are-limited.md).

The general rule for overriding a FairDM setting is in [How to override a FairDM setting](override-a-fairdm-setting.md).
