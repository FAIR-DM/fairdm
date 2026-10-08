# Reading records with a script

Every portal serves its public projects, datasets, samples and measurements to scripts as well as
to people. This page shows how to read them with Python or `curl`. You do not need an account to
read public records.

The portal's address is written below as `https://portal.example.org`. Use your portal's own.

## Find a dataset

Ask for the list of datasets:

```bash
curl https://portal.example.org/api/v1/datasets/
```

The answer is a page of datasets and says how many there are in all:

```json
{
  "count": 42,
  "next": "https://portal.example.org/api/v1/datasets/?page=2",
  "previous": null,
  "results": [
    {
      "url": "https://portal.example.org/api/v1/datasets/dV4DYUk6ohGJdizhxJotoZ8/",
      "uuid": "dV4DYUk6ohGJdizhxJotoZ8",
      "name": "Rock chemistry of the north face",
      "project": {
        "uuid": "pHj2kM9QxLw3tZ7bC4nVfRe",
        "url": "https://portal.example.org/api/v1/projects/pHj2kM9QxLw3tZ7bC4nVfRe/"
      },
      "license": {"name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"},
      "descriptions": [{"type": "Abstract", "value": "..."}],
      "dates": [{"type": "Available", "value": "2024-05"}],
      "identifiers": [{"type": "DOI", "value": "10.1234/example"}],
      "keywords": [],
      "contributors": []
    }
  ]
}
```

Each record is returned whole: its own fields, the record it sits under, its licence or owner, its
descriptions, key dates, identifiers, keywords and the people credited on it. The address in `url`
returns the same record, and the address in `project` returns the project.

When a record refers to another it gives the other record's short identifier (`uuid`) and its
address (`url`). Database numbers never appear. If a reference reads `null`, the record it would
name is private and you may not see it.

## Follow a dataset to its samples and measurements

Samples and measurements are served by type. The type is the plural name the portal gives it, such
as `rock-samples`. The portal's API documentation page lists the types it has.

Narrow a list to one dataset with `dataset`, and a list of measurements to one sample with
`sample`. Both take the short identifier:

```bash
curl "https://portal.example.org/api/v1/samples/rock-samples/?dataset=dV4DYUk6ohGJdizhxJotoZ8"
curl "https://portal.example.org/api/v1/measurements/xrf-measurements/?sample=sd573eit27hDfnZD98NsqsW"
```

A sample comes back with the fields every sample has and every field its type records. A
measurement comes back with its measured values. A database number in `dataset` or `sample` is
refused with a `400` answer.

A type may offer filters of its own, such as `?rock_type=igneous`. Sort a list with `ordering`, and
put a minus sign before the name to sort the other way:

```bash
curl "https://portal.example.org/api/v1/samples/rock-samples/?ordering=-added"
```

## Read every page in Python

```python
import requests

url = "https://portal.example.org/api/v1/samples/rock-samples/"
params = {"dataset": "dV4DYUk6ohGJdizhxJotoZ8", "ordering": "name"}
samples = []

while url:
    page = requests.get(url, params=params, timeout=30)
    page.raise_for_status()
    body = page.json()
    samples.extend(body["results"])
    url, params = body["next"], None

print(f"{len(samples)} samples")
```

Pass `params` on the first request only. The address in `next` already carries them.

## People and organizations

`/api/v1/contributors/` lists the people and organizations credited on records. Each carries what
its profile page shows, such as its name, biography, ORCID iD or ROR ID and links. It never carries
an email address or anything about an account.

## Records you may not see

A private record is in no list you receive, and asking for it directly is answered `404`, exactly as
for a record that does not exist. The same is true of the samples and measurements in a private
dataset: none is returned and none is counted.

## Try it in the browser

The portal's API documentation page lists every address, field and filter, and lets you try a
request. It is linked from the portal's sidebar.
