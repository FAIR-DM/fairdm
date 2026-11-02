# How to allow only some sites to call the API

By default a page on any website may call the portal's API from a browser. You narrow that to the sites you name. Do this when the API should be used from your own front end, and not from arbitrary pages.

## Before you start

- You need to edit the portal's settings module, after the `fairdm.setup()` call. The settings used here are described in [Settings](../reference/settings.md).
- Know the address of each site, with its scheme and, if it is not the default, its port, such as `https://my-portal-frontend.example.com`.

## Steps

1. After the `fairdm.setup()` call, turn off the default and list the sites.

   ```python
   import fairdm

   fairdm.setup()

   CORS_ALLOW_ALL_ORIGINS = False
   CORS_ALLOWED_ORIGINS = [
       "https://my-portal-frontend.example.com",
   ]
   ```

   Write each entry as a scheme and a host, with no path and no trailing slash.

2. Leave `CORS_URLS_REGEX` as FairDM sets it. It limits cross-site answers to addresses under `/api/`, and no other address answers another origin.

3. Restart the portal.

## The result

A browser lets a page on a listed site read the API's answers. A page on any other site is blocked by the browser.

- Credentials are not allowed whichever list you use, so a browser never sends the portal's sign-in cookie from another site. A page on a listed site still has to send a token to write or to read private records.
- A preflight request that asks to send the `Authorization` header is allowed.
- The list limits browsers only. A script, `curl` or a server can call the API without any origin, and is not affected. To control who may write, use tokens: see [How to restrict API tokens to some people](restrict-api-tokens-to-some-people.md).

The decision to let every origin call the API is recorded in [ADR 0028](../../adr/0028-api-tokens-are-created-on-the-account-pages.md).
