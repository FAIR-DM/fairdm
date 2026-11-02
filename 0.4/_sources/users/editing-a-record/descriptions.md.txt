# Descriptions

The Descriptions screen is where the prose about a record is written: a set of labelled text areas, one for each kind of description the record supports. Projects, datasets, samples and measurements all have it. The screen is the same on all four, and only the areas differ.

## How to reach it

Open the record's page, choose **Manage**, then **Edit descriptions**. The address is the record's own address followed by `descriptions/`:

| Record | Address |
|---|---|
| Project | `/projects/<portal ID>/descriptions/` |
| Dataset | `/datasets/<portal ID>/descriptions/` |
| Sample | `/samples/<portal ID>/descriptions/` |
| Measurement | `/measurement/<portal ID>/descriptions/` |

You see the entry when you may change the record. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) for who that is, and for what you are told when you ask for the screen without that right.

## The text areas

The screen has one text area for each description type the record's kind offers. Each is labelled with the type's name and carries the type's definition as help text. Every area is optional, and each holds one passage.

A description is written in markdown. An area takes up to 20,000 characters.

### Which areas each kind has

| Record | Areas, in the order the screen shows them |
|---|---|
| Project | Abstract, Introduction, Background, Objectives, Expected Output, Conclusions, Other |
| Dataset | Abstract, Methods, Series Information, Technical Information, Other |
| Sample | Collection, Preparation, Storage, Destruction, Other |
| Measurement | Conditions, Preparation, Tear Down, Other |

### What shows when an area is empty

An area you leave empty has no description. The record's page leaves it out, or shows its own empty message. On a sample's page the History timeline says "No history has been recorded for this specimen." and, on a measurement's page, the procedure says "No details of how this measurement was made have been recorded."

## Where each description appears

On a sample's page, **Other** appears in the **Notes** card. **Collection**, **Preparation**, **Storage** and **Destruction** appear as the notes of the matching steps in the **History** card. See [The sample page](../samples/sample.md).

On a measurement's page, **Other** appears in the **Notes** card. **Preparation**, **Conditions** and **Tear Down** appear as the notes of the steps in the **How it was measured** card. See [The measurement page](../measurements/measurement.md).

For where a project's and a dataset's descriptions appear, see [The project page](../projects/project.md) and [The dataset page](../datasets/dataset.md).

## Saving

Choose **Save & continue** or **Save & continue editing**. Saving writes each area you filled in and deletes the description for each area you emptied. You arrive on the record's page, which shows "Saved" followed by the record's name.

## What you can do here

- Write, change or remove a description, then save.
- Leave without saving by going back to the record's page.
- Change the record's other details: [Keywords](keywords.md), [Key dates](key-dates.md) and [Identifiers](identifiers.md).
