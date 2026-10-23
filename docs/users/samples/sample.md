# The sample page

A sample's page gathers what the portal holds about one sample: its custody status, its history, what has been measured on it, where it came from and who is credited on it. The heading is the sample's name. This page describes what every sample type's page shows. It does not describe the screens for changing a sample, which the **Manage** menu opens.

## How to reach it

Choose a sample's name in a [samples table](samples.md), in the **Measured on** card of a [measurement's page](../measurements/measurement.md), or in the **Related** card of another sample's page.

The address is `/samples/` followed by the sample's portal ID and `/overview/`. A sample has two tabs: **Overview**, which this page describes, and **Contributors**, described on [Contributors](../contributors/contributors-tab.md).

Who may open the page is explained in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## Notices

Notices appear above the header, so they are read first.

- A destroyed sample shows "This specimen has been destroyed and can't be re-examined. Its record and measurements are kept."
- A sample whose dataset is not public shows "Only people with access to this dataset can see this sample until it is published."

## The header

The header shows:

- The sample's image, or the sample icon when it has none.
- The sample's type as a badge. When the portal describes the type, the badge is a button headed "About" and the type's name. It opens a dialog with the type's description, its keywords, the authority whose schema it follows and the protocol it cites, and you close it with **Close**.
- The sample's custody status as a second badge: **Available**, **In Use**, **Stored**, **Destroyed**, or **Status unknown** when none was recorded.
- The sample's name.
- Its keywords, as badges. These are keywords chosen from a controlled vocabulary.
- Three buttons: **Cite**, which jumps to the Citation card, **Share**, and **Manage**.

**Share** opens a menu headed "Share this page" with Facebook, X / Twitter, Reddit, Pinterest, **Email** and **Copy link**.

**Manage** opens a menu of the screens for changing the sample. You see only the entries you may use. If you may use none, the button is left out.

## Sample at a glance

Three figures: **Measurements**, **Related samples** and **People credited**. Each is a count, and shows 0 when there is nothing to count.

## Notes

A card headed **Notes** shows the sample's description of type Other. It is left out when the sample has no such description.

## History

A card headed **History** lays the sample's life out as a timeline. Each step combines a date, the people credited in the matching role and the matching description:

| Step | Date | Role | Description |
|---|---|---|---|
| Created | Creation date | none | none |
| Collected | Collection date | Collector | Collection |
| Prepared | Preparation date | Preparer | Preparation |
| Archived | Storage date | Archivist | Storage |
| Returned | Return date | none | none |
| Restored | Restoration date | Restorer | none |
| Destroyed | Destruction date | Destroyer | Destruction |

Steps with a date come first, in date order, and the others follow. A date recorded only to the year or the month is shown as recorded.

When nothing is recorded, a person who may change the dataset reads "Nothing is recorded about how this specimen was collected, prepared or stored. Those dates and notes are what lets someone else trust and reuse its measurements." Anyone else reads "No history has been recorded for this specimen."

## Measurements

A card headed **Measurements** lists the measurements made on the sample, newest first, with a count in the card's corner. Each row has the measurement's name, a badge for its type, the date it was added and, when the measurement belongs to a different dataset from the sample, the dataset's name. The card lists the first ten and says "and" followed by a count and "more" for the rest. You see only measurements whose own dataset you may see.

With none, it reads "No measurements have been made on this sample yet."

## Your type's own content

A sample type can add cards of its own to the wide column, above Notes. This is where a portal's own fields appear on the page. A type that adds nothing shows nothing here.

## Location

A card headed **Location** shows a map with the point marked, then **Latitude** and **Longitude** to five decimal places. **Elevation** and **Uncertainty** follow, in metres, when they are recorded. The coordinates are decimal degrees in WGS 84.

With no location it reads "No location has been recorded for this sample."

## Related

A card headed **Related** lists the samples this one is a parent or a subsample of, with the relation (**Parent sample** or **Subsample**), the type and, for a sample in another dataset, that dataset. A count sits in the corner.

Samples in datasets you may not see are not named. The card says how many there are, as "1 related sample belongs to a dataset that hasn't been published yet." With nothing related it reads "No related samples have been recorded."

## Details

A card headed **Details** has one entry for each of these, in order:

- **Project**, when the sample's project is visible to you.
- **Dataset**.
- **Licence**, from the dataset. A dataset with no licence shows "None chosen yet" in a warning colour, with the note "Nobody can safely reuse this data until a licence is chosen."
- **Status**, with a line saying what the status means for anyone hoping to re-examine the specimen.
- **Added** and **Last updated**.
- **For machines**, with a **REST API** button that opens the sample's address in the API.

## People

A card headed **People** shows the faces of everyone credited, up to 18, with the name on hover. When there are more it says "and" followed by a count and "other contributors". **See all** opens the [Contributors](../contributors/contributors-tab.md) tab. With nobody credited it reads "No one is credited yet."

## Identifiers

A card headed **Identifiers** lists each identifier the sample carries with its type. A DOI or IGSN that starts with `10.` links to doi.org. Below them are the sample's **Local ID**, when it has one, and its **Portal ID**, with a button that copies it.

## Citation

A card headed **Citation** gives the citation as plain text, and a **Copy** button copies it. The sample is cited by the people credited as Collector, the year of its collection date (or the year it was added), its name and type, and the IGSN link or the page's address.

A sample with no IGSN reads "This sample has no IGSN, so the citation points at this page. An IGSN gives the physical specimen an identifier that outlives the portal."

## What you can do here

Anything on this page links onward. These are the actions it offers:

- Cite the sample, copy its citation or share the page.
- Open the type's description from the type badge.
- Open the sample's dataset, project, related samples and measurements from the cards.
- See everyone credited with **See all**, and [change who is credited](../contributors/contributors-tab.md).
- Choose **Manage**, then one of:
    - **Edit details**, described on [Edit details](edit-details.md).
    - **Edit descriptions**, described on [Descriptions](../editing-a-record/descriptions.md).
    - **Keywords**, described on [Keywords](../editing-a-record/keywords.md).
    - **Key dates**, described on [Key dates](../editing-a-record/key-dates.md).
    - **Identifiers**, described on [Identifiers](../editing-a-record/identifiers.md).
    - **Delete**, described on [Delete](../editing-a-record/delete.md). To do it, see [How to delete a sample](delete-a-sample.md).
