# Reading and writing records with a script

Every portal serves its public projects, datasets, samples and measurements to scripts as well as
to people. This page shows how to read them with Python or `curl`, and how to create, change and
delete the records your team holds. You do not need an account to read public records. Writing
needs a token that belongs to your account.

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
      "html_url": "https://portal.example.org/datasets/dV4DYUk6ohGJdizhxJotoZ8/",
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
returns the same record, `html_url` is the record's own page on the portal's website, and the
address in `project` returns the project.

When a record refers to another it gives the other record's short identifier (`uuid`) and its
address (`url`). Database numbers never appear. If a reference reads `null`, the record it would
name is private and you may not see it.

## Follow a dataset to its samples and measurements

Samples and measurements are served by type. The type is the plural name the portal gives it, such
as `rock-samples`. Ask the portal which types it has, as described in
[Find out what a portal offers](#find-out-what-a-portal-offers).

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

## How much you can ask for

A page holds 100 records. Ask for more with `page_size`, up to 1,000 a page, which reads ten
thousand records in ten requests instead of a hundred:

```bash
curl "https://portal.example.org/api/v1/samples/rock-samples/?page_size=1000"
```

Asking for more than 1,000 gives you 1,000. The portal's administrator may have changed these
figures, and the limits below. The API documentation page at `/api/v1/docs/` lists the ones your
portal uses.

A portal also limits how often a caller may send requests, so one script cannot slow it for
everyone. Without a token you may send 30 requests a minute and 2,000 a day. With a token you may
send 120 a minute and 20,000 a day. A request past a limit is answered `429` and a `Retry-After`
header gives the number of seconds to wait. A script that reads many pages should wait as told:

```python
import time

import requests

response = requests.get(url, params=params, timeout=30)
if response.status_code == 429:
    time.sleep(int(response.headers["Retry-After"]))
    response = requests.get(url, params=params, timeout=30)
```

For a harvest that needs more than the anonymous limits allow, [get a token](#get-a-token) and send
it with every request.

## People and organizations

`/api/v1/contributors/` lists the people and organizations credited on records. Each carries what
its profile page shows, such as its name, biography, ORCID iD or ROR ID and links. It never carries
an email address or anything about an account.

## Records you may not see

A private record is in no list you receive, and asking for it directly is answered `404`, exactly as
for a record that does not exist. The same is true of the samples and measurements in a private
dataset: none is returned and none is counted.

## Get a token

A token proves to the portal that a request comes from you. You make one yourself, after signing
in as usual with your second factor if you use one:

1. Open your account pages and choose **API tokens**, or go to `/account/tokens/` on your portal.
2. Choose to create a token and pick how long it should last, from 7 days to a year, or never.
3. Copy the token from the page you return to. It is shown once and the portal keeps no copy you
   could read later. Keep it somewhere private, as you would a password.

If you lose a token, revoke it and make another. You can hold up to ten at a time, so a laptop and
a server can each have their own.

Your portal may give tokens to some people only. If the page is closed to you, you can still read
public records without one.

Send the token in the `Authorization` header of each request, as shown below. The portal
treats the request as coming from you, with the access you have. A script cannot ask for a token
with an email address and password; the API has no such address.

## Revoke a token

When a laptop is lost or a script is retired, open **API tokens** again, choose the token in the
list and confirm. The next request that carries it is refused with `401`. Your other tokens keep
working. A token that has reached its end date stops working on its own.

## Create a record

Send the record as JSON with your token. `$TOKEN` stands for yours:

```bash
curl -X POST https://portal.example.org/api/v1/samples/rock-samples/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "RS-14", "dataset": "dV4DYUk6ohGJdizhxJotoZ8", "rock_type": "igneous", "collection_date": "2024-05-02"}'
```

The answer is `201` and the new record, complete, with its `uuid` and `url`. In Python:

```python
import requests

headers = {"Authorization": f"Token {token}"}
body = {
    "name": "RS-14",
    "dataset": "dV4DYUk6ohGJdizhxJotoZ8",
    "rock_type": "igneous",
    "collection_date": "2024-05-02",
}
reply = requests.post(
    "https://portal.example.org/api/v1/samples/rock-samples/",
    json=body,
    headers=headers,
    timeout=30,
)
reply.raise_for_status()
sample = reply.json()
```

A record is created inside a parent, named by its short identifier: a sample or a measurement names
its `dataset`, a measurement also names its `sample`, and a dataset names its `project`. You need
the edit level on that parent. Any signed-in person can create a project. A project or dataset you
create is private until you set `visibility` to `1`, and you are listed on every record you create
at the manage level.

## Change a record

`PATCH` changes only the fields you send. Every other field stays as it was:

```bash
curl -X PATCH "https://portal.example.org/api/v1/samples/rock-samples/sxXGUGgXRVStFw3jbpBWQeM/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"weight_grams": 12.5}'
```

`PUT` replaces the record and needs every required field. Both answer `200` with the record as it
now stands. You need the edit level on the record. Changing a record's `visibility`, or moving it by
sending a different `dataset`, `sample` or `project`, needs the manage level. Sending the parent or
visibility a record already has is not a change.

## What you cannot write

Descriptions, key dates, identifiers, keywords and the credited people are read-only. So are a
record's `uuid`, `url`, `html_url`, `added` and `modified`, a project's or dataset's `image`, and a dataset's
`published` and `license`. Send them and the request still succeeds, and they keep the values they
had. Edit those on the record's page in the portal.

## Delete a record

```bash
curl -X DELETE "https://portal.example.org/api/v1/samples/rock-samples/sxXGUGgXRVStFw3jbpBWQeM/" \
  -H "Authorization: Token $TOKEN"
```

The answer is `204`. Deleting needs the manage level on the record. The portal refuses to delete a
project that has a public dataset, and a sample that has measurements made on it, and so does the
API: the answer is `409` with a `detail` that gives the reason, and nothing is deleted. Make the
datasets private, or delete the measurements, and try again.

## When a request is refused

| Answer | Meaning |
|--------|---------|
| `400` | The body is not valid JSON, a field is missing or a value is not acceptable. The answer lists each field at fault and says why. Nothing was saved. A parent that does not exist and one you may not add to are answered the same way. |
| `401` | The request carried no token, or a token that was revoked, has expired or was never made. |
| `403` | You can see the record but your level on it is too low for this request. |
| `404` | The record does not exist, or it is private and you may not see it. |
| `409` | The portal does not allow this delete, as above. |
| `429` | You sent more requests than the portal allows. Wait for the seconds in the `Retry-After` header. |

## Find out what a portal offers

Two addresses list the sample types and the measurement types a portal has registered:

```bash
curl https://portal.example.org/api/v1/samples/
curl https://portal.example.org/api/v1/measurements/
```

Each answers with a `types` list. An entry gives the type's `name`, its display names, the
`endpoint` where its records are and a `count` of the records you may see. A portal with no types of
that kind answers an empty list. The fields and filters of each type are on the API documentation
page described below.

```json
{
  "types": [
    {
      "name": "RockSample",
      "verbose_name": "Rock Sample",
      "verbose_name_plural": "Rock Samples",
      "endpoint": "https://portal.example.org/api/v1/samples/rock-samples/",
      "count": 42
    }
  ]
}
```

The `count` is of the records you may see, so it is smaller for a visitor than for a person with
access to private datasets. To read every record of a type, request its
`endpoint`.

`/api/v1/` itself links to every list the portal serves and to both of these addresses.

## Try it in the browser

The portal's API documentation page lists every address, field and filter, marks the fields a
request must carry and the ones that are read-only, and lets you try a request and read the
response. Open it from **API** in the portal's sidebar, or go to `/api/v1/docs/`. To try a request
that needs a token, choose **Authorize** and enter `Token <your-token>`.

The page is drawn from a machine-readable description at `/api/v1/schema/` (add `?format=json` for
JSON), which tools that generate API clients can read. A second view of the same description is at
`/api/v1/redoc/`.
