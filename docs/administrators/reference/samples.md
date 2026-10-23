# Samples

The Samples screens of the administration interface list the samples in the portal, including those in private datasets, and open each for editing. There is one list for samples of every type and one list for each sample type the portal registers. This page describes both.

You reach the list of every type by opening the administration interface and choosing **Samples** under **Sample**. A portal's registered types, such as rock samples, appear beside it with a list each. The address of the administration interface is described under [Reaching the administration interface](portal-roles.md#reaching-the-administration-interface).

Opening a list needs the permission to view samples, which the Data Curator role holds. Adding or changing a sample of a type needs the permissions of that type, which the four [portal roles](portal-roles.md) do not hold. A superuser does.

## The list

The lists show the oldest sample first. A sample's name opens its form, in the admin of the sample's own type.

### Columns

| Column | What it shows |
|---|---|
| Name | The sample's name |
| Dataset | The dataset the sample belongs to |
| Status | The custody status: **Available**, **In Use**, **Stored**, **Destroyed** or **Unknown** |
| Sample Type | The type's name, such as "rock sample" |
| Location | The sample's point, or a dash |
| Date added | When the sample was added |
| Last modified | When the sample was last saved |

A type's own list can add columns for its own fields. FairDM adds none.

### Search

The search box matches part of any of these, whatever its case:

- The sample's name.
- Its **Local ID**.
- Its portal ID.

A type's own list can search more fields.

### Filters

| Filter | Choices | Shown on |
|---|---|---|
| Type | **All** and each type you may change | The list of every type only |
| Dataset | Every dataset in the portal, private ones included | Both |
| Status | **All**, **Available**, **In Use**, **Stored**, **Destroyed**, **Unknown** | Both |
| Date added | **Any date**, **Today**, **Past 7 days**, **This month**, **This year** | Both |

### Actions

The only action is Django's own **Delete selected samples**. The screens offer no export, no import, no change of status and no move to another dataset. A sample that has measurements cannot be deleted until its measurements are.

### When the list is empty

The list reads "0 samples" and shows no rows. A search or filter that matches nothing shows the same.

## The sample form

Adding a sample first asks for its type, under the heading **Type**, with a choice of the types you may add. Editing opens the form of the sample's own type.

The form has these sections.

| Section | Fields | Notes |
|---|---|---|
| First, with no heading | **Name**, **Dataset**, **Local ID**, **Status**, **Location**, **Elevation**, **Uncertainty** | **Dataset** is a search box. **Status** starts as **Unknown**. **Elevation** and **Uncertainty** need a location |
| Contents | The fields the sample's type adds | Left out when the type adds none |
| Metadata | **UUID**, **Date added**, **Last modified** | Collapsed, and read-only |

A sample can be saved only as one of the registered types. A sample that was never given a type cannot be saved.

Moving a sample to another dataset is refused when it would leave the sample with nobody who can sign in and manage it. The message begins "Nobody who can sign in would be able to manage this sample there."

### Inlines

The sections below the fields hold the rows attached to the sample. They start with no rows and each has an **Add another** link.

| Section | Layout | Fields | Rows |
|---|---|---|---|
| Descriptions | Stacked | **Type**, **Value** | One per type: **Collection**, **Preparation**, **Storage**, **Destruction**, **Other** |
| Dates | Stacked | **Type**, **Value** | One per type: **Creation date**, **Destruction date**, **Collection date**, **Return date**, **Preparation date**, **Storage date**, **Restoration date** |
| Identifiers | Stacked | **Type**, **Value** | One per type: **IGSN**, **DOI** |
| Contributors | Table | **Contributor**, **Roles**, **Affiliation**, **Level** | No limit |
| Sample relationships | Table | **Type**, **Target** | No limit |

A date takes a year (`2024`), a year and month (`2024-06`) or a full date (`2024-06-01`).

An identifier's value is stored without a display prefix such as `https://doi.org/` or `igsn:`. It has to be unique among the identifiers of every kind of record, not only samples. A value of the type **IGSN** has to be a DataCite DOI (`10.NNNN/…`) or a legacy handle beginning `10273/`.

In **Contributors**, **Roles** lists every role of the shared roles vocabulary, including roles meant for a project or a dataset. The roles for a sample are **Collector**, **Preparer**, **Archivist**, **Destroyer** and **Restorer**. **Level** is **Can view**, **Can edit** or **Can manage**, and it is empty for an organization. A person saved with an empty level is credited with no access.

In **Sample relationships**, **Type** offers one value, **child of**, and **Target** is the sample this one came from. The rows record the sample as the source of each link, so a parent's form does not list its children. A sample cannot be related to itself, a link cannot be recorded when its reverse exists, and the same link cannot be recorded twice.

## What you can do here

- Add a sample. See [How to add a sample in the administration interface](../how-to/add-a-sample-in-the-admin.md).
- Record that a sample came from another sample. See [How to record that a sample came from another sample](../how-to/record-where-a-sample-came-from.md).
