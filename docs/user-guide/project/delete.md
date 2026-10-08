# Delete

The delete page removes a project permanently, along with its datasets and everything recorded
beneath them. Deletion cannot be undone.

You reach it from the **Manage** menu on the project's own page. It is the last entry, set apart
from the others by a divider.

## Who can open it

Anyone holding permission to delete the project, which a manager of the project has. Someone who
may only edit the project sees the other Manage entries and no Delete, and is refused if they type
the address. On a public project, someone who is not signed in is sent to sign in first. A private
project does not answer at all to anyone who may not see it, so its address cannot be used to find
out whether it exists. This is the same rule every page of the project applies.

## What goes with it

Before you confirm, the page tells you how much the deletion will take with the project: a count
of its datasets, of the samples in them and of the measurements in them. Descriptions, dates,
identifiers and contributor records go with it too, but they describe the records rather than
stand on their own, so the page does not list them.

```{warning}
Deleting a project destroys every dataset, sample and measurement in it. Read the counts before
confirming.
```

## Confirming a deletion

To delete a project you must type its name exactly as it appears. Surrounding spaces are ignored,
but the rest of the name must match. The Delete button stays disabled until what you have typed
matches. **Back** abandons the deletion and returns you to the project.

## When deletion is refused

A project cannot be deleted while any of its datasets is still public. If you open the delete page
for such a project, the refusal is shown immediately, listing every public dataset that is in the
way. You do not need to type the name and submit to find out. Make each of the named datasets
private, or remove them, before the project can be deleted. This protects published data: deleting
the project a dataset belongs to must never be a way to withdraw data that has already been made
public.

A project is also refused when a measurement in a dataset outside the project was made on one of
its samples. The page lists the measurements you may see and counts the rest.

A dataset made public after you opened the page also stops the deletion. When you confirm, nothing
is deleted and the page shows the datasets that are in the way.

A project with no datasets, or with only private ones, can be deleted freely.

## After deletion

You are taken to the project listing, and a message tells you the project was deleted.
