# Measurements

The Measurements screens of the administration interface list the measurements in the portal, including those in private datasets, and open each for editing. There is one list for measurements of every type and one list for each measurement type the portal registers. This page describes both.

You reach the list of every type by opening the administration interface and choosing **Measurements** under **Measurement**. A portal's registered types appear beside it with a list each. The address of the administration interface is described under [Reaching the administration interface](portal-roles.md#reaching-the-administration-interface).

Opening a list needs the permission to view measurements, which the Data Curator role holds. Adding or changing a measurement of a type needs the permissions of that type, which the four [portal roles](portal-roles.md) do not hold. A superuser does.

## The list

The lists show the most recently modified measurement first. A measurement's name opens its form, in the admin of the measurement's own type.

### Columns

| Column | What it shows |
|---|---|
| Name | The measurement's name |
| Sample | The sample the measurement was made on |
| Dataset | The dataset the measurement belongs to |
| Measurement Type | The type's name, such as "XRF measurement" |
| Date added | When the measurement was added |
| Last modified | When the measurement was last saved |

There is no column for the measured value. A type's own list can add columns for its own fields. FairDM adds none.

### Search

The search box matches part of the measurement's name or its portal ID, whatever the case. The sample's name is not searched. To find the measurements made on one sample, use the **Sample** filter.

A type's own list can search more fields.

### Filters

| Filter | Choices | Shown on |
|---|---|---|
| Type | **All** and each type you may change | The list of every type only |
| Dataset | Every dataset in the portal, private ones included | Both |
| Sample | Every sample | Both |
| Date added | **Any date**, **Today**, **Past 7 days**, **This month**, **This year** | Both |

A type's own list can add filters for its own fields. FairDM adds none.

### Actions

The only action is Django's own **Delete selected measurements**. The screens offer no export, no import and no move to another dataset.

### When the list is empty

The list reads "0 measurements" and shows no rows. A search or filter that matches nothing shows the same.

## The measurement form

Adding a measurement first asks for its type, under the heading **Type**, with a choice of the types you may add. Editing opens the form of the measurement's own type.

The form has these sections.

| Section | Fields | Notes |
|---|---|---|
| First, with no heading | **Name**, **Sample**, **Dataset**, **Image**, **Location**, **Elevation**, **Uncertainty** | **Sample** and **Dataset** are search boxes. **Elevation** and **Uncertainty** need a location |
| Contents | The fields the measurement's type adds | Left out when the type adds none |
| Metadata | **UUID**, **Date added**, **Last modified** | Collapsed, and read-only |

A measurement can be saved only as one of the registered types. A measurement that was never given a type cannot be saved, and the type of a saved measurement cannot be changed.

The **Dataset** can differ from the dataset of the **Sample**. Moving a measurement to another dataset is refused when it would leave the measurement with nobody who can sign in and manage it. The message begins "Nobody who can sign in would be able to manage this measurement there."

Where Django needs a label for a measurement, such as a breadcrumb, it shows the value the measurement's type reports, and the name when the type reports none.

### Inlines

The sections below the fields hold the rows attached to the measurement. They start with no rows and each has an **Add another** link.

| Section | Layout | Fields | Rows |
|---|---|---|---|
| Descriptions | Stacked | **Type**, **Value** | One per type: **Conditions**, **Preparation**, **Tear Down**, **Other** |
| Dates | Stacked | **Type**, **Value** | One per type: **Setup date**, **Tear down date** |
| Identifiers | Stacked | **Type**, **Value** | One row, of the type **DOI** |
| Contributors | Table | **Contributor**, **Roles**, **Affiliation**, **Level** | No limit |

A date takes a year (`2024`), a year and month (`2024-06`) or a full date (`2024-06-01`). A date describes the measurement's own set-up and tear-down, not the sample's.

An identifier's value has to be unique among the identifiers of every kind of record, not only measurements.

In **Contributors**, **Roles** lists every role of the shared roles vocabulary, including roles meant for a project, a dataset or a sample. The roles for a measurement are **Preparation**, **Collection** and **Support**. **Level** is **Can view**, **Can edit** or **Can manage**, and it is empty for an organization. A person saved with an empty level is credited with no access.

## What you can do here

- Add a measurement. See [How to add a measurement in the administration interface](../how-to/add-a-measurement-in-the-admin.md).
- Record a measurement against a sample in another dataset. See [How to record a measurement against a sample in another dataset](../how-to/record-a-measurement-against-a-sample-in-another-dataset.md).
