# The dataset page

A dataset's page is where you land when you open a dataset. Its heading is the dataset's name. The page says what the dataset is, whether its data is published, under which licence, what it holds, when each step of its life happened, how to cite it and who made it. It is also where the people who work on the dataset reach every other dataset screen. Open it from a card on [Datasets](datasets.md), from a project's page, from a link on a person's or organization's page, or by saving a new dataset. The dataset's portal ID, written after the portal's address, also opens it: `/` followed by the portal ID takes you to the page.

Who may open the page depends on the dataset's visibility and the level you hold on it. A private dataset answers a stranger as though it did not exist. A dataset in a private project is closed the same way, whatever its own visibility. Any other public dataset opens for everyone, but its samples and measurements stay hidden from everyone but its team until the dataset is published. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) and [Dataset publication, DOIs and DataCite metadata](../../explanation/dataset-publication-dois-and-datacite-metadata.md).

## The tabs

The dataset has these tabs:

- **Overview** is the page described here.
- **Contributors** lists the people and organizations credited on the dataset. See [Contributors](../contributors/contributors-tab.md).
- **Samples** and **Measurements** list the dataset's records. They are shown only to people who may see the records. See [Browse samples and measurements](browse-samples-and-measurements.md).

## The header

The header is a band in the dataset's colour. It shows:

- a badge for its state: **Published**, **Unpublished** (public, but its data is not published) or **Private**
- the dataset's name
- the dataset's creators, each linked to their page. These are the people credited as Creator.
- a line of key facts: its **Project**, linked to its page (left out when the dataset has none or you may not see it), its **Licence** (a dash when none is chosen) and its DOI, linked to doi.org, when it has one
- the dataset's keywords
- a **Cite** button, which jumps to the Cite panel
- a **Share** menu, which shares the dataset's permalink

A dataset with an image shows it filling the header's right-hand side, and on a phone as a banner above the header. Selecting the image opens it at full size. A dataset without an image shows the dataset icon on a ruled grid.

People who may change the dataset also see an **Edit** button, which opens [Edit details](edit-details.md), and **Edit** beside the keywords, or **Add keywords** when there are none, which opens [Keywords](../editing-a-record/keywords.md). There is no menu of editing screens. Each part of the dataset is edited from the panel that shows it.

## The notices

Notices appear above the header.

- People who may change a private dataset see "This dataset is private. Only people with access to it can open this page." with a **Change visibility** button that opens Edit details.
- On a public dataset that is not published, people who may change it see "Anyone can read this description, but the records stay hidden until the dataset is published." Everyone else sees "The data in this dataset hasn't been published yet. You can read what it holds, and the records open to everyone once the dataset is published."
- A dataset with a Withdrawal date says "This dataset was withdrawn on" followed by the date, and "It is kept here so existing citations still resolve."

## The figures

Four figures sit along the foot of the header: **Samples**, **Measurements**, **Contributors** and **Related publications**. The sample and measurement figures link to the **Samples** and **Measurements** tabs and count the records you may see. **Contributors** links to the Contributors tab, and **Related publications** to the panel of that name. If you may not see the dataset's records, the page leaves those two figures out. The page never lists a sample or measurement itself.

## The content column

The wide column holds these cards, from the top:

- **Descriptions.** With several descriptions, the panel has a tab for each type. With one, the panel is titled with that type. Long text folds after a few lines behind **Read more**. People who may change the dataset see **Edit**, which opens [Descriptions](../editing-a-record/descriptions.md). With none, the panel is titled **About**. It tells people who may change the dataset that nobody has described it yet and offers a **Write a description** button. It tells everyone else "No description has been added yet."
- **Timeline**, the dataset's key dates across the page in the order they happened, and down it on a phone. The steps are Collected (with its end date, or "ongoing"), Added to the portal, Submitted, Published, Available from and Withdrawn. A step with no date is left out, and Added to the portal is always there. Until a publication date is recorded, **Published** is still shown: as "Not yet" while the data is not published, and with a dash once it is. A withdrawal always comes last. A date appears as precisely as it was entered: a day, a month and year, or a year. People who may change the dataset see **Edit**, which opens [Key dates](../editing-a-record/key-dates.md).
- **What it holds**, while the dataset holds no samples or measurements. It says so, and offers people who may change the dataset an **Import data** button, disabled until importing is available.
- **What it holds**, once it holds records: **Records by type**, a bar for each sample and measurement type in the type's colour, samples and measurements apart, and **Growth**, a line chart of the running total of samples and measurements by month with a text description. The line chart needs records from at least two months. Both are left out when you may not see the dataset's records.
- **Where the samples come from.** A map of every sample you may open that has a location, grouped into numbered clusters where they crowd. Select a cluster to zoom in and a point to see the sample's name, type and dataset with a link to its page. Several samples at one spot are listed together. Scroll the page past the map, and hold Ctrl (⌘ on a Mac) while scrolling to zoom it. Beneath the map are how many samples are mapped, how many have no location and the area they cover. **See all** opens the Samples tab, which gives each sample's latitude and longitude. When none of the samples has a location, the panel says so. With no samples, or while you may not see the dataset's records, it is left out.

## The side column

The narrow column holds these cards, from the top:

- **Ready to publish?**, for people who may change the dataset, until the dataset is both public and published. It says "Everything required is in place." or how many required items are missing, shows how many of ten items are in place with a ring, lists the missing ones and folds away the items in place. A **Publish** button sits under the list, disabled until publishing is available. Each missing item with a **Fix** link opens the screen that fixes it. The recommended items are marked "recommended". The items are:
    - An abstract describes the data (required, **Fix** opens Descriptions)
    - The methods are described (required, opens Descriptions)
    - At least one creator is credited (required, no link)
    - Someone is named as the contact (required, no link)
    - A licence is chosen (required, opens Edit details)
    - It holds samples or measurements (required, no link)
    - The collection period is recorded (required, opens Key dates)
    - Keywords make it findable (recommended, opens Keywords)
    - A related publication is linked (recommended, no link)
    - The dataset is public (recommended, opens Edit details)
- **Cite**, the citation written as Creators (Year). Title. Publisher. Identifier. The year is the publication date, else the date it became available, else the year the dataset was added. The identifier is the DOI link or, with no DOI, the dataset's permalink. When the dataset has a data publication, the panel cites that publication and says to cite it rather than the page. With neither, a note says the citation points at the page and will use the DOI once one is recorded on [Identifiers](../editing-a-record/identifiers.md). A switch in the panel's heading sets the format to **Text**, **BibTeX** or **RIS**. **Copy** copies the format on show, and for BibTeX and RIS a **Download** link saves it as a file named after the dataset. The panel keeps the format you chose for your next visit. Reference managers read the BibTeX and RIS files.
- **Details**, one panel of facts in sections. A fact with no value shows a dash.
    - The details: **Project**, linked to its page, with a note such as "2 other datasets in this project". The row is left out when the dataset has no project, and also when you may not see the project. **Licence**, the licence's name linked to its text. When none is chosen, the row says "None chosen yet" and warns that nobody can safely reuse the data. **Last updated**.
    - **Identifiers**: the dataset's identifiers by type, with a DOI linked to doi.org, the **Portal ID** and the **Permalink**, the dataset's permanent link. Each has a button that copies it. People who may change the dataset see **Edit**, which opens [Identifiers](../editing-a-record/identifiers.md).
    - **For machines**, with a **REST API** button that opens the dataset in the API. See [API documentation](../api/api-docs.md).
    - People who may delete the dataset see **Delete this dataset** as the last line, which opens [Delete](../editing-a-record/delete.md).
    People who may change the dataset see **Edit** on the panel, which opens Edit details.
- **People**, everyone credited on the dataset. The first six are named with their roles and the organization they are credited from, then up to ten more are shown as faces, each linked to their page, and a link counts the rest. **See all** opens the Contributors tab, and for people who may manage the dataset **Manage** does. With nobody credited it says "No one is credited yet."
- **Related publications**, with their count. Each says how it relates to the dataset, such as "Describes this dataset", and its year, then its title linked to its DOI. With none, people who may change the dataset see "No publications linked. The paper that describes this data is the one reusers look for first." Everyone else sees "No publications are linked to this dataset." None of the editing screens changes this list.

## What you can do here

- Change the dataset's own fields: [Edit details](edit-details.md).
- Write about the dataset: [Descriptions](../editing-a-record/descriptions.md).
- Add words people can find it by: [Keywords](../editing-a-record/keywords.md).
- Record the collection period and other dates: [Key dates](../editing-a-record/key-dates.md).
- Record its DOI: [Identifiers](../editing-a-record/identifiers.md).
- Credit people and decide who may open the dataset: [Contributors](../contributors/contributors-tab.md).
- Fill the metadata so others can reuse it: [How to write metadata others can reuse](write-metadata-others-can-reuse.md).
- Close the dataset to everyone but a team: [How to restrict a dataset to specific people](restrict-a-dataset-to-specific-people.md).
- Open the dataset to everyone: [How to make a dataset public](make-a-dataset-public.md).
- Take someone out: [How to remove someone's access to a dataset](remove-someones-access-to-a-dataset.md).
- Remove the dataset: [How to delete a dataset](delete-a-dataset.md).
