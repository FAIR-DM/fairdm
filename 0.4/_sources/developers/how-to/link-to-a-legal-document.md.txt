# How to link to a legal document

A portal's privacy policy, terms of use and impressum are pages under `/legal/`. FairDM adds no link to any of them, because it cannot know which documents your portal has, so you add the links where your visitors look for them, such as the footer.

## Before you start

Your portal needs a published document, and you need its slug. The slug is the segment of the document's address. An administrator sets it when writing the document, as described in [How to write and publish a legal document](../../administrators/how-to/write-and-publish-a-legal-document.md).

## Steps

1. In the template, reverse the document's address with the `mvp_compliance:document` URL name and the slug.

   ```django
   <a class="link" href="{% url 'mvp_compliance:document' 'terms-of-use' %}">Terms of use</a>
   ```

2. In Python, reverse it the same way.

   ```python
   from django.urls import reverse

   reverse("mvp_compliance:document", args=["terms-of-use"])
   ```

3. To point at an older version, add the version number as a query string: `?version=2026.1`.

## The result

The link opens `/legal/terms-of-use/`, which always shows the version in force. A slug that names no document, or a document with nothing published, answers "not found". Check the link after the document is published.

The other URL names, `mvp_compliance:agree` and `mvp_compliance:agreed`, and the pages behind them are listed in [Legal documents](../reference/legal-documents.md). A signed-in person finds the list of what they agreed to under **Agreements** in the account area, with no link from you.
