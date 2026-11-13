# The sample page

A sample's page gathers what the portal holds about one sample: its custody status, its history, what has been measured on it, where it came from and who is credited on it. The heading is the sample's name. This page describes what every sample type's page shows. It does not describe the screens for changing a sample, which the **Edit** controls on its panels open.

## How to reach it

Choose a sample's name in a [samples table](samples.md), in the **Measured on** card of a [measurement's page](../measurements/measurement.md), or in the **Related samples** panel of another sample's page.

The address is `/samples/` followed by the sample's portal ID. The portal ID alone, after the portal's address, also opens it: `/` followed by the portal ID is the sample's permalink. An older link that ends in `/overview/` leads to the same page. A sample has three tabs: **Overview**, which this page describes, **Contributors**, described on [Contributors](../contributors/contributors-tab.md), and **Measurements**, described in [Browse samples and measurements](../datasets/browse-samples-and-measurements.md#browse-a-samples-measurements).

Who may open the page is explained in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## Notices

Notices appear above the header, so they are read first.

- A destroyed sample shows "This specimen has been destroyed and can't be re-examined. Its record and measurements are kept."
- A sample whose dataset is not public shows "Only people with access to this dataset can see this sample until it is published."

## The header

The header is a band in the sample's colour. A sample with an image shows it filling the header's right-hand side, and on a phone as a banner above the header. Selecting the image opens it at full size. A sample without one shows the sample icon on a ruled grid. The header shows:

- The sample's type as a badge. When the portal describes the type, the badge is a button headed "About" and the type's name. It opens a dialog with the type's description, its keywords, the authority whose schema it follows and the protocol it cites, and you close it with **Close**.
- The sample's custody status as a second badge: **Available**, **In Use**, **Stored**, **Destroyed**, or **Status unknown** when none was recorded.
- The sample's name.
- A line of key facts: the sample's **Dataset**, linked to its page, its **Local ID** when it has one, its IGSN or DOI when it has one that resolves, linked to doi.org, and **Taken at** with the coordinates to four decimal places when it has a location. The coordinates jump to the Location panel.
- Its keywords, as badges. These are keywords chosen from a controlled vocabulary. People who may change the sample see **Edit** beside them, or **Add keywords** when there are none.
- Buttons: **Cite**, which jumps to the Cite panel, **Share**, and for people who may change the sample **Edit**, which opens [Edit details](edit-details.md).

**Share** opens a menu headed "Share this page" with Facebook, X / Twitter, Reddit, Pinterest, **Email** and **Copy link**. Every choice shares the sample's permalink, and **Copy link** copies it.

There is no menu of editing screens. Each part of the sample is edited from the panel that shows it, and a control appears only for someone who may use its screen.

## Sample at a glance

Three figures along the foot of the header: **Measurements**, **Related samples** and **People credited**. Each is a count, and shows 0 when there is nothing to count. **Measurements** jumps to the Measurements panel and **Related samples** to the Related samples panel, with a line under it such as "1 parent · 2 subsamples". **People credited** opens the [Contributors](../contributors/contributors-tab.md) tab.

## Notes

A panel headed **Notes** shows the sample's description of type Other. It is left out when the sample has no such description. People who may change the sample see **Edit**, which opens [Descriptions](../editing-a-record/descriptions.md).

## History

A panel headed **History** lays the sample's life out as a timeline, the date on the left of each step. Each step combines a date, the people credited in the matching role and the matching description:

| Step | Date | Role | Description |
|---|---|---|---|
| Created | Creation date | none | none |
| Collected | Collection date | Collector | Collection |
| Prepared | Preparation date | Preparer | Preparation |
| Archived | Storage date | Archivist | Storage |
| Returned | Return date | none | none |
| Restored | Restoration date | Restorer | none |
| Destroyed | Destruction date | Destroyer | Destruction |

Steps with a date come first, in date order, and the others follow. A date recorded only to the year or the month is shown as recorded. People who may change the sample see **Edit**, which opens [Key dates](../editing-a-record/key-dates.md).

When nothing is recorded, a person who may change the dataset reads "Nothing is recorded about how this specimen was collected, prepared or stored. Those dates and notes are what lets someone else trust and reuse its measurements." Anyone else reads "No history has been recorded for this specimen."

## Measurements

A panel headed **Measurements** lists the measurements made on the sample, newest first, with a count beside the heading. Each row has the measurement's name, its type, the date it was added on the right and, when the measurement belongs to a different dataset from the sample, the dataset's name. The panel lists the first thirty and says "and" followed by a count and "more" for the rest. **See all** opens the sample's **Measurements** tab, which lists every one. You see only measurements whose own dataset you may see.

When the measurements are of more than one type, a row of buttons above the list filters it: **All**, then one button per type with how many there are, the most measured type first. Choosing a type shows only its rows and hides "and … more", and **All** shows every row again.

With none, it reads "No measurements have been made on this sample yet."

## Your type's own content

A sample type can add panels of its own to the wide column, above Notes. This is where a portal's own fields appear on the page, usually as a panel of properties, each a label over its value, with a dash where nothing is recorded. People who may change the sample see **Edit** on it, which opens Edit details. A type that adds nothing shows nothing here.

## Cite

A panel headed **Cite**, at the top of the side column, gives the citation as plain text, and a **Copy** button copies it. The sample is cited by the people credited as Collector, the year of its collection date (or the year it was added), its name and type, and the IGSN link or, with no IGSN, the sample's permalink.

A sample with no IGSN reads "This sample has no IGSN, so the citation points at this page. An IGSN gives the physical specimen an identifier that outlives the portal."

## Location

A panel headed **Location**, straight after Cite, shows a map with the point marked, then **Latitude** and **Longitude** to five decimal places. **Elevation** and **Uncertainty** follow, in metres, when they are recorded. The coordinates are decimal degrees in WGS 84. The map's tile credits sit behind the (i) button in its corner. People who may change the sample see **Edit**, which opens Edit details.

With no location it reads "No location has been recorded for this sample."

## Details

A panel headed **Details** holds the sample's facts in sections. A fact with no value shows a dash. People who may change the sample see **Edit** on it, which opens Edit details. The first section has one row for each of these, in order:

- **Project**, when the sample's project is visible to you.
- **Dataset**.
- **Licence**, from the dataset. A dataset with no licence shows "None chosen yet" in a warning colour, with the note "Nobody can safely reuse this data until a licence is chosen."
- **Status**, with a line saying what the status means for anyone hoping to re-examine the specimen.
- **Added** and **Last updated**.

**Identifiers** follows. It lists each identifier the sample carries with its type. A DOI or IGSN that starts with `10.` links to doi.org. Below them are the sample's **Local ID**, when it has one, its **Portal ID** and its **Permalink**. Each identifier, the portal ID and the permalink have a button that copies it. People who may change the sample see **Edit**, which opens [Identifiers](../editing-a-record/identifiers.md).

**For machines** has a **REST API** button that opens the sample's address in the API. People who may delete the sample see **Delete this sample** as the last line, which opens [Delete](../editing-a-record/delete.md).

## Related samples

A panel headed **Related samples** lists the samples this one is a parent or a subsample of, with the relation (**Parent sample** or **Subsample**) and, for a sample in another dataset, that dataset. A count sits beside the heading.

Samples in datasets you may not see are not named. The panel says how many there are, as "1 related sample belongs to a dataset that hasn't been published yet." With nothing related it reads "No related samples have been recorded."

## People

A panel headed **People** names the first six people credited, each with their roles and the organization they are credited from, then shows up to ten more as faces, each linked to their page, and counts the rest. **See all** opens the [Contributors](../contributors/contributors-tab.md) tab, and for people who may manage the sample **Manage** does. With nobody credited it says "No one is credited yet."

## What you can do here

Anything on this page links onward. These are the actions it offers:

- Cite the sample, copy its citation or share the page.
- Open the type's description from the type badge.
- Open the sample's dataset, project, related samples and measurements from the header and the panels.
- Filter the measurements by type.
- See everyone credited with **See all**, and [change who is credited](../contributors/contributors-tab.md).
- Change the sample, if you may, from the **Edit** on the panel that shows each part:
    - the header's **Edit**, described on [Edit details](edit-details.md)
    - **Edit** on Notes, described on [Descriptions](../editing-a-record/descriptions.md)
    - **Edit** beside the keywords, described on [Keywords](../editing-a-record/keywords.md)
    - **Edit** on the type's properties and on Location, described on [Edit details](edit-details.md)
    - **Edit** on History, described on [Key dates](../editing-a-record/key-dates.md)
    - **Edit** beside Identifiers, described on [Identifiers](../editing-a-record/identifiers.md)
    - **Delete this sample**, described on [Delete](../editing-a-record/delete.md). To do it, see [How to delete a sample](delete-a-sample.md).
