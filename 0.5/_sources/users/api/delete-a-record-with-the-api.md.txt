# How to delete a record with the API

This guide deletes one sample from a script. Use it to remove records you loaded by mistake, or to clear out a batch you no longer need.

```{warning}
A deleted record cannot be brought back. The API does not ask you to confirm.
```

## Before you start

- Have an [API token](get-an-api-token.md) in the environment variable `FAIRDM_TOKEN`.
- Be listed on the record at the manage level. Edit level is not enough.
- Know the short identifier (`uuid`) of the record.

## Steps

1. Save this as `delete_sample.py`. Change the names marked with a comment.

   ```python
   import os

   import requests

   PORTAL = "https://portal.example.org"  # your portal's address
   SAMPLE_TYPE = "rock-samples"  # the sample type of the record
   SAMPLE = "sxXGUGgXRVStFw3jbpBWQeM"  # the uuid of the record

   session = requests.Session()
   session.headers["Authorization"] = f"Token {os.environ['FAIRDM_TOKEN']}"

   response = session.delete(
       f"{PORTAL}/api/v1/samples/{SAMPLE_TYPE}/{SAMPLE}/", timeout=30
   )
   if response.status_code == 409:
       raise SystemExit(response.json()["detail"])
   response.raise_for_status()
   print("Deleted")
   ```

2. Run it with `python delete_sample.py`.

## The result

The portal answers `204` with no body, and the script prints `Deleted`. The record is gone from every list.

The API refuses the same deletes the portal refuses:

- A project that has a public dataset. Make the datasets private or delete them first.
- A sample that has measurements made on it. Delete the measurements first.

For these the portal answers `409`, nothing is deleted, and the `detail` in the answer gives the reason. The script prints it.

If the portal answers `403`, your level on the record is too low. If it answers `404`, the record does not exist or is private and you may not see it.

Deleting works the same for the other kinds of record. The portal's own pages for it are [Delete a project](../projects/delete-a-project.md), [Delete a dataset](../datasets/delete-a-dataset.md), [Delete a sample](../samples/delete-a-sample.md) and [Delete a measurement](../measurements/delete-a-measurement.md).

## Next

The [REST API reference](../../developers/reference/rest-api.md) lists every answer a request can get.
