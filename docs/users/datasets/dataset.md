# The dataset page

A dataset's page is where you land when you open a dataset. Its heading is the dataset's name. The page says what the dataset is, whether its data is published, under which licence, what it holds, when each step of its life happened, how to cite it and who made it. It is also where the people who work on the dataset reach every other dataset screen. Open it from a card on [Datasets](datasets.md), from a project's page, from a link on a person's or organization's page, or by saving a new dataset.

Who may open the page depends on the dataset's visibility and the level you hold on it. A private dataset answers a stranger as though it did not exist. A public dataset opens for everyone, but its samples and measurements stay hidden until the dataset is published. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) and [Dataset publication, DOIs and DataCite metadata](../../explanation/dataset-publication-dois-and-datacite-metadata.md).

## The tabs

The dataset has these tabs:

- **Overview** is the page described here.
- **Contributors** lists the people and organizations credited on the dataset. See [Contributors](../contributors/contributors-tab.md).

## The header

The header shows:

- the dataset's image, or an icon when it has none
- a badge for its state: **Published**, **Unpublished** (public, but its data is not published) or **Private**
- a badge with the licence's name, when a licence is chosen
- the dataset's name
- the dataset's creators, each linked to their page. These are the people credited as Creator.
- the dataset's keywords
- a **Cite** button, which jumps to the Citation card
- a **Share** menu

People who may change the dataset also see a **Manage** menu. It lists the editing screens you may use, in this order:

1. **Edit details**, described in [Edit details](edit-details.md).
2. **Edit descriptions**, described in [Descriptions](../editing-a-record/descriptions.md).
3. **Keywords**, described in [Keywords](../editing-a-record/keywords.md).
4. **Key dates**, described in [Key dates](../editing-a-record/key-dates.md).
5. **Identifiers**, described in [Identifiers](../editing-a-record/identifiers.md).
6. **Delete**, described in [Delete](../editing-a-record/delete.md). It comes last, after a divider, and only people who may delete the dataset see it.

The menu does not appear when nothing is in it.

## The notices

Notices appear above the header.

- People who may change a private dataset see "This dataset is private. Only people with access to it can open this page." with a **Change visibility** button that opens Edit details.
- On a public dataset that is not published, people who may change it see "Anyone can read this description, but the records stay hidden until the dataset is published." Everyone else sees "The data in this dataset hasn't been published yet. You can read what it holds, and the records open to everyone once the dataset is published."
- A dataset with a Withdrawal date says "This dataset was withdrawn on" followed by the date, and "It is kept here so existing citations still resolve."

## The figures

A strip of four figures sits under the header: **Samples**, **Measurements**, **Contributors** and **Related publications**. Under the sample and measurement counts the page gives the number of types, or **None yet**. The page never lists a sample or measurement itself.

## The content column

The wide column holds these cards, from the top:

- **Descriptions.** With several descriptions, the card has a tab for each type. With one, the card is titled with that type. With none, the card is titled **About**. It tells people who may change the dataset that nobody has described it yet and offers a **Write a description** button. It tells everyone else "No description has been added yet."
- **Data types.** This card appears only while the dataset holds no samples or measurements. It says so. Once the dataset holds records, the card gives way to the charts.
- **Data types** and **Progress** charts. A bar chart of the records by sample and measurement type, and a line chart of the running total of samples and measurements by month. Each has a text description. A chart is left out when there is nothing to draw, and the line chart needs records from at least two months.

## The side column

The narrow column holds these cards, from the top:

- **Ready to publish?**, for people who may change the dataset, until the dataset is both public and published. It says "Everything required is in place." or how many required items are missing, shows how many of ten items are in place with a progress bar, and lists the missing ones first. Each missing item with a **Fix** link opens the screen that fixes it. The recommended items are marked "recommended". The items are:
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
- **Details**, a list of facts:
    - **Project**, linked to its page, with a note such as "2 other datasets in this project". The row is left out when the dataset has no project, and also when you may not see the project.
    - **Licence**, the licence's name linked to its text. When none is chosen, the row says "None chosen yet" and warns that nobody can safely reuse the data.
    - **Last updated**
    - **For machines**, with a **REST API** button that opens the dataset in the API. See [API documentation](../api/api-docs.md).
- **Timeline**, the dataset's key dates in the order they happened. The steps are Collected (with its end date, or "ongoing"), Added to the portal, Submitted, Published, Available from and Withdrawn. A step with no date is left out, and Added to the portal is always there. A date appears as precisely as it was entered: a day, a month and year, or a year.
- **People**, a grid of faces with the name on hover, each linked to the person's page. A line counts those not shown. With nobody credited it says "No one is credited yet."
- **Identifiers**, a table of the dataset's identifiers by type, with a DOI linked to doi.org, and the **Portal ID** with a button that copies it.
- **Citation**, the citation written as Creators (Year). Title. Publisher. Identifier. The year is the publication date, else the date it became available, else the year the dataset was added. The identifier is the DOI link, or the address of the page. When the dataset has a data publication, the card cites that publication and says to cite it rather than the page. A **Copy** button copies the text.
- **Related publications**, each with a badge for how it relates to the dataset, such as "Describes this dataset", its title linked to its DOI and its year. With none, people who may change the dataset see "No publications linked. The paper that describes this data is the one reusers look for first." Everyone else sees "No publications are linked to this dataset." None of the editing screens changes this list.

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
