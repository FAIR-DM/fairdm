# How to delete a dataset

Deleting a dataset removes it for good, together with the samples and measurements it holds. Do it when a dataset was made by mistake or its records are no longer wanted.

```{warning}
Deleting a dataset that holds samples and measurements destroys that data. It cannot be undone, and being public does not protect a dataset from it. Read the counts on the screen before you confirm.
```

## Before you start

You need the **Can manage** level on the dataset, or on the project above it. Only people who may delete the dataset see **Delete** in the **Manage** menu. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## Steps

1. Open [the dataset page](dataset.md).
2. Open the **Manage** menu and choose **Delete**. It is the last entry, after a divider. The [Delete](../editing-a-record/delete.md) screen opens.
3. Read the messages above the form. When the dataset holds records, the screen lists them under "The following related records will also be permanently deleted:" with a count for each type of sample and measurement. A dataset that holds none shows only the warning that the deletion is permanent.
4. Under "To confirm, type" followed by the dataset's name, type that name into the box exactly as shown.
5. Select **Delete**. The button stays disabled until what you typed matches the name.

To leave without deleting, select **Back**. It returns you to the dataset page.

## The result

The dataset and everything beneath it are gone. You land on [Datasets](datasets.md), and a message says "Deleted" followed by the dataset's name.

## If the screen says the dataset cannot be deleted

The screen shows "This record cannot be deleted." and lists the measurements that are in the way. A measurement in another dataset was made on one of this dataset's samples. The screen names the measurements you may see, by name or portal ID, and counts the rest as measurements you do not have access to. It offers no **Delete** button. The people who hold those measurements must remove them, or change them so that they no longer refer to the sample, before the dataset can be deleted.
