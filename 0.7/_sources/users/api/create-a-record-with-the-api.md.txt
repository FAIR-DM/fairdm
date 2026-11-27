# How to create a record with the API

This guide creates a sample in a dataset from a script. Use it to load many records from a file or a lab system instead of typing them into the portal. Projects, datasets and measurements are created the same way, at their own addresses.

## Before you start

- Have an [API token](get-an-api-token.md) in the environment variable `FAIRDM_TOKEN`.
- Be listed on the dataset with at least the edit level. Any signed-in person may create a project.
- Know the short identifier (`uuid`) of the dataset. It is the last part of the dataset's page address on the portal, such as `dV4DYUk6ohGJdizhxJotoZ8` in `https://portal.example.org/datasets/dV4DYUk6ohGJdizhxJotoZ8/`.
- Know the fields of the sample type. The [API documentation](api-docs.md) marks the fields a request must carry.

## Steps

1. Save this as `create_sample.py`. Change the names marked with a comment.

   ```python
   import os

   import requests

   PORTAL = "https://portal.example.org"  # your portal's address
   SAMPLE_TYPE = "rock-samples"  # the sample type to create

   session = requests.Session()
   session.headers["Authorization"] = f"Token {os.environ['FAIRDM_TOKEN']}"

   body = {
       "name": "RS-14",
       "dataset": "dV4DYUk6ohGJdizhxJotoZ8",  # the uuid of your dataset
       # The fields your sample type records. These belong to the example type.
       "rock_type": "igneous",
       "collection_date": "2024-05-02",
   }

   response = session.post(
       f"{PORTAL}/api/v1/samples/{SAMPLE_TYPE}/", json=body, timeout=30
   )
   if response.status_code == 400:
       raise SystemExit(response.json())
   response.raise_for_status()

   sample = response.json()
   print(sample["uuid"], sample["html_url"])
   ```

2. Run it with `python create_sample.py`.

## The result

The portal answers `201` and the new record, complete. The script prints its short identifier and the address of its page on the portal. You are listed on the record at the manage level.

If the portal answers `400`, nothing was saved. The script prints each field at fault and why, such as a missing required field, a value it cannot accept, or a dataset that does not exist or that you may not add to.

A record is created inside a parent, named by its short identifier:

- a sample names its `dataset`
- a measurement names its `dataset` and its `sample`
- a dataset may name its `project`

A project or dataset you create is private until you send `visibility` as `1`. Descriptions, key dates, identifiers, keywords and the credited people cannot be sent to the API. Add them on the record's pages in the portal, described in [Descriptions](../editing-a-record/descriptions.md), [Key dates](../editing-a-record/key-dates.md), [Identifiers](../editing-a-record/identifiers.md), [Keywords](../editing-a-record/keywords.md) and the [Contributors tab](../contributors/contributors-tab.md).

## Next

- [How to change a record with the API](change-a-record-with-the-api.md)
- The [REST API reference](../../developers/reference/rest-api.md) for the fields of each record and the answers a request can get
