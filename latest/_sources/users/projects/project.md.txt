# The project page

A project's page is where you land when you open a project. Its heading is the project's name. The page says what the project is, who leads it, how far it has got and what it holds, and it is where the people who work on the project reach every other project screen. Open it from a card on [Projects](projects.md), from a link on a person's or organization's page, or by saving a new project. The project's portal ID, written after the portal's address, also opens it: `/` followed by the portal ID takes you to the page.

Who may open the page depends on the project's visibility and the level you hold on it. A private project answers a stranger as though it did not exist. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## The tabs

The project has these tabs:

- **Overview** is the page described here.
- **Dataset List** lists the project's datasets as cards, with the same search, sort and filters as [Datasets](../datasets/datasets.md).
- **Contributors** lists the people and organizations credited on the project. See [Contributors](../contributors/contributors-tab.md).
- **Samples** and **Measurements** list the records of all the project's datasets that you may see. See [Browse samples and measurements](../datasets/browse-samples-and-measurements.md).

## The header

The header is a band in the project's colour. It shows:

- a **Project** badge, a badge for the project's status, and a **Private** badge when the project is private
- the project's name
- the project's leaders, each linked to their page. These are the people credited as Project Leader, then those credited as Project Manager. The first four are named, and a link counts the rest.
- a line of key facts: the owning **Organisation**, linked to its page, when **Runs** from its start to its end (or "ongoing"), and its DOI, linked to doi.org
- the project's keywords
- a **Cite** button, which jumps to the Cite panel
- a **Share** menu, which shares the project's permalink

A project with an image shows it filling the header's right-hand side, and on a phone as a banner above the header. Selecting the image opens it at full size. A project without an image shows the project icon on a ruled grid.

People who may change the project also see:

- an **Edit** button, which opens [Edit details](edit-details.md)
- **Edit** beside the keywords, or **Add keywords** when there are none, which opens [Keywords](../editing-a-record/keywords.md)

There is no menu of editing screens. Each part of the project is edited from the panel that shows it, and a control appears only for someone who may use its screen.

## The notices

Notices appear above the header.

- People who may change a private project see "This project is private. Only people with access to it can open this page, and none of its datasets can be found by anyone else until the project is made public." with a **Change visibility** button that opens Edit details.
- A project whose status is Searching for collaborators says "This project is looking for collaborators." It names the contact person, or the first leader when no one is the contact, and offers a **View profile** button.

## The figures

Four figures sit along the foot of the header:

- **Datasets**, linked to the Dataset List tab
- **Samples**, linked to the Samples tab
- **Measurements**, linked to the Measurements tab
- **Contributors**, linked to the Contributors tab

A visitor's figures count only the project's public datasets and the samples and measurements in them. The figures of people who may change the project count every dataset.

## The content column

The wide column holds these panels, from the top:

- **Descriptions.** With several descriptions, the panel has a tab for each type. With one, the panel is titled with that type. Long text folds after a few lines behind **Read more**. With none, the panel is titled **About**. It tells people who may change the project that nobody has described it yet and offers a **Write an abstract** button. It tells everyone else "No description has been added yet." People who may change the project see **Edit**, which opens [Descriptions](../editing-a-record/descriptions.md).
- **Datasets.** The five datasets updated most recently. Each shows whether it is **Published** or **Unpublished**, its licence (or **No licence**), when it was last updated, and how many samples and measurements it holds. A link under the list counts the rest, and **See all** opens the Dataset List tab. People who may change the project see **Add dataset** beside it. With no datasets, the panel says "No datasets have been shared from this project yet." People who may change the project see an explanation and an **Add dataset** button instead.
- **What it holds.** **Records by type**, a bar for each sample and measurement type in its type's colour, with its count, and **Growth**, a line chart of the running total of samples and measurements by month with a text description. The panel is left out when there is nothing to draw, and the line chart needs records from at least two months.

## The side column

The narrow column holds these panels, from the top:

- **Metadata readiness**, for people who may change the project. A ring shows how many of ten items are in place. The missing ones are listed, and each with a **Fix** link opens the screen that fixes it. The items in place are folded away under a count. The items are:
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
- **Cite**, the citation written as Creators (Year). Title. Publisher. Identifier. The year is the start year, or the year the project was added when it has no start date. The identifier is the DOI link, or the project's permalink. When there is no DOI, a note says the citation points at the page. A **Copy** button copies the text.
- **Details**, one panel of facts in sections. A fact with no value shows a dash.
    - The details: **Organisation**, the owner, linked to its page, which is left out when the project has no owner, then **Status**, **Licences**, each licence held by the public datasets with a count, or "No public datasets yet", with a note that counts public datasets that have no licence, then **Added** and **Last updated**, and **Timeline**: the start and end dates as recorded, or "ongoing" when there is no end. With both dates it adds a bar and a label such as "Year 2 of 4", "Not started yet" or "Finished". People who may change the project see **Edit** beside it, or **Add dates** when there are none, which opens [Key dates](../editing-a-record/key-dates.md).
    - **Identifiers**: the project's identifiers by type, with a DOI linked to doi.org, the **Portal ID** and the **Permalink**, the project's permanent link. Each has a button that copies it. People who may change the project see **Edit**, which opens [Identifiers](../editing-a-record/identifiers.md).
    - **Funding**: the awards recorded for the project with the funder, the award title and number. With none it says "No funding has been recorded." People who may change the project see a longer note. None of the editing screens changes funding.
    - **For machines**, with a **REST API** button that opens the project in the API. See [API documentation](../api/api-docs.md).
    - People who may delete the project see **Delete this project** as the last line, which opens [Delete](../editing-a-record/delete.md).
    People who may change the project see **Edit** on the panel, which opens Edit details.
- **People**, everyone credited on the project. The first six are named with their roles and the organization they are credited from, then up to ten more are shown as faces, each linked to their page, and a link counts the rest. **See all** opens the Contributors tab, and for people who may manage the project **Manage** does. With nobody credited it says "No one is credited yet."

## What you can do here

- Change the project's own fields: [Edit details](edit-details.md).
- Write about the project: [Descriptions](../editing-a-record/descriptions.md).
- Add words people can find it by: [Keywords](../editing-a-record/keywords.md).
- Record when it starts and ends: [Key dates](../editing-a-record/key-dates.md).
- Record its DOI and grant numbers: [Identifiers](../editing-a-record/identifiers.md).
- Credit people and decide who may open the project: [Contributors](../contributors/contributors-tab.md).
- Add a dataset: [How to create a dataset](../datasets/create-a-dataset.md).
- Remove the project: [How to delete a project](delete-a-project.md).
