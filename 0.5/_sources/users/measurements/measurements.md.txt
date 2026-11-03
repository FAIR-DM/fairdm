# Measurements

The measurements screen is a table of the measurements of one measurement type, such as the XRF results a portal records. A portal registers its own measurement types, so it has one of these screens for each type, and all of them are built the same way. This page describes what they share. It does not describe a single measurement, which is on [The measurement page](measurement.md).

## How to reach it

Open **Measurements** in the navigation menu. It holds one entry for each measurement type the portal has registered, named with the type's plural name. A portal that has registered no measurement types has no **Measurements** entry.

A type's screen is at `/collections/measurements/` followed by the type's name in lowercase, for example `/collections/measurements/xrfmeasurement/`.

## Which rows you see

The table lists the measurements held in published datasets, and it lists the same rows for every visitor, signed in or not. Your own unpublished measurements are not mixed in. You find those on the page of the dataset that holds them. The reasoning is in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## The toolbar

The toolbar sits above the table.

- The heading is the type's plural name, followed by a count of the rows that match.
- A search box narrows the rows by the fields the type's registration lists for search. Unless the registration lists others, that is the measurement's name.
- A **Filters** button opens the filter panel beside the table. It shows how many filters are applied.
- A **Switch** menu lists every sample and measurement screen under the headings **Samples** and **Measurements**, with the one you are on marked. It appears when the portal has more than one screen to switch between.

### The filter panel

The panel holds the filters that are not in the toolbar. Every measurement type has:

- A filter for the measurement's dataset. It offers only published datasets.
- A filter for the sample the measurement was made on. It offers only samples in published datasets.
- **Measurement Type**, headed **Any type** when nothing is chosen.
- **Description contains**, which searches the text of the measurement's descriptions.
- **Date after** and **Date before**, which take a year (`2024`), a year and month (`2024-06`) or a full date (`2024-06-01`).

A type adds one filter for each field its registration lists. A date field takes a range, a field with fixed choices takes a menu, a number field takes a range and a text field takes a text box.

## The table

Each row is one measurement. The columns, from the left, are:

- A dataset icon with no heading. It links to the measurement's dataset. When the dataset is private the icon stays and the link is left out, because a published dataset can still be private.
- **Name**, which links to the measurement's page.
- **Sample**, which links to the sample the measurement was made on. When the sample's dataset is not published the cell reads "Unpublished" and has no link.
- The type's own fields, in the order its registration lists them.
- **Latitude** and **Longitude**, in decimal degrees. They give the measurement's own location, or its sample's when the measurement has none and you may open the sample. Both are empty otherwise.

Choose a column heading to sort by it. The table shows up to 100 rows a page, with a pager beneath it.

### When there are no rows

The table reads "No published" followed by the type's plural name and "yet", for example "No published XRF measurements yet".

## What you can do here

- Open a measurement by choosing its name. See [The measurement page](measurement.md).
- Open the sample a measurement was made on. See [The sample page](../samples/sample.md).
- Switch to another measurement or sample screen from the **Switch** menu. For samples, see [Samples](../samples/samples.md).
- Narrow the rows with the search box and the filters.
