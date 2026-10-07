# Delete

The delete page removes a dataset permanently, along with everything recorded beneath it.
Deletion cannot be undone.

You reach it from the **Manage** menu on the dataset's own page. It is the last entry, set apart
from the others by a divider.

## Who can open it

Anyone holding permission to delete the dataset, which a manager of the dataset has. Someone who
may only edit the dataset sees the other Manage entries and no Delete, and is refused if they type
the address. A private dataset does not answer at all to someone who may not see it, the same rule
the dataset's own page applies.

## What goes with it

Before you confirm, the page tells you how much data the deletion will take with the dataset: a
count for each kind of sample and each kind of measurement it holds. Descriptions, dates,
identifiers and contributor records go with it too, but they describe the dataset rather than
stand on their own, so the page does not list them. A dataset holding no samples and no
measurements shows no warning at all.

```{warning}
Deleting a dataset that holds samples and measurements destroys that data. Read the counts
before confirming.
```

## Confirming a deletion

To delete a dataset you must type its name exactly as it appears. Surrounding spaces are ignored,
but the rest of the name must match. The Delete button stays disabled until what you have typed
matches. **Back** abandons the deletion and returns you to the dataset.

## When deletion is refused

A dataset cannot be deleted while a measurement in another dataset was made on one of its samples.
The page says so, lists the measurements that are in the way and offers no way to confirm. A
measurement can sit in a dataset you hold no access to, so the page names only the measurements you
may see, by name or portal ID, and counts the rest. Remove those measurements, or ask the people
who hold them to, before the dataset can be deleted.

## Visibility does not block a deletion

A public dataset can be deleted by someone holding permission to delete it. Making a dataset
public shares its metadata with the community. It does not publish the data beneath it, and it
is not a point of no return.

The protection that does prevent a deletion applies to published data, and arrives with the
publication workflow. Until then, the only safeguards are the list of what will be destroyed and
the name you have to type.

## After deletion

You are taken to the dataset listing, and a message tells you the dataset was deleted.
