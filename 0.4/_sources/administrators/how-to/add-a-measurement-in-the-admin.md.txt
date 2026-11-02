# How to add a measurement in the administration interface

Adding a measurement in the administration interface records an observation made on a sample without using the portal's pages. Do it to repair a dataset or to enter a result on behalf of someone who cannot.

## Before you start

- The sample the measurement was made on has to exist, and so does the dataset the measurement will belong to. The administration interface offers every sample and every dataset, private ones included.
- You need the permission to add measurements of the type you will choose. The type list shows only the types you may add, and you are refused if there are none. The four [portal roles](../reference/portal-roles.md) hold the permissions of the base measurement record, not of each registered type, so a superuser, or a member of a group with the type's permissions, does this.

## Steps

1. Open the administration interface. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface).
2. Under **Measurement**, choose **Measurements**, then **Add measurement**. A measurement cannot be saved as a bare measurement, so the next page asks for its type.
3. Under **Type**, choose the kind of measurement, such as an XRF measurement, and select **Save**. If your portal registers only one type, this page is skipped.
4. Enter the **Name**.
5. Search for the **Sample** the measurement was made on, and choose it.
6. Search for the **Dataset** the measurement belongs to, and choose it. It can be a different dataset from the sample's. See [How to record a measurement against a sample in another dataset](record-a-measurement-against-a-sample-in-another-dataset.md).
7. Optionally add an **Image**, and a **Location** with its **Elevation** and **Uncertainty**. Elevation and uncertainty need a location.
8. Fill in the type's own fields, under the **Contents** heading.
9. Choose **Save**.

Each description, date, identifier and contributor has a section further down the same page, and you can fill them in before saving. They are described on [Measurements](../reference/measurements.md).

## The result

The measurement is listed under **Measurements** with its type. It has a portal ID that begins with `m`, shown in the collapsed **Metadata** section. A measurement's type cannot be changed afterwards. To correct a wrong type, delete the measurement and add it again.

The measurement takes its access from its own dataset. Whoever holds a level on that dataset or on its project holds it on the measurement. The administration interface credits nobody for you. To give a person their own level, add a row to the **Contributors** section and set its **Level**. A row saved with an empty level credits the person with no access. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).
