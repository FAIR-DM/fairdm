# Limits on the API

The API that serves your portal's records to scripts is limited, so that a crawler or a runaway
script cannot overload a small server. This page gives the limits a new portal starts with and the
settings that change them. It is written for the person who runs the portal. The settings go in the
portal's Django settings file, so a change needs someone who can edit that file and restart the
portal.

## How much a caller may ask for

Each kind of caller has two limits. One counts requests over a minute and stops a burst. The other
counts requests over a day and stops steady heavy use. A caller who is signed in with a token or a
session is allowed several times what an anonymous caller is.

| Limit | Setting name | Starting value |
|-------|--------------|----------------|
| Anonymous caller, over a minute | `anon_burst` | 30 requests |
| Anonymous caller, over a day | `anon_day` | 2,000 requests |
| Signed-in caller, over a minute | `user_burst` | 120 requests |
| Signed-in caller, over a day | `user_day` | 20,000 requests |

A caller past a limit is refused with the answer `429 Too Many Requests`. The answer carries a
`Retry-After` header that says how many seconds to wait before trying again.

An anonymous caller is counted by the address the request comes from, so the limits only protect a
portal once the address is read correctly. See [Counting callers behind a proxy](#counting-callers-behind-a-proxy).
A signed-in caller is counted as the person, whatever address they use.

## How many records a page holds

Every list in the API is paged. A caller who does not ask for a size gets the default. A caller may
ask for more with `?page_size=`, up to a ceiling, and is given the ceiling when asking for more
than that.

| Setting | Meaning | Starting value |
|---------|---------|----------------|
| `REST_FRAMEWORK["PAGE_SIZE"]` | Records in a page when the caller does not ask | 100 |
| `FAIRDM_API_MAX_PAGE_SIZE` | Most records a caller may ask for in one page | 1,000 |

At the starting values a script reading ten thousand records makes a hundred requests, or ten when
it asks for the largest page. An anonymous script that waits as told when it is refused reads them
in a few minutes, well inside the daily limit.

## Changing a limit or a page size

Put the changes in the portal's settings file, after `fairdm.setup()` returns, and restart the
portal. The limits are the entries of one dictionary:

```python
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user_day"] = "100000/day"
REST_FRAMEWORK["PAGE_SIZE"] = 50
FAIRDM_API_MAX_PAGE_SIZE = 500
```

A rate is written as a number, a slash and a period: `second`, `minute`, `hour` or `day`. Setting
a rate to `None` removes that limit. If you replace the whole `DEFAULT_THROTTLE_RATES` dictionary
instead of changing entries, include all four names, or API requests fail with a server error.

The API documentation page at `/api/v1/docs/` lists the limits and page sizes the portal is
running with, so it always matches the settings.

## Counting callers behind a proxy

Most portals sit behind a reverse proxy or a load balancer. Tell the API how many proxies there
are with `REST_FRAMEWORK["NUM_PROXIES"]`:

```python
# One reverse proxy between the visitor and the portal
REST_FRAMEWORK["NUM_PROXIES"] = 1
```

The limits count per address only once `NUM_PROXIES` is set. Without it, the API takes the
caller's address from the `X-Forwarded-For` header, which the caller controls. A script that sends
a different value in that header on every request is counted as a new caller each time and is never
stopped. Set it to `0` when no proxy stands in front of the portal.

## Where the counts are kept

The counts live in the portal's default cache, which is Redis on a production portal. Every worker
process of the portal shares them. If the cache cannot be reached, requests are not counted and none
is refused for exceeding a limit, so keep the cache running.
