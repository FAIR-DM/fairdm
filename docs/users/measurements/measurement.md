# The measurement page

A measurement's page gathers what the portal holds about one measurement: its result, how it was made, the sample it was made on and who is credited on it. The heading is the measurement's name, or its portal ID when it has no name. This page describes what every measurement type's page shows. It does not describe the screens for changing a measurement, which the **Edit** on each panel opens.

## How to reach it

Choose a measurement's name in a [measurements table](measurements.md), in the **Measurements** card of a [sample's page](../samples/sample.md), or in the **Other measurements on this sample** panel of another measurement's page.

The address is `/measurements/` followed by the measurement's portal ID. The portal ID alone, after the portal's address, also opens it: `/` followed by the portal ID is the measurement's permalink. A measurement has two tabs: **Overview**, which this page describes, and **Contributors**, described on [Contributors](../contributors/contributors-tab.md).

Who may open the page is explained in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## Notices

A measurement whose dataset is not public shows, above the header, "Only people with access to this dataset can see this measurement until it is published."

## The header

The header is a band in the measurement's colour. A measurement with an image shows it filling the header's right-hand side, and on a phone as a banner above the header. Selecting the image opens it at full size. A measurement without one shows the measurement icon on a ruled grid. The header shows:

- The measurement's type as a badge. When the portal describes the type, the badge is a button headed "About" and the type's name. It opens a dialog with the type's description, its keywords, the authority whose schema it follows and the protocol it cites, and you close it with **Close**.
- The measurement's name, or its portal ID.
- A line of key facts, each a link:
    - **Measured on**: the sample, when you may open it.
    - **Dataset**: the measurement's dataset.
    - The first identifier that resolves, such as a DOI, labelled with its type.
- Its keywords, as badges. These are keywords chosen from a controlled vocabulary. People who may change the measurement see **Edit** beside them, or **Add keywords** when there are none.
- Buttons: **Cite**, which jumps to the Cite panel, **Share**, and for people who may change the measurement **Edit**, which opens [Edit details](edit-details.md).

**Share** opens a menu headed "Share this page" with Facebook, X / Twitter, Reddit, Pinterest, **Email** and **Copy link**. Every choice shares the measurement's permalink, and **Copy link** copies it.

There is no menu of editing screens. Each part of the measurement is edited from the panel that shows it, and a control appears only for someone who may use its screen.

## Result

The foot of the header shows the measurement's result, headed **Result**: the value in large type, with its uncertainty and units when the type records them. It appears when the measurement's type defines a value. A type that records its result another way draws it here in its own form, with notes such as a detection limit beside the value. This is where a portal's own result appears.

## Your type's own content

A measurement type can add panels of its own to the wide column, above the procedure. This is where a portal's own fields appear on the page, usually as a panel of properties, each a label over its value, with a dash where nothing is recorded. People who may change the measurement see **Edit** on it, which opens [Edit details](edit-details.md). A type that adds nothing shows nothing here.

## How it was measured

A panel headed **How it was measured** lays the procedure out as a timeline, the date on the left of each step. Each step combines a date, the people credited in the matching role and the matching description:

| Step | Date | Role | Description |
|---|---|---|---|
| Set up | Setup date | Preparation | Preparation |
| Measured | none | Collection | Conditions |
| Taken down | Tear down date | none | Tear Down |

Steps with a date come first, in date order, and the others follow. A date recorded only to the year or the month is shown as recorded. People who may change the measurement see **Edit**, which opens [Key dates](../editing-a-record/key-dates.md).

When nothing is recorded, a person who may change the measurement's dataset reads "Nothing is recorded about how this measurement was made. The setup and conditions are what let someone else judge whether the value is comparable with theirs." Anyone else reads "No details of how this measurement was made have been recorded."

## Notes

A panel headed **Notes** shows the measurement's description of type Other. It is left out when there is none. People who may change the measurement see **Edit**, which opens [Descriptions](../editing-a-record/descriptions.md).

## Measured on

A panel headed **Measured on** shows the sample the measurement was made on, as a small version of the sample's own header: its image or icon, its type, its status badge, its name as a link, its local ID and the dataset it belongs to.

When the sample's dataset is not published you cannot open the sample, and the panel reads "The sample this was measured on belongs to a dataset that hasn't been published yet."

When you may open the sample and it is in a different dataset from the measurement, a note adds "This measurement and its sample are recorded in different datasets. That's normal when one group measures specimens another group collected."

## Other measurements on this sample

A panel with this heading lists the other measurements made on the same sample in a table, newest first, with a count beside the heading. The columns are **Measurement** (its name as a link), **Type**, **Dataset** ("This dataset" when it is the measurement's own) and **Added**. On a phone each row becomes a short entry, the name above the rest. The table lists the first twelve, and "and" followed by a count and "more" stands for the rest. When you may open the sample, **See all** and that count open the sample's **Measurements** tab, which lists every one. You see only measurements whose own dataset you may see. The panel is left out when there are none.

## Cite

A panel headed **Cite**, at the top of the side column, gives the citation as plain text, and a **Copy** button copies it. The measurement is cited by the people credited with the Collection role, the year of its setup date (or the year it was added), its name, its type and the sample, and the DOI link or, with no DOI, the measurement's permalink.

A measurement with no DOI reads "Most measurements are cited through their dataset. This citation points at this page." with a **Cite the dataset** link to the dataset's Cite panel.

## Location

A panel straight after **Cite** shows where the measurement was made.

- A measurement with a location of its own gets a panel headed **Where it was measured**, with a map and the coordinates. People who may change the measurement see **Edit** on it, which opens [Edit details](edit-details.md).
- A measurement with none shows its sample's location under **Where the sample was taken**, when you may open the sample and the sample has one.
- With no location to show, the panel reads "No location has been recorded for the sample." or, when you may not open the sample, "The sample belongs to a dataset that has not been published, so its location is not shown."

The coordinates are **Latitude** and **Longitude** to five decimal places, then **Elevation** and **Uncertainty** in metres when they are recorded, in decimal degrees (WGS 84). The map's tile credits sit behind the (i) button in its corner.

## Details

A panel headed **Details** holds the measurement's facts in sections. A fact with no value shows a dash. People who may change the measurement see **Edit** on it, which opens Edit details. The first section has one row for each of these, in order:

- **Project**, when the measurement's project is visible to you.
- **Dataset**.
- **Licence**, from the dataset. A dataset with no licence shows "None chosen yet" in a warning colour, with the note "Nobody can safely reuse this data until a licence is chosen."
- **Added** and **Last updated**.

**Identifiers** follows. It lists each identifier the measurement carries with its type. A DOI that starts with `10.` links to doi.org. Below them are the measurement's **Local ID**, when it has one, its **Portal ID** and its **Permalink**. Each identifier, the portal ID and the permalink have a button that copies it. People who may change the measurement see **Edit**, which opens [Identifiers](../editing-a-record/identifiers.md).

**For machines** has a **REST API** button that opens the measurement's address in the API. People who may delete the measurement see **Delete this measurement** as the last line, which opens [Delete](../editing-a-record/delete.md).

## People

A panel headed **People** names the first six people credited, each with their roles and the organization they are credited from, then shows up to ten more as faces, each linked to their page, and counts the rest. **See all** opens the [Contributors](../contributors/contributors-tab.md) tab, and for people who may manage the measurement **Manage** does. With nobody credited it says "No one is credited yet."

## What you can do here

- Cite the measurement, copy its citation or share the page.
- Open the type's description from the type badge.
- Open the measurement's sample, dataset and project from the cards, and the other measurements on the sample.
- See everyone credited with **See all**, and [change who is credited](../contributors/contributors-tab.md).
- Change the measurement, if you may, from the **Edit** on the panel that shows each part:
    - the header's **Edit**, described on [Edit details](edit-details.md)
    - **Edit** on Notes, described on [Descriptions](../editing-a-record/descriptions.md)
    - **Edit** beside the keywords, described on [Keywords](../editing-a-record/keywords.md)
    - **Edit** on How it was measured, described on [Key dates](../editing-a-record/key-dates.md)
    - **Edit** beside Identifiers, described on [Identifiers](../editing-a-record/identifiers.md)
    - **Delete this measurement**, described on [Delete](../editing-a-record/delete.md). To do it, see [How to delete a measurement](delete-a-measurement.md).
