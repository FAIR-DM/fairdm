# The measurement page

A measurement's page gathers what the portal holds about one measurement: its result, how it was made, the sample it was made on and who is credited on it. The heading is the measurement's name, or its portal ID when it has no name. This page describes what every measurement type's page shows. It does not describe the screens for changing a measurement, which the **Manage** menu opens.

## How to reach it

Choose a measurement's name in a [measurements table](measurements.md), in the **Measurements** card of a [sample's page](../samples/sample.md), or in the **Other measurements on this sample** card of another measurement's page.

The address is `/measurement/` followed by the measurement's portal ID. A measurement has two tabs: **Overview**, which this page describes, and **Contributors**, described on [Contributors](../contributors/contributors-tab.md).

Who may open the page is explained in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## Notices

A measurement whose dataset is not public shows, above the header, "Only people with access to this dataset can see this measurement until it is published."

## The header

The header shows:

- The measurement's image, or the measurement icon when it has none.
- The measurement's type as a badge. When the portal describes the type, the badge is a button headed "About" and the type's name. It opens a dialog with the type's description, its keywords, the authority whose schema it follows and the protocol it cites, and you close it with **Close**.
- The measurement's name, or its portal ID.
- Its keywords, as badges. These are keywords chosen from a controlled vocabulary.
- Three buttons: **Cite**, which jumps to the Citation card, **Share**, and **Manage**.

**Share** opens a menu headed "Share this page" with Facebook, X / Twitter, Reddit, Pinterest, **Email** and **Copy link**.

**Manage** opens a menu of the screens for changing the measurement. You see only the entries you may use. If you may use none, the button is left out.

## Result

A card headed **Result** shows the measurement's value, with its uncertainty and units when the type records them. It appears when the measurement's type defines a value. A type that records its result another way draws it here in its own form. This is where a portal's own result appears.

## Your type's own content

A measurement type can add cards of its own to the wide column, above the procedure. A type that adds nothing shows nothing here.

## How it was measured

A card headed **How it was measured** lays the procedure out as a timeline. Each step combines a date, the people credited in the matching role and the matching description:

| Step | Date | Role | Description |
|---|---|---|---|
| Set up | Setup date | Preparation | Preparation |
| Measured | none | Collection | Conditions |
| Taken down | Tear down date | none | Tear Down |

Steps with a date come first, in date order, and the others follow. A date recorded only to the year or the month is shown as recorded.

When nothing is recorded, a person who may change the measurement's dataset reads "Nothing is recorded about how this measurement was made. The setup and conditions are what let someone else judge whether the value is comparable with theirs." Anyone else reads "No details of how this measurement was made have been recorded."

## Notes

A card headed **Notes** shows the measurement's description of type Other. It is left out when there is none.

## Measured on

A card headed **Measured on** shows the sample the measurement was made on: its image or icon, its type, its status badge, its name as a link, its local ID, the dataset it belongs to and its keywords.

When the sample's dataset is not published you cannot open the sample, and the card reads "The sample this was measured on belongs to a dataset that hasn't been published yet."

When the sample is in a different dataset from the measurement, a notice adds "This measurement and its sample are recorded in different datasets. That's normal when one group measures specimens another group collected."

## Other measurements on this sample

A card with this heading lists the other measurements made on the same sample, newest first, with a count in the corner. Each row has the measurement's name, its type, the dataset when it differs from this one, and the date it was added. The card lists the first eight and says "and" followed by a count and "more" for the rest. You see only measurements whose own dataset you may see. The card is left out when there are none.

## Location

A card shows where the measurement was made.

- A measurement with a location of its own gets a card headed **Measurement location**, with a map and the coordinates.
- A measurement with none shows its sample's location under **Sample location**, when you may open the sample and the sample has one.
- With no location to show, the card reads "No location has been recorded for the sample." or, when you may not open the sample, "The sample belongs to a dataset that has not been published, so its location is not shown."

The coordinates are **Latitude** and **Longitude** to five decimal places, then **Elevation** and **Uncertainty** in metres when they are recorded, in decimal degrees (WGS 84).

## Details

A card headed **Details** has one entry for each of these, in order:

- **Project**, when the measurement's project is visible to you.
- **Dataset**.
- **Licence**, from the dataset. A dataset with no licence shows "None chosen yet" in a warning colour, with the note "Nobody can safely reuse this data until a licence is chosen."
- **Added** and **Last updated**.
- **For machines**, with a **REST API** button that opens the measurement's address in the API.

## People

A card headed **People** shows the faces of everyone credited, up to 18, with the name on hover. When there are more it says "and" followed by a count and "other contributors". **See all** opens the [Contributors](../contributors/contributors-tab.md) tab. With nobody credited it reads "No one is credited yet."

## Identifiers

A card headed **Identifiers** lists each identifier the measurement carries with its type. A DOI that starts with `10.` links to doi.org. Below them are the measurement's **Local ID**, when it has one, and its **Portal ID**, with a button that copies it.

## Citation

A card headed **Citation** gives the citation as plain text, and a **Copy** button copies it. The measurement is cited by the people credited with the Collection role, the year of its setup date (or the year it was added), its name, its type and the sample, and the DOI link or the page's address.

A measurement with no DOI reads "Most measurements are cited through their dataset. This citation points at this page." with a **Cite the dataset** link to the dataset's Citation card.

## What you can do here

- Cite the measurement, copy its citation or share the page.
- Open the type's description from the type badge.
- Open the measurement's sample, dataset and project from the cards, and the other measurements on the sample.
- See everyone credited with **See all**, and [change who is credited](../contributors/contributors-tab.md).
- Choose **Manage**, then one of:
    - **Edit details**, described on [Edit details](edit-details.md).
    - **Edit descriptions**, described on [Descriptions](../editing-a-record/descriptions.md).
    - **Keywords**, described on [Keywords](../editing-a-record/keywords.md).
    - **Key dates**, described on [Key dates](../editing-a-record/key-dates.md).
    - **Identifiers**, described on [Identifiers](../editing-a-record/identifiers.md).
    - **Delete**, described on [Delete](../editing-a-record/delete.md). To do it, see [How to delete a measurement](delete-a-measurement.md).
