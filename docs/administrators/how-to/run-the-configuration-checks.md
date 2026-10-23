# How to run the configuration checks

Running the checks tells you what is wrong with the portal's configuration before a visitor finds out. You run them when you set a portal up, after you change its configuration, and in the pipeline that deploys it.

## Before you start

You need a shell on the machine or container that runs the portal, set up with the same environment variables as the portal. A check reads the settings in force, so a shell with different variables reports on a different portal.

## Steps

1. Run the full set of checks against production standards.

   ```bash
   python manage.py check --deploy
   ```

   `--deploy` includes the checks that apply to a live portal. It assesses against production standards whatever `DJANGO_ENV` holds. Plain `python manage.py check` leaves those checks out.

2. Read the report. Each problem starts with its id, such as `fairdm.E001`. Look the id up in [Configuration checks](../reference/configuration-checks.md) for what it means and how to fix it.

3. To run only some checks, add `--tag` with one or more tags. Pass `--deploy` as well, because a tag does not include the deployment checks on its own.

   ```bash
   python manage.py check --deploy --tag database --tag caches
   ```

   To run only the checks that can stop a production start, use the `production_critical` tag.

   ```bash
   python manage.py check --deploy --tag production_critical
   ```

4. To use the checks in a deployment pipeline, run the command in a step that has the production environment variables. The command exits with a non-zero status when it finds an error, which fails the step. To fail on warnings too, add `--fail-level WARNING`.

   ```bash
   python manage.py check --deploy --fail-level WARNING
   ```

## The result

The command prints "System check identified no issues" when every check passes. Otherwise it lists each problem with a hint.

A production portal with a failing production-critical check cannot run the command at all. It stops with "FairDM production configuration is invalid" and lists the failing checks. Fix those first, then run the command again to see the checks that are not part of the start-up guard. See [How to fix a portal that refuses to start in production](fix-a-portal-that-refuses-to-start-in-production.md).

The tags are listed in [Configuration checks](../reference/configuration-checks.md#tags). Why some checks run at start-up and others only on request is explained in [How FairDM configures a portal](../../explanation/how-fairdm-configures-a-portal.md).
