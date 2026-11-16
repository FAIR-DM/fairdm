# How to read a dataset's samples with a script

This guide reads every sample of one dataset into a Python list, following the pages the portal returns. Use it to copy a dataset's samples into your own analysis. Measurements are read the same way from their own address.

## Before you start

- Have an [API token](get-an-api-token.md) in the environment variable `FAIRDM_TOKEN`. Public records can be read without one, but a token also lets you read the private datasets you have access to.
- Know the name of the dataset.
- Know the plural name of the sample type, in the form it has in the API. It is the type's plural name in lower case with hyphens, such as `rock-samples` for "Rock Samples". The [API documentation](api-docs.md) lists the sample types your portal holds.

## Steps

1. Save this as `read_samples.py`. Change the three names marked with a comment.

   ```python
   import os
   import time

   import requests

   PORTAL = "https://portal.example.org"  # your portal's address
   DATASET_NAME = "Rock chemistry of the north face"  # the name of your dataset
   SAMPLE_TYPE = "rock-samples"  # the sample type to read

   session = requests.Session()
   session.headers["Authorization"] = f"Token {os.environ['FAIRDM_TOKEN']}"


   def get_all(path, **params):
       """Return every record of a list, following the pages."""
       url = f"{PORTAL}{path}"
       records = []
       while url:
           response = session.get(url, params=params, timeout=30)
           if response.status_code == 429:
               time.sleep(int(response.headers["Retry-After"]))
               continue
           response.raise_for_status()
           body = response.json()
           records.extend(body["results"])
           url, params = body["next"], None
       return records


   datasets = [d for d in get_all("/api/v1/datasets/") if d["name"] == DATASET_NAME]
   if len(datasets) != 1:
       raise SystemExit(f"Found {len(datasets)} datasets named {DATASET_NAME!r}")

   samples = get_all(
       f"/api/v1/samples/{SAMPLE_TYPE}/",
       dataset=datasets[0]["uuid"],
       ordering="name",
   )
   print(f"{len(samples)} samples")
   ```

2. Run it with `python read_samples.py`.

The script asks the portal for the datasets you may see and keeps the one with your name. It then asks for the samples of that dataset, using the dataset's short identifier (`uuid`). The address in `next` already carries the filters, so `get_all` sends them with the first request only. When the portal answers `429`, you have sent too many requests, and the script waits for the seconds the portal asks for before it carries on.

## The result

The script prints the number of samples, and `samples` holds one dictionary for each. A sample has the fields every sample has, such as `uuid`, `name`, `status` and `dataset`, and the fields its type records. A reference to another record, such as `dataset`, gives that record's `uuid` and its address in the API in `url`.

If a reference reads `None`, the record it names is private and you may not see it.

## Next

- [How to read only what changed](read-only-what-changed.md) to keep a copy up to date
- The [API documentation](api-docs.md) screen, which lists the filters each type offers
- The [REST API reference](../../developers/reference/rest-api.md) for the addresses, filters, page sizes and request limits
