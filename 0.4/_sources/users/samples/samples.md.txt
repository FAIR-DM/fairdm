# Samples

The samples screen is a table of the samples of one sample type, such as the rock samples a portal records. A portal registers its own sample types, so it has one of these screens for each type, and all of them are built the same way. This page describes what they share. It does not describe a single sample, which is on [The sample page](sample.md).

## How to reach it

Open **Samples** in the navigation menu. It holds one entry for each sample type the portal has registered, named with the type's plural name. A portal that has registered no sample types has no **Samples** entry.

A type's screen is at `/collections/samples/` followed by the type's name in lowercase, for example `/collections/samples/rocksample/`.

## Which rows you see

The table lists the samples held in published datasets, and it lists the same rows for every visitor, signed in or not. Your own unpublished samples are not mixed in. You find those on the page of the dataset that holds them. The reasoning is in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## The toolbar

The toolbar sits above the table.

- The heading is the type's plural name, followed by a count of the rows that match.
- A search box narrows the rows by the fields the type's registration lists for search. Unless the registration lists others, that is the sample's name.
- A status filter narrows the rows to one custody status. A type whose filters leave it out does not show it.
- A **Filters** button opens the filter panel beside the table. It shows how many filters are applied.
- A **Switch** menu lists every sample and measurement screen under the headings **Samples** and **Measurements**, with the one you are on marked. It appears when the portal has more than one screen to switch between.

### The filter panel

The panel holds the filters that are not in the toolbar. Every sample type has:

- **Has image**, which keeps the samples that do, or do not, carry an image.
- A filter for the sample's dataset. It offers only published datasets.
- A filter for the sample type.

A type adds one filter for each field its registration lists. A date field takes a range, a field with fixed choices takes a menu, a number field takes a range and a text field takes a text box.

## The table

Each row is one sample. The columns, from the left, are:

- A dataset icon with no heading. It links to the sample's dataset. When the dataset is private the icon stays and the link is left out, because a published dataset can still be private.
- **Name**, which links to the sample's page.
- The type's own fields, in the order its registration lists them.
- **Latitude** and **Longitude**, in decimal degrees. Both are empty for a sample with no location.

Choose a column heading to sort by it. The table shows up to 100 rows a page, with a pager beneath it.

### When there are no rows

The table reads "No published" followed by the type's plural name and "yet", for example "No published rock samples yet".

## What you can do here

- Open a sample by choosing its name. See [The sample page](sample.md).
- Switch to another sample or measurement screen from the **Switch** menu. For measurements, see [Measurements](../measurements/measurements.md).
- Narrow the rows with the search box and the filters.
