# How to write and publish a legal document

A portal keeps its privacy policy, terms of use and similar texts in the database. You write a document in the administration interface, check how it reads, and publish it, which puts it in force at once.

## Before you start

None of the four [portal roles](../reference/portal-roles.md) holds the permissions for documents, so a superuser does this, or a member of a group your portal made with them. Writing needs the add and change permissions for documents and versions in the **Compliance** section. Publishing needs the separate **Can publish a version** permission.

## Steps

1. Open the administration interface. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface).
2. Under **Compliance**, choose **Documents**, then **Add document**.
3. Enter the **Name**, such as "Privacy policy". The **Slug** fills in from the name and becomes the document's address. Use lowercase letters, digits and single hyphens. The slugs `agree` and `agreed` are reserved.
4. Choose the **Kind**. **Agreed to** is for a text people accept. **Notice** is for a text people only read, such as an impressum.
5. For a document people agree to, leave **Enforced** ticked if a person who has not agreed must be stopped until they do. Untick it to offer the document without requiring it.
6. Choose **Save**.
7. Open the document you saved. The number in the address of its page, `.../mvp_compliance/document/<number>/change/`, is its identifier.
8. Go to `/admin/mvp_compliance/version/add/?document=<number>`, with that number in place. The administration interface has no button for a document's first version. A version is added for the document the address names.
9. Write the text in the **Markdown** field, and choose **Save**. The version is a draft, and a draft has no number.
10. Open the draft from **Versions** and choose **Preview**. The page shows the text as a reader will be served it.
11. Choose **Publish**, read the confirmation, and choose **Publish** again.

## The result

The page confirms the publication and names the version's number, which is the year and the version's place among that year's versions, such as 2026.1. The text is served at `/legal/<slug>/` for everyone.

A signed-in person who has not agreed to a document they must agree to is asked on their next page. Publishing sends nobody a message, so tell people yourself. Who is asked, and what happens to those who agreed to an earlier version, is explained in [Who is asked to agree to a legal document](../../explanation/who-is-asked-to-agree-to-a-legal-document.md).

A published version can never be edited or deleted, and the document's slug cannot change once a version is published. To correct a text, open the version in force and choose **Start the next version**. The new draft opens with the wording of the version in force. Publishing a draft that says exactly what the version in force says is refused.

If your portal changed the address of the administration interface, use that address in step 8.
