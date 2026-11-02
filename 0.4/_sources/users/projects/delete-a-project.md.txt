# How to delete a project

Deleting a project removes it for good, together with its datasets and everything recorded beneath them. Do it when a project was made by mistake or its records are no longer wanted.

```{warning}
Deleting a project destroys every dataset, sample and measurement in it. It cannot be undone. Read the counts on the screen before you confirm.
```

## Before you start

- You need the **Can manage** level on the project. Only people who may delete the project see **Delete** in the **Manage** menu. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).
- Every dataset in the project must be private. A project with a public dataset cannot be deleted. If one is public, make it private first, as described in [How to restrict a dataset to specific people](../datasets/restrict-a-dataset-to-specific-people.md), or delete the dataset.

## Steps

1. Open [the project page](project.md).
2. Open the **Manage** menu and choose **Delete**. It is the last entry, after a divider. The [Delete](../editing-a-record/delete.md) screen opens.
3. Read the messages above the form. Under "The following related records will also be permanently deleted:" the screen lists the datasets, samples and measurements that go with the project, with a count for each type.
4. Under "To confirm, type" followed by the project's name, type that name into the box exactly as shown.
5. Select **Delete**. The button stays disabled until what you typed matches the name.

To leave without deleting, select **Back**. It returns you to the project page.

## The result

The project and everything beneath it are gone. You land on [Projects](projects.md), and a message says "Deleted" followed by the project's name.

## If the screen says the project cannot be deleted

The screen shows "This record cannot be deleted." and lists the datasets that are in the way. It offers no **Delete** button. Make each listed dataset private or delete it, then open the screen again.

The screen also refuses when a measurement in a dataset outside the project was made on one of the project's samples. It lists the measurements you may see and counts the rest. The people who hold those measurements must remove them, or change them so that they no longer refer to the sample, before the project can be deleted.
