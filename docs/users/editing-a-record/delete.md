# Delete

The Delete screen removes a record from the portal for good, after showing what goes with it and asking you to type its name. Projects, datasets, samples and measurements all have it. The screen is the same on all four, and what it lists and what stops a deletion differ.

## How to reach it

Open the record's page, choose **Manage**, then **Delete**. It is the last entry in the menu, set apart from the others by a divider and drawn in red. The address is the record's own address followed by `delete/`:

| Record | Address |
|---|---|
| Project | `/projects/<portal ID>/delete/` |
| Dataset | `/datasets/<portal ID>/delete/` |
| Sample | `/samples/<portal ID>/delete/` |
| Measurement | `/measurement/<portal ID>/delete/` |

You see the entry when you may delete the record, which needs more than the right to change it. Someone who can only edit the record sees the other **Manage** entries and no **Delete**. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) for who may delete, and for what you are told when you ask for the screen without that right.

## The warning

The screen opens with "You are about to permanently delete this record. This action cannot be undone."

## What goes with the record

Below the warning, a list headed "The following related records will also be permanently deleted:" says what is deleted along with the record. It is left out when nothing goes with the record.

- A project or a dataset lists counts rather than rows, because listing every row could run to thousands of lines. The counts come under the headings **Datasets**, **Samples** and **Measurements**, each line giving a type's plural name and its count in brackets.
- A sample or a measurement lists the rows themselves: its descriptions, dates and identifiers and, for a sample, its links to other samples.

Some rows may belong to records you cannot see. A link between samples that names a sample you may not see is not listed. The screen says so with "One more row you do not have access to also goes with this record." or the same sentence for a larger count.

## Confirming

The screen asks you to type the record's name:

- "To confirm, type" followed by the name and "below:" sits above a field headed "Type the name to confirm".
- A measurement with no name is confirmed by typing its portal ID. The screen shows the one to type.
- The **Delete** button stays off until what you type matches exactly.
- **Back** abandons the deletion and returns you to the record's page.

## When the deletion is refused

When something stops the deletion, the screen shows "This record cannot be deleted." and a list of what stands in the way. It has no field and no **Delete** button, only **Back**.

| Record | What stops it | The screen says |
|---|---|---|
| Project | Public datasets inside it | "It holds the following public datasets, which must be removed or made private first:" |
| Dataset | Measurements held in another dataset that were made on its samples | "It is referenced by the following measurements, which must be removed or updated first:" |
| Sample | Measurements made on it | "It is referenced by the following measurements, which must be removed or updated first:" |
| Measurement | Nothing in FairDM stops it | — |

A measurement can belong to a dataset you hold no access to. The screen names only the measurements you may see, by name or by portal ID, and counts the rest with "One more measurement you do not have access to also stops this deletion." or the same sentence for a larger count.

## After deletion

A message reads "Deleted" followed by the record's name, or its portal ID for a measurement with no name. Where you arrive depends on the record.

| Record | You arrive on |
|---|---|
| Project | The projects list |
| Dataset | The datasets list |
| Sample or measurement | The page of its dataset, or the datasets list if you may not open that dataset |

## What you can do here

- Delete the record. For the steps, see [How to delete a project](../projects/delete-a-project.md), [How to delete a dataset](../datasets/delete-a-dataset.md), [How to delete a sample](../samples/delete-a-sample.md) and [How to delete a measurement](../measurements/delete-a-measurement.md).
- Go back to the record without deleting it, with **Back**.
