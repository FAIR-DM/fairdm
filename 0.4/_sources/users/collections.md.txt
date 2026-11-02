# Collections

A collection is a table of all the published records of one kind of sample or one kind of measurement. The portal makes one table for every kind it has registered, such as rock samples or XRF measurements. There is no single page called Collections. Each table is headed with the plural name of its kind, and the navigation menu groups the tables under **Samples** and **Measurements**.

You reach a collection in any of these ways:

- Open **Samples** or **Measurements** in the navigation menu and choose a kind.
- Select the name of a kind in the **Samples and measurements** section of the [Home](home.md) screen.
- Use the **Switch** menu on another collection.

Each table has its own address, `collections/samples/` or `collections/measurements/` followed by the name of the kind. Anyone can open a collection, signed in or not. It lists published records only, whoever is looking. See [Dataset publication, DOIs and DataCite metadata](../explanation/dataset-publication-dois-and-datacite-metadata.md) for what publishing means.

## The toolbar

Along the top of the table are:

- the heading, which is the plural name of the kind, followed by a count
- a **Search** box with a **Search** button, when the kind has fields to search
- a **Status** menu, when the kind has a status, listing the statuses with **Any status** at the top
- a **Filters** button, when the kind has more filters than fit in the toolbar
- a **Switch** menu with a **Samples** group and a **Measurements** group, naming every collection. It appears only when the portal has more than one.

The count reads `1 sample`, `12 samples` and so on while no search or filter is applied. Once one is applied it reads `n results`, or **No results**.

The search box and the filters depend on the kind. Each kind chooses which of its fields can be searched and filtered.

## The filters panel

The **Filters** button opens a panel beside the table. It holds every filter the toolbar does not draw. The panel has an **Apply** button, and a **Clear** button once a filter in it is set. A number on the **Filters** button counts the filters applied from the panel.

Below the toolbar, each applied search or filter shows as a button. Selecting one removes it. When more than one is applied, a **Clear all** button removes them together.

## The table

The table fills the rest of the screen. Its columns depend on the kind, but some are always there:

- a column headed with nothing but a dataset icon, which links to the record's dataset. The icon is not a link when the dataset is private.
- **Name**, linked to the record's page
- **Latitude** and **Longitude**, filled for records that have a location
- the fields the kind registered for its table

A measurement table also has **Sample**, which links to the measurement's sample when the sample's dataset is published and reads **Unpublished** when it is not. A measurement's **Latitude** and **Longitude** come from its own location, or from its sample's location when you are allowed to open that sample.

Select a column heading to sort by that column, and again to reverse the order. Until you choose, samples are listed oldest first and measurements are listed with the most recently changed first. Latitude and Longitude cannot be sorted.

The table shows up to 100 records. When there are more, the foot of the screen shows `Showing` a range `of` the total, with page numbers. On a narrow screen it shows two buttons and the page count instead.

## When it is empty

A kind with no published record shows an icon and the heading **No published** followed by the plural name and **yet**, for example **No published rock samples yet**. The screen has no button for adding a record.

When a search or filter matches nothing, the heading reads **No** followed by the plural name and **match**, with the line **Try other words or fewer filters.** and a **Clear all** button.

## What you can do here

- Open a record from its **Name**. See [The sample page](samples/sample.md) and [The measurement page](measurements/measurement.md).
- Open the dataset a record belongs to. See [The dataset page](datasets/dataset.md).
- Read the same records with a script. See [How to read a dataset's samples with a script](api/read-a-datasets-samples-with-a-script.md).
