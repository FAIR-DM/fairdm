# Create a Dataset

The Create a Dataset screen starts a new dataset with the four facts every dataset needs: its name, its project, its licence and who may see it. Everything else is filled in afterwards on the dataset's own screens. You reach it from the **Create new** menu in the header, where you choose **Dataset**, or from the **Add dataset** button on a [project page](../projects/project.md). The screen is at `/datasets/create/`. A visitor who is not signed in is sent to sign in first.

## The form

The form has these fields, in this order:

- **Name.** Required, up to 300 characters. The help text reads "Give your dataset a descriptive name that reflects its purpose and content. This will help others discover and understand your data."
- **Project.** Optional. The list offers the projects you hold at least the **Can edit** level on. Type to search it. The help text reads "Select the research project this dataset belongs to. Datasets can be organized under projects for better management." A dataset can be attached to a project, or moved to another, later on [Edit details](edit-details.md).
- **License.** Required. The portal's default licence is chosen when the form opens, which is CC BY 4.0 unless the portal names another. See [settings](../../developers/reference/settings.md). The help text explains that CC BY 4.0 allows sharing and adaptation with attribution.
- **Visibility.** Two options, **Private** and **Public**. Public is selected when the form opens. The help text reads "Whether this dataset's metadata may be read by anyone using the portal. The data held beneath the dataset is governed separately."

Visibility governs the dataset's page and its metadata: the name, descriptions, dates and the rest. It does not release the samples and measurements held in the dataset. Those stay hidden until the dataset is published, and a researcher cannot publish from any portal screen. See [Dataset publication, DOIs and DataCite metadata](../../explanation/dataset-publication-dois-and-datacite-metadata.md).

The form preselects Public, but the dataset itself defaults to Private, so a dataset that is created without this form starts private. The form and the dataset decide their defaults separately. See [ADR 0009](../../adr/0009-a-form-default-and-a-model-default-may-differ.md).

## The buttons

The form ends with two buttons, **Save & continue** and **Save & continue editing**. Both create the dataset and open its page, where a message says "Dataset successfully created." If a field is wrong, the form stays open with the error beside the field and nothing is created.

## What is recorded for you

The dataset lists you as a contributor with the **Can manage** level and the roles Creator, Project Member and Contact Person. The exception is a superuser, who cannot be credited on a record. See [Contributors](../contributors/contributors-tab.md) for what the level allows.

## What is not on this screen

The form leaves out the cover image and the data publication, which are on [Edit details](edit-details.md). The dataset's descriptions, keywords, dates and identifiers have screens of their own, all in the **Manage** menu of [the dataset page](dataset.md).

## What you can do here

- Create the dataset: [How to create a dataset](create-a-dataset.md).
- Fill in the rest: [Edit details](edit-details.md), [Descriptions](../editing-a-record/descriptions.md), [Key dates](../editing-a-record/key-dates.md).
