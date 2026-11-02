# How to sync a profile from ORCID or ROR without Celery

A sync copies a person's ORCID record or an organization's ROR record onto the profile, and a Celery worker normally does it in the background. You run it yourself in a shell when a portal has no worker, or when you want one profile refreshed at once.

## Before you start

- The shell must run in the portal's environment, and the server must reach `pub.orcid.org` or `api.ror.org` over HTTPS.
- The profile must already hold the identifier. The task reads it from the profile's ORCID or ROR identifier.

On a development portal with `REDIS_URL` unset, FairDM already runs tasks in the web process, so a saved identifier syncs without a worker and you do not need this page.

## Steps

1. Open a Django shell.

   ```bash
   python manage.py shell
   ```

2. Find the identifier and run the sync task as an ordinary function.

   ```python
   from fairdm.contrib.contributors.models import ContributorIdentifier
   from fairdm.contrib.contributors.tasks import sync_contributor_identifier

   identifier = ContributorIdentifier.objects.get(
       type="ORCID", value="0000-0002-1825-0097"
   )
   sync_contributor_identifier(identifier.pk)
   ```

   For an organization, look up the ROR identifier in the same way.

   ```python
   identifier = ContributorIdentifier.objects.get(type="ROR", value="04aj4c181")
   sync_contributor_identifier(identifier.pk)
   ```

   The call returns `True` when the sync succeeded and `False` when the registry has no such record or answered in a form the task cannot read. A network error raises `requests.RequestException`.

3. Check the profile.

   ```python
   profile = identifier.related.get_real_instance()
   print(profile.last_synced, bool(profile.synced_data))
   ```

## The result

The profile's `synced_data` holds the registry's record and `last_synced` is today's date. A blank name is filled from the record. An organization also takes its city, country and location from the record's first place. Nothing else on the profile changes.

## Rewrite the whole profile

To overwrite the profile with the registry's record instead, call the transform. `force=True` fetches even if the profile was synced today.

```python
from fairdm.contrib.contributors.utils.transforms import ORCIDTransform, RORTransform

person, created = ORCIDTransform.update_or_create("0000-0002-1825-0097", force=True)
organization, created = RORTransform.update_or_create("04aj4c181", force=True)
```

```{warning}
The transform replaces the display name, the first and last names and the biography of a person with the ORCID values. A blank value in ORCID blanks the portal's biography. For an organization it replaces the name and the alternative names and sets the location. Any correction made in the portal is lost. If no profile holds the identifier, the call creates one.
```

If a sync does not update a profile and you do not know why, work through [How to fix an ORCID or ROR sync that does not update](../../administrators/how-to/fix-an-orcid-or-ror-sync-that-does-not-update.md). The registries the portal asks when a manager adds a contributor are described in [How the ORCID and ROR lookup works](../../administrators/explanation/how-the-orcid-and-ror-lookup-works.md).
