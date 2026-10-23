# How to count API callers behind a proxy

The API limits an anonymous caller by the address the request comes from, and behind a reverse proxy or a load balancer it reads the right address only when the portal knows how many proxies there are. You set that number when you deploy a portal, and again when you add or remove a proxy.

## Before you start

Count the proxies between a visitor and the portal. A reverse proxy, a load balancer and a content delivery network each count as one. Each must add the address it received the request from to the end of the `X-Forwarded-For` header.

## Steps

1. Open the settings module that calls `fairdm.setup()`.

2. After the `fairdm.setup()` call, set `NUM_PROXIES` in `REST_FRAMEWORK` to that count. Use `0` when nothing stands in front of the portal.

   ```python
   import fairdm

   fairdm.setup()

   # One reverse proxy between the visitor and the portal
   REST_FRAMEWORK["NUM_PROXIES"] = 1
   ```

3. Restart the portal.

4. Run the deployment checks.

   ```bash
   python manage.py check --deploy
   ```

## The result

`fairdm.W601` no longer appears. Any value you set ends the warning, `0` and `None` included. FairDM chooses no value for you, because the right number depends on your deployment.

The API takes the caller's address from the entry of `X-Forwarded-For` that sits that many places from the right, the one your own proxy wrote. Without the setting, the API takes the whole header, which the caller writes. A script that sends a different value in it on every request is then counted as a new caller each time, and the limits never stop it.

Use the exact count. A number larger than the real count reaches an entry further left, which the caller wrote and can change. A number smaller than the real count counts every visitor by the address of a proxy.

The same count applies to the limits on the search boxes, which count callers the way the API does. The check is described in [Configuration checks](../../administrators/reference/configuration-checks.md#fairdmw601-the-number-of-proxies-in-front-of-the-api-is-not-set). The reason for counting by address is in [How API callers are limited](../explanation/how-api-callers-are-limited.md).
