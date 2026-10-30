# Who is asked to agree to a legal document

This page explains which people a FairDM portal asks to agree to a legal document, which people it lets through, and why the check works the way it does. It covers the rules that decide who is held up. It does not cover how to write and publish a document or link to one, which are tasks in [How to write and publish a legal document](../administrators/how-to/write-and-publish-a-legal-document.md) and [How to link to a legal document](../developers/how-to/link-to-a-legal-document.md), and it does not list the settings, which are in [Settings](../developers/reference/settings.md).

A portal's privacy policy, terms of use and impressum are kept in the database as documents, not written into templates. FairDM installs the django-mvp-compliance package for this. FairDM ships no documents, so until your portal publishes one nobody is asked anything. What a document says is your portal's own business, and installing the package does not make a portal compliant with anything.

## Three kinds of document

Each document is one of three things, chosen on the document itself.

| The document is | A signed-in person who has not agreed |
|---|---|
| **Required** (agreed to, and enforced) | Is sent to the agreement page from any page they ask for, and back to where they were going once they agree |
| **Optional** (agreed to, and not enforced) | Is offered it on the agreement page and is never held up |
| **A notice**, such as an impressum | Is never asked. A notice is read, not agreed to |

A new document is required by default. A cookie policy is a typical optional document: published and offered, never demanded.

The distinction exists because some texts create an obligation and some only inform. Holding a person at a page until they agree to a notice would be meaningless, since there is nothing to agree to. Holding a person at a page for a document that is only offered would block people for no reason.

## Who is held up and who is not

The rule asks one question: is a required document outstanding for this signed-in person?

- **A visitor who is not signed in is never asked.** There is no one to record an agreement against. A visitor can read every published document.
- **A signed-in person is asked** when a required document has a version in force that they have not agreed to.
- **A superuser is not held up.** An account that holds the `mvp_compliance.skip_agreement` permission is not held up either, and you can give that permission to a group.
- **A document with nothing published is not outstanding.** There is no version in force to agree to.

A person's agreement is to a specific version. When a document gets a new version, that version is outstanding for everyone again, including people who agreed to the version before. This is why a published version can never be edited: a correction is a new version, and the record of who agreed to which wording stays true.

## What stays reachable while a person is asked

Someone who has been sent to the agreement page can still:

- Read the documents themselves.
- Sign out.
- Load static and media files, so the pages render.
- Reach any address your portal has added to the exempt list. FairDM exempts the address used by the administrator's "hijack" button, so an administrator acting as a held-up person can return to their own account.

Every other address sends them to the agreement page. That includes the addresses under `/api/` when somebody uses the API with their browser session.

A request that carries an API token and no browser session is not checked. The check works on the signed-in session, and a script that authenticates with a token has none. Holding a script to an agreement is not what the check is for.

## Why the check runs on every page

The alternative is to ask at sign-in or at the first page after it. That would miss a document that is published, or a new version of one, after a person has signed in. It would also let a long-lived session carry on indefinitely under old terms. Running the check as middleware means a person is asked on the next request after something becomes outstanding.

To keep the cost down, a clear result is remembered in the person's session for a short time before the check asks again. The interval is a setting of the package, and setting it to zero checks every request.

## Where the record of agreement lives

The portal keeps a record of who agreed to which version, and when. A signed-in person finds their own list under **Agreements** in the account area. The address a person agreed from is recorded only if your portal turns that on, because it is personal data.

## Limits

- The agreement page asks a person to agree. It does not verify that they have read the document.
- Taking the middleware out of the portal's settings stops the asking altogether, while the document pages and the existing records stay.
- Agreement is recorded for signed-in accounts. A portal that needs consent from visitors who have no account needs another mechanism.

## Where to go next

- [Legal documents](../developers/reference/legal-documents.md) lists the pages and permissions.
- [How to configure the agreement check](../developers/how-to/configure-the-agreement-check.md) describes the settings you change to adjust it.
