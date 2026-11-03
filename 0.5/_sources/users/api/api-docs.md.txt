# API documentation

The API documentation screen lists every address the portal's API serves, with its fields and filters, and lets you send a request and read the answer. Use it to find out what your portal offers before you write a script. The facts behind each address are on the [REST API reference](../../developers/reference/rest-api.md).

## How to reach it

You do not need to sign in. Open it in any of these ways:

- Choose **API** in the **Documentation** group of the sidebar.
- Choose **API docs** in the footer of the portal's landing page, or the **API docs** button in the landing page's API section.
- Go to `/api/v1/docs/` on your portal.

The same description is available to tools at `/api/v1/schema/`. Add `?format=json` for JSON.

## Introduction

The top of the screen shows the API's title and version, and the description your portal gives it. The description lists the kinds of record the API serves and how to filter and sort a list. Your portal's developers may have changed the title and the text.

Three sections follow, written from the portal's own settings so they match what it does:

- **Authentication** says how to identify yourself, with a token or from a page of the portal.
- **Limits** lists how often a caller may send requests. Each line names a limit and its rate, such as `anon_burst: 30/minute`. The names starting `anon` apply to requests without a token, and those starting `user` to requests with one. `burst` limits a minute and `day` limits a day.
- **Paging** gives the number of records in a page and the most you may ask for with `page_size`.

## Authorize

The **Authorize** button opens a box for your token. Enter `Token` and a space, then your token, such as `Token 1a2b3c…`, and choose **Authorize**. Requests you send from the screen then carry it, as you. Without it they are sent as a visitor. Get a token with [How to get an API token](get-an-api-token.md).

## The sections of operations

Below the introduction, the operations are grouped under a heading for each kind of record, in this order:

- **Projects**
- **Datasets**
- **People**
- **Organizations**
- **Samples**, which holds every sample type
- **Measurements**, which holds every measurement type

A portal that has no sample types or no measurement types has no heading for them. People and organizations can only be read, so they list two operations each. A project, dataset, sample type or measurement type lists operations to list, read, create, replace, change and delete.

In **Samples** and **Measurements** each operation is titled with the type's plural name and what it does, such as "Rock Samples: list". The list operation of a type also carries the description your portal gives the type and, where it has them, the authority behind it, how to cite it, its keywords and a link to its repository.

## An operation

Choose an operation to open it. It shows:

- the address and the method
- the parameters it takes, which for a list are its filters, `ordering`, `page` and `page_size`
- for an operation that sends data, the fields of the request, with the ones a request must carry marked and the read-only ones marked as such
- the answers it can give, with an example of each

A list shows only the filters that work on that list. If a type has no filters of its own, the list takes the ones every list takes.

## Try it out

**Try it out** turns the parameters into a form. Fill them in, choose **Execute**, and the screen shows the request it sent, the answer and the status code.

```{warning}
A request sent from the screen is a real request. Create, change and delete operations change the portal's records for the account whose token you entered. Try them on records you can afford to lose.
```

## What you can do from here

- [Get an API token](get-an-api-token.md) so the screen and your scripts act as you
- [Read a dataset's samples with a script](read-a-datasets-samples-with-a-script.md)
- [Read only what changed](read-only-what-changed.md)
- [Create a record with the API](create-a-record-with-the-api.md)
- [Change a record with the API](change-a-record-with-the-api.md)
- [Delete a record with the API](delete-a-record-with-the-api.md)
- [Revoke an API token](revoke-an-api-token.md)
