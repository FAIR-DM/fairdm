# How to fix an ORCID or ROR sync that does not update

A sync copies a person's ORCID record or an organization's ROR record into the portal, and **Last synced** shows when it last completed. When that date stays empty or never changes, you work through the likely causes in order, from the record itself to the server.

## Before you start

Steps 1 to 3 need only the administration interface. Steps 4 and 5 need someone who can read the server's logs and manage its background worker.

## Steps

1. Open the record and read **Last synced**.

   - For a person, open **Community** → **Users**, then the person. **Last synced** is in the first section.
   - For an organization, open **Community** → **Organizations**, then the organization. **Last synced** and **Synced data** are in the **Synchronisation** section. An empty **Synced data** means no record has ever been stored.

   **Last synced** is a date, so a sync that ran earlier today looks the same as one that ran a minute ago.

2. Check that the record holds the identifier, in the right form.

   - A person's identifiers are in the identifiers section of their change form. The ORCID value must be the iD alone, such as `0000-0002-1825-0097`. A value that is a web address makes the sync ask ORCID for a record that does not exist, and it gives up.
   - An organization's ROR value may be the bare ID (`04aj4c181`) or its address (`https://ror.org/04aj4c181`).

   The organization form has no identifiers section. An organization without a ROR identifier is skipped by **Sync from ROR**. Add the organization again from the **Contributors** tab of a record, choosing it from the ROR search, so that the identifier is stored. See [How to add a person or organization](../../users/contributors/add-a-person-or-organization.md).

3. For an organization, tick it in the list, choose **Sync from ROR** in the **Action** menu and select **Go**. The message "Triggered ROR sync for 1 organization(s)" means the sync was queued, not that it finished. If the message says no organizations with ROR identifiers were found, return to step 2. People have no such action. Saving a new identifier queues their sync.

4. Ask whoever runs the server to check that a background worker is running and that the broker, the Redis instance named by `REDIS_URL`, is reachable. A queued sync waits for a worker. Run the checks with `--deploy` and look for `fairdm.E300` and `fairdm.E301`. See [How to run the configuration checks](run-the-configuration-checks.md).

5. Ask for the worker's log. A sync that gives up logs "not found (404)" for an iD or ID the registry does not hold, or a timeout after ten seconds. A failed request is retried up to three times with growing delays. The sync task is limited to ten runs a minute for each worker, so a large batch takes a while.

## The result

**Last synced** shows today's date, and an organization's **Synced data** holds the registry's record.

A completed sync does less than you may expect:

- It stores the registry's record and sets **Last synced**.
- It fills in a person's name only when the name is blank.
- For an organization it also sets the city, country and location from the record's first place, and fills a blank name.
- It does not change a person's biography, links or alternative names.

Once an organization has synced data, its name, city and country become read-only in the administration interface. Its location stays editable.

To rewrite a whole profile from the registry's record, or to run a sync on a machine with no worker, see [How to sync a profile from ORCID or ROR without Celery](../../developers/how-to/sync-a-profile-from-orcid-or-ror-without-celery.md). How the portal searches the two registries when a manager adds a contributor is in [How the ORCID and ROR lookup works](../explanation/how-the-orcid-and-ror-lookup-works.md).
