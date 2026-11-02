# Edit details

The Edit details screen changes a dataset's own fields: its cover image, name, licence and data publication and, for managers, its project and visibility. Open [the dataset page](dataset.md), choose **Manage** and then **Edit details**. The **Change visibility** button in the private-dataset notice opens the same screen. The entry appears only for people who may change the dataset. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) for who that is.

## The form

The form has these fields, in this order:

- **Cover Image.** An uploader for the dataset's image. The help text reads "Upload a representative image (recommended 3:2 ratio, e.g. 1200x800 px). Accepted formats: JPEG, PNG, WebP. Maximum file size: 5 MB. Images that do not match the 3:2 ratio will be centre-cropped on display." The field is optional.
- **Name.** Required, up to 300 characters.
- **Project.** Optional. The project the dataset belongs to, chosen by typing to search the projects you hold at least the **Can edit** level on. Only a manager sees this field.
- **License.** Required. The licence the dataset's data is published under.
- **Data Publication.** Optional. The paper, report or other literature that describes the dataset, chosen by typing to search the literature in the portal. The help text reads "Link to the primary data publication (paper, report, or other literature) that describes this dataset." When it is set, the Citation card on the dataset page cites this publication.
- **Visibility.** Two options, **Private** and **Public**. The help text reads "Whether this dataset's metadata may be read by anyone using the portal. The data held beneath the dataset is governed separately." Only a manager sees this field.

A manager is someone who holds the **Can manage** level on the dataset or on the project above it, or holds a portal role that can change every dataset, such as Data Curator. If you hold only **Can edit**, the form shows the first four fields. The two hidden fields change who has rights over the dataset, which is why they stay with managers. See [Contributors](../contributors/contributors-tab.md) for the levels.

Visibility governs the dataset's page and metadata. It does not publish the samples and measurements held in the dataset. See [Dataset publication, DOIs and DataCite metadata](../../explanation/dataset-publication-dois-and-datacite-metadata.md).

A change of project is refused when it would leave the dataset with nobody who can manage it.

## The buttons

The form ends with **Save & continue** and **Save & continue editing**. Both save the form and return you to the dataset page, where a message says "Saved" followed by the dataset's name. If a field is wrong, the form stays open with the error beside the field and nothing is saved.

## What is not on this screen

- The abstract, methods and other descriptions are on [Descriptions](../editing-a-record/descriptions.md).
- Free keywords are on [Keywords](../editing-a-record/keywords.md).
- The collection period and the other dates are on [Key dates](../editing-a-record/key-dates.md).
- The DOI is on [Identifiers](../editing-a-record/identifiers.md).
- The people credited on the dataset are on [Contributors](../contributors/contributors-tab.md).
- Whether the dataset's data is published is not a field on any portal screen.
- The portal ID is given by the portal and cannot be edited.

## What you can do here

- Rename the dataset, replace its image, change its licence or link its data publication: change the field and save.
- Open the dataset to everyone, or close it: [How to make a dataset public](make-a-dataset-public.md) and [How to restrict a dataset to specific people](restrict-a-dataset-to-specific-people.md). These are manager-only.
- Move the dataset to another project: change **Project** and save. This is manager-only.
- Remove the dataset: [How to delete a dataset](delete-a-dataset.md).
