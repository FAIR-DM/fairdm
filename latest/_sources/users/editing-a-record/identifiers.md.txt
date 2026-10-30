# Identifiers

The Identifiers screen records the identifiers that name a record outside the portal, such as a DOI. Projects, datasets, samples and measurements all have it. The screen is the same on all four, and only the identifier types differ. The portal's own identifier for a record, its portal ID, is made by the portal and is not a row on this screen.

## How to reach it

Open the record's page, choose **Manage**, then **Identifiers**. The address is the record's own address followed by `identifiers/`:

| Record | Address |
|---|---|
| Project | `/projects/<portal ID>/identifiers/` |
| Dataset | `/datasets/<portal ID>/identifiers/` |
| Sample | `/samples/<portal ID>/identifiers/` |
| Measurement | `/measurement/<portal ID>/identifiers/` |

You see the entry when you may change the record. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) for who that is, and for what you are told when you ask for the screen without that right.

## The table of identifiers

The screen is a table with one row for each identifier the record carries. Each row pairs a **Type** with an **Identifier**.

- The **Type** menu offers the identifier types of the record's kind, listed below.
- The **Identifier** is the value, such as `10.5555/example`.
- Each row has a **Remove** control, which marks the row for deletion.

A record can carry each type once, so the table never has more rows than the kind has types. **Add row** adds an empty row, and it is switched off once every type has one.

A value can name only one record in the whole portal, whatever its kind. A value another record already uses is refused with "The identifier" followed by the value and "is already in use." and nothing is saved.

### Which types each kind has

| Record | Identifier types |
|---|---|
| Project | DOI, Grant Number, Proposal Identifier |
| Dataset | DOI |
| Sample | IGSN, DOI |
| Measurement | DOI |

### When the record has no identifiers

The table has no rows and shows only **Add row**.

## How kinds differ

A sample's **IGSN** is checked. You may paste it with a common prefix such as `https://doi.org/`, `https://igsn.org/`, `doi:` or `igsn:`, and the portal removes the prefix. What is left must be a DataCite DOI such as `10.60516/AU1101` or a legacy IGSN handle such as `10273/BGRB5054RX05201`. Anything else is refused with a message that gives both examples.

No other identifier type is checked for its form.

## Where the identifiers appear

The record's page lists every identifier in its **Identifiers** card. A DOI, or an IGSN that starts with `10.`, links to doi.org. The same card shows the record's **Local ID**, when it has one, and its **Portal ID**. A sample's citation uses its IGSN, and a measurement's uses its DOI. See [The sample page](../samples/sample.md) and [The measurement page](../measurements/measurement.md). For a project and a dataset, see [The project page](../projects/project.md) and [The dataset page](../datasets/dataset.md).

## Saving

Choose **Save & continue** or **Save & continue editing**. You arrive on the record's page, which shows "Saved" followed by the record's name.

## What you can do here

- Add an identifier, change one or its type, or remove one, then save.
- Leave without saving by going back to the record's page.
- Change the record's other details: [Descriptions](descriptions.md), [Keywords](keywords.md) and [Key dates](key-dates.md).
