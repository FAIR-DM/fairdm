# How to change a record with the API

This guide changes some fields of a sample and leaves the rest as they were. Use it to correct values or to update many records from a script.

## Before you start

- Have an [API token](get-an-api-token.md) in the environment variable `FAIRDM_TOKEN`.
- Be listed on the record with at least the edit level.
- Know the short identifier (`uuid`) of the record. A list in the API gives it, as does the last part of the record's page address on the portal.

## Steps

1. Save this as `change_sample.py`. Change the names marked with a comment.

   ```python
   import os

   import requests

   PORTAL = "https://portal.example.org"  # your portal's address
   SAMPLE_TYPE = "rock-samples"  # the sample type of the record
   SAMPLE = "sxXGUGgXRVStFw3jbpBWQeM"  # the uuid of the record

   session = requests.Session()
   session.headers["Authorization"] = f"Token {os.environ['FAIRDM_TOKEN']}"

   # Only the fields you send change. This one belongs to the example type.
   changes = {"weight_grams": 12.5}

   response = session.patch(
       f"{PORTAL}/api/v1/samples/{SAMPLE_TYPE}/{SAMPLE}/", json=changes, timeout=30
   )
   if response.status_code == 400:
       raise SystemExit(response.json())
   response.raise_for_status()

   sample = response.json()
   print(sample["name"], sample["modified"])
   ```

2. Run it with `python change_sample.py`.

## The result

The portal answers `200` and the record as it now stands. Every field you did not send keeps its value, and `modified` shows the time of the change.

To replace the record instead, use `session.put`. It needs every required field.

Two kinds of change need more than the edit level:

- Changing `visibility`.
- Moving a record by sending a different `dataset`, `sample` or `project`.

Both need the manage level on the record. Sending the parent or visibility the record already has is not a change.

If the portal answers `403`, your level on the record is too low. If it answers `404`, the record does not exist or is private and you may not see it. The portal says the same for both.

The API leaves some fields as they are even when you send them, and answers as if it had accepted them:

- the record's `uuid`, `url`, `html_url`, `added` and `modified`
- a project's or dataset's `image`
- a dataset's `published` and `license`
- the descriptions, key dates, identifiers, keywords and credited people of any record
- the location of a sample or measurement

Change those on the record's pages in the portal.

## Next

- [How to delete a record with the API](delete-a-record-with-the-api.md)
- The [REST API reference](../../developers/reference/rest-api.md) for the fields of each record and the answers a request can get
