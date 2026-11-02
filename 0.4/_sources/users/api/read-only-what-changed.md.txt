# How to read only what changed

This guide keeps a local copy of a list up to date by asking only for the records that were added or changed since your last read. Use it when you read the same dataset on a schedule and do not want to download everything each time.

## Before you start

- Have an [API token](get-an-api-token.md) in the environment variable `FAIRDM_TOKEN`.
- Be able to [read a dataset's samples](read-a-datasets-samples-with-a-script.md). This guide changes that script.

## Steps

1. Save this as `read_changes.py`. Change the three names marked with a comment.

   ```python
   import os
   import time
   from datetime import datetime, timezone
   from pathlib import Path

   import requests

   PORTAL = "https://portal.example.org"  # your portal's address
   DATASET = "dV4DYUk6ohGJdizhxJotoZ8"  # the uuid of your dataset
   SAMPLE_TYPE = "rock-samples"  # the sample type to read
   STATE_FILE = Path("last-read.txt")

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


   started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

   params = {"dataset": DATASET}
   if STATE_FILE.exists():
       params["modified_after"] = STATE_FILE.read_text().strip()

   changed = get_all(f"/api/v1/samples/{SAMPLE_TYPE}/", **params)
   print(f"{len(changed)} samples are new or changed")

   STATE_FILE.write_text(started)
   ```

2. Run it with `python read_changes.py`. The first run has no earlier read to compare with, so it returns every sample.
3. Run it again later. It asks for the samples changed since the time the previous run began.

The script takes the time before it reads and saves it only after the read has finished. A record changed while the script runs is then read again on the next run, rather than missed. `modified_after` includes records changed at that exact moment, so a record can come back twice. Match your local copy on `uuid` and replace the old version.

## The result

`changed` holds the samples added or changed since the last run, and `last-read.txt` holds the time the latest run began.

A record that someone deleted does not appear in any list, so this finds new and changed records only. To notice deletions, read the full list now and then and drop the local records that are no longer in it.

## Next

- To read only records changed before a moment, send `modified_before` with the same kind of value.
- The [REST API reference](../../developers/reference/rest-api.md) describes both filters, including how a date without a time, and a time without an offset, are read.
