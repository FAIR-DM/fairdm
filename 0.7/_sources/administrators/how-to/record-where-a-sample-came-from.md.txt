# How to record that a sample came from another sample

A sample cut from a core, or split from a larger specimen, is a child of the sample it came from. Record the link in the administration interface so the portal can show the two together.

## Before you start

Both samples have to exist. The relationship is recorded on the child, so open the sample that came from the other.

You need to be able to change samples of the child's type. See [Samples](../reference/samples.md).

## Steps

1. Open the administration interface. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface).
2. Under **Sample**, choose **Samples**, and open the child sample.
3. In the **Sample relationships** section, choose **Add another Sample relationship**.
4. Set **Type** to **child of**. It is the only type offered.
5. Set **Target** to the parent sample, the one this sample came from.
6. Choose **Save**.

## The result

The child's page in the portal lists the parent in its **Related** card as the **Parent sample**, and the parent's page lists the child as a **Subsample**. See [The sample page](../../users/samples/sample.md).

The administration interface shows the link only on the child, in its **Sample relationships** section. The parent's page there has no section for its children.

The portal refuses three things, wherever the relationship is saved:

- A sample related to itself. The message reads "Sample cannot relate to itself".
- A link whose reverse already exists, such as recording that A is a child of B when B is already recorded as a child of A. The message begins "Circular relationship detected".
- The same link twice.

To remove a link, tick **Delete** on its row and save. The relationship carries no description, so the link is all that is recorded.
