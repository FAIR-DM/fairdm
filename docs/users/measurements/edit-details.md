# Edit details

The Edit details screen changes a measurement's own fields, such as its name, its image, its location and the values its type records. Descriptions, keywords, dates and identifiers have screens of their own. The same screen exists for every measurement type, and each type decides which fields it offers.

## How to reach it

Open the measurement's page, choose **Manage**, then **Edit details**. The address is `/measurement/` followed by the measurement's portal ID and `/edit/`.

You see the entry when you may change the measurement. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) for who that is, and for what you are told when you ask for the screen without that right.

## The form

The form is the one the measurement's type is registered with, less the fields that would move the measurement. A measurement always stays in its dataset and stays on its sample, so neither the dataset field nor the sample field is offered.

The fields every measurement has are listed here. A type can leave any of them out, and it adds its own fields after them, such as a value and its uncertainty. This is where a portal's own fields appear.

| Field | What it holds |
|---|---|
| name | The measurement's name. A measurement with no name is shown by its portal ID |
| image | A picture of the measurement |
| Local ID | The creator's own identifier for the measurement within its dataset |
| location | Where the measurement was made, as a point in WGS 84, with its elevation and uncertainty |

The elevation is in metres above mean sea level, and a negative number is below it. The uncertainty is the distance in metres from the location within which the true place lies. Both need a location. A measurement with no location of its own is shown at its sample's location.

Each field is labelled and shows the help text its type gives it. A field that is refused shows what is wrong beside it, and nothing is saved.

## The buttons

The screen ends with **Save & continue** and **Save & continue editing**. Both save the form and take you to the measurement's page, which shows "Saved" followed by the measurement's name, or its portal ID when it has none.

## What you can do here

- Save your changes to the measurement's own fields.
- Leave without saving by going back to the measurement's page.
- Change the measurement's other details on their own screens: [Descriptions](../editing-a-record/descriptions.md), [Keywords](../editing-a-record/keywords.md), [Key dates](../editing-a-record/key-dates.md) and [Identifiers](../editing-a-record/identifiers.md).
- Delete the measurement. See [How to delete a measurement](delete-a-measurement.md).
