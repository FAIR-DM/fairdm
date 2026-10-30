# How to record a measurement against a sample in another dataset

A laboratory often measures samples that another team collected and keeps its results in its own dataset. Record such a measurement so that the sample stays in the collectors' dataset and the result belongs to the laboratory's.

## Before you start

The sample and the laboratory's dataset have to exist. The steps are those of [How to add a measurement in the administration interface](add-a-measurement-in-the-admin.md), with one difference in how you fill two fields.

## Steps

1. Open the administration interface. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface).
2. Under **Measurement**, choose **Measurements**, then **Add measurement**, and choose the measurement's type.
3. Enter the **Name**.
4. Search for the **Sample**, and choose it. The search offers every sample in the portal, whatever dataset it is in.
5. Search for the **Dataset**, and choose the dataset the measurement belongs to. Do not choose the sample's dataset unless the result belongs there.
6. Fill in the rest of the form and choose **Save**.

## The result

The measurement is stored in the dataset you chose and refers to a sample that stays in its own dataset. Neither record moves.

Each dataset is judged on its own. Who may open the measurement is decided by the measurement's dataset alone. A level on the sample's dataset gives no access to the measurement, and a level on the measurement's dataset gives no access to the sample. In a listing, a visitor who may open the measurement but not the sample sees "Unpublished" in the sample column instead of the sample's name.

If the measurement has no location of its own, the portal shows the sample's location for it, but only to a viewer who may open the sample. See [ADR 0033](../../adr/0033-a-measurement-borrows-its-samples-location-only-for-a-viewer-who-may-open-the-sample.md).

The reasoning is in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md). To move a measurement into a different dataset later, change its **Dataset**. The portal refuses a move that would leave the measurement with nobody who can manage it. The message reads "Nobody who can sign in would be able to manage this measurement there."
