# How to find why a user cannot see a dataset

When someone reports that they cannot see a dataset, the portal has refused them for one of a few reasons. Start from what they see, find the heading below that matches it, and follow the checks under it.

## Before you start

Ask the person three things: whether they were signed in, which address or page they used, and what the page said.

You need to read datasets in the administration interface, which the Data Curator role allows, and to read people, which the Portal Administrator and Community Manager roles allow. A superuser can do both. See [Portal roles](../reference/portal-roles.md).

To open a dataset's **Contributors** tab you need to be able to open the dataset. A Data Curator can open any dataset.

## The page says "No dataset matches the given query"

The portal answers a person who may not open a private dataset exactly as it would for a dataset that does not exist. A visitor who is not signed in gets the same answer.

1. Open the administration interface and choose **Datasets** under **Dataset**. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface). Search by name, portal ID or project name, and open the dataset.
2. Read **Visibility**. If it is **Public**, the dataset's own page is open to everyone. Check the portal ID in the address the person used against the **UUID** on the dataset's page, because the address may belong to another dataset or to one that was deleted.
3. If it is **Private**, open the dataset in the portal and choose its **Contributors** tab. Look for the person under **People**.
4. If the person is not listed, look at the card headed "Access from the" project. It lists people who hold a level only through the project. If they are not there either, the person holds no level on the dataset. Add them with [How to let a colleague into a private record](../../users/contributors/let-a-colleague-into-a-private-record.md), or make the dataset public with [How to make a dataset public](../../users/datasets/make-a-dataset-public.md).
5. If the person is listed with **No access**, they are credited with no level. Choose **Edit** beside them, choose a level, and save.
6. If the person is listed with a level, open **Community**, then **Users**, search for their email address and read the **Account state**. An **Inactive** account has been deactivated and holds nothing until it is active again. A level set for a person with no account takes effect when they have one.

## The dataset opens, but its samples and measurements are missing

A dataset's page and the data beneath it are released by two separate flags. Visibility governs the page. **Published** governs whether the samples and measurements may be shown, and only the administration interface sets it. People who hold a level on the dataset see the data whatever the flags say.

1. Open the dataset in the administration interface.
2. Read **Published** in the first section. If it is not ticked, the data is hidden from everyone who holds no level.
3. Tick **Published** only when the data is ready to be seen, and choose **Save**.

See [Dataset publication, DOIs and DataCite metadata](../../explanation/dataset-publication-dois-and-datacite-metadata.md).

## The dataset is missing from the portal's list of datasets

A list of datasets shows the public datasets, and it shows the same ones to everyone. A private dataset is in no list, whatever levels people hold. People who hold a level reach it by its address. To put it in the list, set **Visibility** to **Public**.

## The dataset opens, but its project says it does not exist

A level travels down from a project to its datasets, never up. A person listed only on a dataset cannot open a private project above it.

1. Open the project's **Contributors** tab.
2. Add the person at the **Can view** level, or set the project's **Visibility** to **Public**. See [How to make a project public](make-a-project-public.md).

## You cannot tell what the person sees

A superuser sees an **impersonate user** column on the **Users** list. It signs you in as the person, so you see exactly what they see. Sign out of their account when you finish.

For the order in which the portal asks its questions, and what each refusal means, see [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).
