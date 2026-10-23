# How to import people from a list of ORCID iDs

This script creates a profile for each ORCID iD in a file, so that records can be credited to people who have not signed up. You run it when you attribute imported data to researchers you know only by iD.

To import from a spreadsheet with names and affiliations instead, use the **Import** button on the people list. See [People](../../administrators/reference/people.md).

## Before you start

- The portal's server must reach `pub.orcid.org` over HTTPS.
- A background worker should be running. Each new profile queues a sync with ORCID, and the sync needs a worker. Without one the profile keeps the data this script stores.
- Each iD in the file is the iD alone, such as `0000-0002-1825-0097`, not its web address.

## Steps

1. Save the iDs in a CSV file with one column named `orcid_id`.

   ```text
   orcid_id
   0000-0002-1825-0097
   0000-0003-1234-5678
   ```

2. Open a Django shell in the portal's environment.

   ```bash
   python manage.py shell
   ```

3. Run the import. It skips anyone who has already claimed their account, makes a new profile unclaimed, and pauses between rows to stay under ORCID's limits.

   ```python
   import csv
   import time

   import requests

   from fairdm.contrib.contributors.models import ContributorIdentifier
   from fairdm.contrib.contributors.utils.transforms import ORCIDTransform

   with open("orcids.csv", newline="") as handle:
       for row in csv.DictReader(handle):
           orcid_id = row["orcid_id"].strip()

           held = ContributorIdentifier.objects.filter(
               type="ORCID", value=orcid_id
           ).first()
           if held and getattr(held.related.get_real_instance(), "is_claimed", False):
               print(f"Skipped {orcid_id}: already claimed")
               continue

           try:
               person, created = ORCIDTransform.update_or_create(orcid_id)
           except requests.RequestException as error:
               print(f"Failed {orcid_id}: {error}")
               continue

           if created:
               person.email = None
               person.is_claimed = False
               person.is_active = True
               person.set_unusable_password()
               person.save(update_fields=["email", "is_claimed", "is_active", "password"])

           print(f"{'Created' if created else 'Updated'} {person}")
           time.sleep(1.5)
   ```

## The result

Each new person exists as an active, unclaimed profile with the name, the biography and the links from the ORCID record, an ORCID identifier, no email address and an unusable password. That is a ghost. Someone who later signs in with that iD claims the profile. See [How a profile is claimed](../../explanation/how-a-profile-is-claimed.md).

A person already in the portal under that iD is left alone when their record was synced within the last day, and is refreshed from ORCID otherwise. A refresh rewrites the name, the first and last names and the biography, as described in [How to sync a profile from ORCID or ROR without Celery](sync-a-profile-from-orcid-or-ror-without-celery.md).

The people appear in the people list in the administration interface, where the **Claimed Status** filter shows them as unclaimed. To credit them on a record, see [How to credit a person on a record](credit-a-person-on-a-record.md).
