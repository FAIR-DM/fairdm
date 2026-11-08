# How to check the portal's services in the control room

The control room shows whether the services behind your portal are working: Redis, the cache that is kept in it, and the background-task workers. Use it when pages are slow, when a background task such as a contributor lookup does not finish, or to confirm that a change to the server took effect.

Only superusers can open it. Staff accounts that are not superusers, and people who hold a portal role, are refused, because the pages show how the portal is wired and the arguments of background tasks.

## Before you start

You need to sign in with a superuser account that is also marked as staff. A superuser whose staff flag has been cleared is refused.

## Steps

1. Sign in to the administration interface.
2. On the administration home page, open the **Dashboard** entry under **DJ Control Room**. It opens the dashboard, which lists one card for each panel.
3. Open the panel you need.
   - **Redis** lists the keys in the portal's Redis database and shows each key's value and remaining lifetime.
   - **Cache** lists what the portal has cached and shows each entry.
   - **Celery** shows the workers that are running, the queues and the tasks.

## The result

Each panel shows the current state of its service. If a service is down, its panel still opens and shows that it cannot connect, so you can tell which part is at fault.

The Redis panel is read-only. You can look at keys but not change, delete or expire them. Developers can turn editing on, as described in [How to change who can open the control room](../../developers/how-to/change-who-can-open-the-control-room.md).

```{warning}
Flushing the cache from the cache panel clears the whole Redis database. When the cache and the background-task queue share one `REDIS_URL`, as they do by default, tasks that are waiting in the queue are lost with it.
```
