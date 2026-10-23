# Edit details

The Edit details screen changes a sample's own fields, such as its name, its image, its custody status and its location. Descriptions, keywords, dates and identifiers have screens of their own. The same screen exists for every sample type, and each type decides which fields it offers.

## How to reach it

Open the sample's page, choose **Manage**, then **Edit details**. The address is `/samples/` followed by the sample's portal ID and `/edit/`.

You see the entry when you may change the sample. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) for who that is, and for what you are told when you ask for the screen without that right.

## The form

The form is the one the sample's type is registered with, less the field that would move the sample to another dataset. A sample always stays in its dataset, so the dataset field is never offered.

The fields every sample has are listed here. A type can leave any of them out, and it adds its own fields after them. This is where a portal's own fields appear.

| Field | What it holds |
|---|---|
| name | The sample's name |
| image | A picture of the sample |
| Local ID | The creator's own identifier for the sample within its dataset |
| status | The sample's custody status: **Available**, **In Use**, **Stored**, **Destroyed** or **Unknown**. A sample starts as **Unknown** |
| location | Where the sample was taken, as a point in WGS 84, with its elevation and uncertainty |

The elevation is in metres above mean sea level, and a negative number is below it. The uncertainty is the distance in metres from the location within which the true place lies. Both need a location.

Each field is labelled and shows the help text its type gives it. A field that is refused shows what is wrong beside it, and nothing is saved.

## The buttons

The screen ends with **Save & continue** and **Save & continue editing**. Both save the form and take you to the sample's page, which shows "Saved" followed by the sample's name.

## What you can do here

- Save your changes to the sample's own fields.
- Leave without saving by going back to the sample's page.
- Change the sample's other details on their own screens: [Descriptions](../editing-a-record/descriptions.md), [Keywords](../editing-a-record/keywords.md), [Key dates](../editing-a-record/key-dates.md) and [Identifiers](../editing-a-record/identifiers.md).
- Delete the sample. See [How to delete a sample](delete-a-sample.md).
