# The project page

A project's page is where you land when you open a project. Its heading is the project's name. The page says what the project is, who leads it, how far it has got and what it holds, and it is where the people who work on the project reach every other project screen. Open it from a card on [Projects](projects.md), from a link on a person's or organization's page, or by saving a new project.

Who may open the page depends on the project's visibility and the level you hold on it. A private project answers a stranger as though it did not exist. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## The tabs

The project has these tabs:

- **Overview** is the page described here.
- **Dataset List** lists the project's datasets as cards, with the same search, sort and filters as [Datasets](../datasets/datasets.md).
- **Contributors** lists the people and organizations credited on the project. See [Contributors](../contributors/contributors-tab.md).
- **Export** opens [Export Project Data](export.md).

## The header

The header shows:

- the project's image, or an icon when it has none
- a badge for the project's status, and a **Private** badge when the project is private
- the project's name
- the project's leaders, each linked to their page. These are the people credited as Project Leader, then those credited as Project Manager.
- the project's keywords
- a **Cite** button, which jumps to the Citation card
- a **Share** menu

People who may change the project also see:

- an **Add dataset** button, which opens [Create a Dataset](../datasets/create-dataset.md)
- a **Manage** menu

The **Manage** menu lists the editing screens you may use, in this order:

1. **Edit details**, described in [Edit details](edit-details.md).
2. **Edit descriptions**, described in [Descriptions](../editing-a-record/descriptions.md).
3. **Keywords**, described in [Keywords](../editing-a-record/keywords.md).
4. **Key dates**, described in [Key dates](../editing-a-record/key-dates.md).
5. **Identifiers**, described in [Identifiers](../editing-a-record/identifiers.md).
6. **Delete**, described in [Delete](../editing-a-record/delete.md). It comes last, after a divider, and only people who may delete the project see it.

The menu does not appear when nothing is in it.

## The notices

Notices appear above the header.

- People who may change a private project see "This project is private. Only people with access to it can open this page, and none of its datasets can be found by anyone else until the project is made public." with a **Change visibility** button that opens Edit details.
- A project whose status is Searching for collaborators says "This project is looking for collaborators." It names the contact person, or the first leader when no one is the contact, and offers a **View profile** button.

## The figures

A strip of four figures sits under the header:

- **Datasets**, linked to the Dataset List tab
- **Samples**
- **Measurements**
- **Contributors**, linked to the Contributors tab

A visitor's figures count only the project's public datasets and the samples and measurements in them. The figures of people who may change the project count every dataset. Under the dataset count, the page gives how many datasets are published, or **None yet**. When some datasets are private, people who may change the project see how many are public and how many are private instead. Under the sample and measurement counts the page gives the number of types, or **None yet**.

## The content column

The wide column holds these cards, from the top:

- **Descriptions.** With several descriptions, the card has a tab for each type. With one, the card is titled with that type. With none, the card is titled **About**. It tells people who may change the project that nobody has described it yet and offers a **Write an abstract** button. It tells everyone else "No description has been added yet."
- **Datasets.** The five datasets updated most recently. Each shows whether it is **Published** or **Unpublished**, its licence (or **No licence**), how many samples and measurements it holds and when it was last updated. A link under the list counts the rest, and a **View all** button opens the Dataset List tab. With no datasets, the card says "No datasets have been shared from this project yet." People who may change the project see an explanation and an **Add dataset** button instead.
- **Data types** and **Progress**. A bar chart of the records by sample and measurement type, and a line chart of the running total of samples and measurements by month. Each has a text description. A chart is left out when there is nothing to draw, and the line chart needs records from at least two months.

## The side column

The narrow column holds these cards, from the top:

- **Metadata readiness**, for people who may change the project. It says how many of ten items are in place, with a progress bar, and lists the missing ones first. Each missing item with a **Fix** link opens the screen that fixes it. The items are:
    - An abstract describes the project (**Fix** opens Descriptions)
    - At least one creator is credited (opens Contributors)
    - Someone is named as the contact (opens Contributors)
    - A start date is recorded (opens Key dates)
    - Keywords make it findable (opens Keywords)
    - Funding is acknowledged (no link)
    - It has a persistent identifier (DOI) (opens Identifiers)
    - At least one dataset is public (opens the Dataset List tab)
    - Every public dataset has a licence (opens the Dataset List tab)
    - The project is public (opens Edit details)
- **Details**, a list of facts:
    - **Organisation**, the owner, linked to its page. The row is left out when the project has no owner.
    - **Status**
    - **Licences**, each licence held by the public datasets with a count, or "No public datasets yet". A note counts public datasets that have no licence.
    - **Added** and **Last updated**
    - **Timeline**, the start and end dates as recorded, or "ongoing" when there is no end. With both dates it adds a progress bar and a label such as "Year 2 of 4", "Not started yet" or "Finished". With neither it says "No start or end date has been recorded."
    - **For machines**, with a **REST API** button that opens the project in the API. See [API documentation](../api/api-docs.md).
- **People**, a grid of faces with the name on hover, each linked to the person's page. A **See all** button opens the Contributors tab, and a line counts those not shown. With nobody credited it says "No one is credited yet."
- **Identifiers**, a table of the project's identifiers by type, with a DOI linked to doi.org, and the **Portal ID** with a button that copies it.
- **Funding**, the awards recorded for the project with the funder, the award title and number. With none it says "No funding has been recorded." People who may change the project see a longer note. None of the editing screens changes funding.
- **Citation**, the citation written as Creators (Year). Title. Publisher. Identifier. The year is the start year, or the year the project was added when it has no start date. The identifier is the DOI link, or the address of the page. When there is no DOI, a note says the citation points at the page. A **Copy** button copies the text.

## What you can do here

- Change the project's own fields: [Edit details](edit-details.md).
- Write about the project: [Descriptions](../editing-a-record/descriptions.md).
- Add words people can find it by: [Keywords](../editing-a-record/keywords.md).
- Record when it starts and ends: [Key dates](../editing-a-record/key-dates.md).
- Record its DOI and grant numbers: [Identifiers](../editing-a-record/identifiers.md).
- Credit people and decide who may open the project: [Contributors](../contributors/contributors-tab.md).
- Add a dataset: [How to create a dataset](../datasets/create-a-dataset.md).
- Remove the project: [How to delete a project](delete-a-project.md).
