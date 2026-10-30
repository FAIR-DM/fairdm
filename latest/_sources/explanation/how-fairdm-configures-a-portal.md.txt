# How FairDM configures a portal

This page explains how a FairDM portal gets its Django settings, why the settings are layered the way they are, and why a portal in production refuses to start when its configuration is unsafe. It covers the design. It does not list the arguments of `fairdm.setup()` or the settings FairDM defines, which are in [Configuration](../developers/reference/configuration.md) and [Settings](../developers/reference/settings.md), and it does not list each configuration check, which is in [Configuration checks](../administrators/reference/configuration-checks.md).

## One entry point

A portal's settings module makes a single call:

```python
import fairdm

fairdm.setup()
```

That call fills the module with a complete Django configuration. Everything else a portal sets comes after it, as ordinary assignments. The aim is that a portal author has one place to look and one rule to learn, instead of copying a long settings file from a template and having to keep it current.

## Production is the starting point

The configuration FairDM builds first is a production configuration. `DJANGO_ENV` names the environment, and when it is unset the environment is `production`. The baseline is not a development setup that also happens to work in production. It is the strict one, and development is the exception that relaxes it.

The reason is the direction of failure. If a variable is forgotten, an unrecognised name falls to the strictest configuration rather than the loosest. A developer sees the effect within seconds, because the portal behaves as if it were deployed. The opposite default, where an unknown name resolves to development, would loosen security on a typo.

## The five layers

`fairdm.setup()` composes the settings in five layers. A later layer wins over an earlier one for the same setting.

1. **The baseline.** FairDM's production defaults, one module for each concern, such as the database, the cache, security and authentication.
2. **FairDM's own override** for the resolved environment, if FairDM ships one. It ships exactly one, for `development`.
3. **Addon settings.** Settings contributed by the addons the portal names.
4. **The portal's own override module** for the resolved environment, found beside the portal's settings module.
5. **Assignments the portal makes after `setup()` returns.** This is the only supported way to override a setting FairDM owns.

`setup()` accepts no settings as arguments. Passing one raises a `TypeError`. A settings change is an assignment after the call, so there is never a question of which of two routes wins.

### A layer applies if its file exists

Layers 2 and 4 are chosen by looking for a module named after the environment. If the module is there, it applies. If it is not, the layer is skipped without error. There is no list of permitted environment names, and no name is special except that FairDM happens to ship a file for `development`.

The alternative is a list of valid names and a separate map from name to file. Two structures then have to agree, and a name present in one and missing from the other fails in a way neither describes. Asking the filesystem is a single question with one answer.

The consequence is that any value of `DJANGO_ENV` is valid. A typo, a name only your portal knows or an empty string finds no override module and gets the production baseline. A portal that wants a staging profile provides a `staging` override module the same way it would provide any other.

### The portal's override sits beside its settings module

The portal's own override is looked up in the directory that holds its settings module, not in a directory that must be called `config`. A portal laid out the way `django-admin startproject` makes it, with its settings inside a package named after the project, still has its override found. Because "no module found" is a legitimate outcome, a hard-coded path would fail silently there. The documentation shows the recommended layout in every example, since that is what a new portal should use.

If the settings module has no file on disk, such as one generated at run time, the portal layer is skipped with a warning.

### Environment files are read first

Before any layer is composed, `setup()` reads environment files. Reading `stack.env`, then `stack.<environment>.env`, respects variables already set in the process. An explicit `env_file` is read last and does overwrite them. A real environment variable therefore beats a file on disk, unless you ask a specific file to win.

### Addons are applied safely

An addon's settings are applied to a private copy, and merged only if its module runs to the end. An addon that fails partway leaves no half-written settings. In production a failing addon stops the portal and names the addon. In any other environment it logs a warning and is skipped.

## A portal's apps come first

Apps a portal declares through `setup()` are registered ahead of FairDM's own apps. Django's template and static file loaders return the first match in the order of `INSTALLED_APPS`. A portal that ships a template at the same path as a FairDM one has its own file served. Overriding a framework template is the ordinary way a portal makes itself its own, and a framework that could not be overridden at that point would push portals towards forks. See [ADR 0004](../adr/0004-portal-apps-precede-framework-apps.md).

## No safe default for an unsafe value

FairDM ships no working default for a value whose absence would weaken a deployment: the secret key, the site domain, the allowed-hosts list that is composed from it, and any administrative password. Each resolves to an empty string until the deployment sets it.

The settings do not raise when one is missing. The baseline is layer 1, and a later layer could supply the value, so a failure at the baseline would stop development and the test suite before the development layer ran. Instead the production checks described below refuse to start the portal. A default that is safe only because a check elsewhere might catch it is safe only while that check runs. Removing the default makes the failure structural. See [ADR 0003](../adr/0003-no-working-default-for-a-security-critical-value.md).

## Why a production portal refuses to start

Whenever the settings in force are the production baseline, FairDM runs its production-critical checks and stops the process if any fails. Every failure is reported in one message, not only the first. The checks cover:

- A PostgreSQL database with PostGIS.
- A shared cache backend.
- A secret key that is present and is not an insecure or published value.
- A non-empty allowed-hosts list with no wildcard.
- Debug switched off.
- The four portal roles present in the database.
- No development accounts present.

### The gate is the composed settings

The checks run when the settings are the production baseline, which is decided by the same file-existence rule as the layers. The only exemption is an environment for which FairDM ships a non-production override, which today is `development` alone. A typo, `Production` with a capital letter, an empty string and a `staging` module of your own all run on the production baseline, so all of them are checked as production. Setting `DJANGO_ENV` to exactly `development` is the only way to opt out. A guard keyed on the literal word "production" would have skipped the checks for `Production` while the layers gave it the strict baseline, and the portal would have started with no secret key and no database.

### Why the check runs from `ready()`

`setup()` runs inside the settings module, before Django has loaded its apps, so the check framework does not exist at that point. `ready()` is the first moment in startup when it does. Raising there stops both a server and every management command.

A consequence to accept is that a production machine with broken configuration cannot run any management command until it is fixed, `check --deploy` included. That is what failing fast means, and the remedy is always to set the missing variable.

### Why Celery is not in the list

A portal can legitimately run without a background worker. A guard that stops a start for a reason operators consider wrong is a guard they learn to route around. Celery checks therefore run on demand and are not part of the boot guard.

### Why the roles check stands down for `migrate`

The portal roles are installed after migration. The roles check fires before that, so blocking `migrate` on a missing role would leave the portal with no way back. The check stands down for the `migrate` command. An absent or unmigrated group table reports nothing, because a database that has never been migrated is a different condition from a portal that is missing its roles. See [ADR 0020](../adr/0020-a-missing-role-is-answered-four-ways.md).

### Why one check runs in every environment

`fairdm.E006` catches a cookie named with a `__Secure-` or `__Host-` prefix while the matching secure setting is off. Browsers silently discard such a cookie, so every login form looks correct and every post is rejected. The fault shows up where a portal is served over plain HTTP, which is away from production, so the check is not tagged as a deployment check and runs on the plain `check` command and at `runserver`. A check that only ran under `--deploy` would never fire where the fault occurs.

### What the guard does not do

The full check set, including the recommendations outside the production-critical subset, is available on demand through `manage.py check --deploy`. It always assesses against production standards, whatever the current environment. Silencing a production-critical check in a report hides it from the report. It does not stop the check running at start-up. The decision record is [ADR 0002](../adr/0002-configuration-checks-run-in-production-only.md), and the rule for environments is in [ADR 0001](../adr/0001-environment-overrides-are-found-by-existence.md).

## Where to go next

- [How to override a FairDM setting](../developers/how-to/override-a-fairdm-setting.md)
- [How to add an environment override module](../developers/how-to/add-an-environment-override-module.md)
- [How to create an addon](../developers/how-to/create-an-addon.md)
- [How to fix a portal that refuses to start in production](../administrators/how-to/fix-a-portal-that-refuses-to-start-in-production.md)
