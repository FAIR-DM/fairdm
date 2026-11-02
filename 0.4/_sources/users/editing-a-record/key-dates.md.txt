# Key dates

The Key dates screen records the dates that matter in a record's life, such as when a project started or when a sample was collected. Projects, datasets, samples and measurements all have it. The screen is the same on all four, and only the date types differ.

## How to reach it

Open the record's page, choose **Manage**, then **Key dates**. The address is the record's own address followed by `key-dates/`:

| Record | Address |
|---|---|
| Project | `/projects/<portal ID>/key-dates/` |
| Dataset | `/datasets/<portal ID>/key-dates/` |
| Sample | `/samples/<portal ID>/key-dates/` |
| Measurement | `/measurement/<portal ID>/key-dates/` |

You see the entry when you may change the record. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) for who that is, and for what you are told when you ask for the screen without that right.

## The table of dates

The screen is a table with one row for each date the record carries. Each row pairs a **Type** with a **Date**.

- The **Type** menu offers the date types of the record's kind, listed below.
- The **Date** takes a year (`2024`), a year and month (`2024-06`) or a full date (`2024-06-01`). The record shows the date exactly as precisely as you enter it.
- Each row has a **Remove** control, which marks the row for deletion.

A record can carry each type once, so the table never has more rows than the kind has types. **Add row** adds an empty row, and it is switched off once every type has one.

### Which types each kind has

| Record | Date types, in the order the menu shows them |
|---|---|
| Project | Start Date, End Date |
| Dataset | Date Available, Collection Start Date, Collection End Date, Submission Date, Publication Date, Withdrawal Date |
| Sample | Creation date, Destruction date, Collection date, Return date, Preparation date, Storage date, Restoration date |
| Measurement | Setup date, Tear down date |

### When the record has no dates

The table has no rows and shows only **Add row**.

## How kinds differ

A project and a dataset refuse an end that falls before the start, and nothing is saved when one does.

- On a project the pair is **Start Date** and **End Date**. The message reads "The project's end date" followed by the end date, "cannot be before its start date" and the start date.
- On a dataset the pair is **Collection Start Date** and **Collection End Date**. The message reads the same way, with "collection" before each date.

A sample and a measurement have no such pair, so any dates are accepted.

## Where the dates appear

On a sample's page the dates are the steps of the **History** card. See [The sample page](../samples/sample.md). On a measurement's page, **Setup date** and **Tear down date** are the dates of the steps in **How it was measured**. See [The measurement page](../measurements/measurement.md). For a project and a dataset, see [The project page](../projects/project.md) and [The dataset page](../datasets/dataset.md).

## Saving

Choose **Save & continue** or **Save & continue editing**. You arrive on the record's page, which shows "Saved" followed by the record's name.

## What you can do here

- Add a date, change a date or its type, or remove a date, then save.
- Leave without saving by going back to the record's page.
- Change the record's other details: [Descriptions](descriptions.md), [Keywords](keywords.md) and [Identifiers](identifiers.md).
