# How to add a sample in the administration interface

Adding a sample in the administration interface records a specimen in a dataset without using the portal's pages. Do it to repair a dataset or to enter a sample on behalf of someone who cannot.

## Before you start

- The dataset the sample belongs to has to exist. The administration interface offers every dataset, private ones included.
- You need the permission to add samples of the type you will choose. The type list shows only the types you may add, and you are refused if there are none. The four [portal roles](../reference/portal-roles.md) hold the permissions of the base sample record, not of each registered type, so a superuser, or a member of a group with the type's permissions, does this.

## Steps

1. Open the administration interface. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface).
2. Under **Sample**, choose **Samples**, then **Add sample**. A sample cannot be saved as a bare sample, so the next page asks for its type.
3. Under **Type**, choose the kind of sample, such as a rock sample, and select **Save**. If your portal registers only one type, this page is skipped.
4. Enter the **Name**.
5. Search for the **Dataset** the sample belongs to, and choose it.
6. Optionally enter the **Local ID** and set the **Status**. A new sample starts as **Unknown**.
7. Optionally enter the **Location**, with its **Elevation** and **Uncertainty**. Elevation and uncertainty need a location.
8. Fill in the type's own fields, under the **Contents** heading.
9. Choose **Save**.

Each description, date, identifier, contributor and relationship has a section further down the same page, and you can fill them in before saving. They are described on [Samples](../reference/samples.md).

## The result

The sample is listed under **Samples** with its type. It has a portal ID that begins with `s`, shown in the collapsed **Metadata** section.

The sample takes its access from its dataset. Whoever holds a level on the dataset or on its project holds it on the sample, and the sample opens to everyone only when the dataset is public and published. The administration interface credits nobody for you. To give a person their own level on the sample, add a row to the **Contributors** section and set its **Level**. A row saved with an empty level credits the person with no access. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

To record that the sample came from another sample, follow [How to record that a sample came from another sample](record-where-a-sample-came-from.md).
