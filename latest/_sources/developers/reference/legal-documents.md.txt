# Legal documents

This page lists what a FairDM portal has for legal documents: the pages, the URL names, the permissions, the models you can query and the system checks. It does not describe the settings, which are in [Settings](settings.md), or who is asked to agree, which is in [Who is asked to agree to a legal document](../../explanation/who-is-asked-to-agree-to-a-legal-document.md).

FairDM installs [django-mvp-compliance](https://github.com/django-mvp/django-mvp-compliance), the `mvp_compliance` app, and wires it in for every portal that calls `fairdm.setup()`:

- `mvp_compliance` is in `INSTALLED_APPS`.
- `mvp_compliance.middleware.AgreementMiddleware` is in `MIDDLEWARE`.
- `fairdm.conf.urls` mounts `mvp_compliance.urls` under `legal/`.
- An **Agreements** entry is added to the account area's menu.

FairDM ships no documents. Until your portal publishes one, there are no pages under `/legal/` and the check asks nobody anything.

## Pages and URL names

| URL name | Address | Who may open it | What it shows |
|---|---|---|---|
| `mvp_compliance:document` | `/legal/<slug>/` | Everyone | A document in the version in force. `?version=<number>` shows any published version of it |
| `mvp_compliance:agree` | `/legal/agree/` | Signed-in people | The documents outstanding for the person, each with a toggle. Accepts a `next` address to go on to |
| `mvp_compliance:agreed` | `/legal/agreed/` | Signed-in people | The person's own list of the versions they accepted |

The document page answers "not found" for a slug that names no document, a document with nothing published and a `?version=` value that names no published version. It answers the same way to a signed-in person as to a visitor.

The `agreed` page answers "not found" in a portal whose URL configuration has no `account-center` name.

The slugs `agree` and `agreed` are reserved and cannot name a document.

## Documents and versions

A document has a name, a slug and a kind. A version holds the text.

| Field | Type | Default | What it does |
|---|---|---|---|
| `Document.name` | `str`, 100 characters | None | The name the document is known by. Unique |
| `Document.slug` | slug, 100 characters | None | The segment of the document's address. Unique, lowercase. It cannot change once a version is published |
| `Document.kind` | `"agreed"` or `"notice"` | `"agreed"` | Whether people agree to the document or only read it. Nobody is asked to accept a notice |
| `Document.enforced` | `bool` | `True` | Whether a person who has not accepted the document is stopped until they do. It never applies to a notice |
| `Version.markdown` | text | None | The wording, in Markdown |
| `Version.status` | `"draft"`, `"current"` or `"superseded"` | `"draft"` | Set by publishing. A document has at most one current version |
| `Version.number` | `str` | None | The year and the version's place among that year's versions, such as `2026.1`. A draft has none |

A published version can never be edited. A correction is a new version.

### Creating a document from code

```python
from mvp_compliance.models import Document

terms = Document.objects.create(name="Terms of use", slug="terms-of-use")
terms.versions.create(markdown="# Terms of use\n\n...").publish()
```

`Version.publish(publisher=None)` makes a draft the version in force and supersedes the one that held it. It raises `PublishError` when the version is not a draft, when its rendered output is empty and when it says exactly what the version in force says.

### Queries

| Method | Returns |
|---|---|
| `Document.objects.in_force()` | The documents that have a version in force |
| `Document.objects.outstanding_for(user)` | The documents whose version in force `user` has not accepted. A notice is never outstanding |
| `Document.objects.enforced_outstanding_for(user)` | The outstanding documents that are enforced |
| `document.current` | The version in force, or `None` |
| `document.is_outstanding_for(user)` | `True` when `document` is outstanding for `user` |

## Permissions

All belong to the `mvp_compliance` app.

| Permission | What it allows |
|---|---|
| `add_document`, `change_document` | Writing documents in the administration interface |
| `add_version`, `change_version` | Writing draft versions |
| `publish_version` | Publishing a version, which puts it in force at once |
| `skip_agreement` | Going on without accepting the enforced documents. Superusers are never stopped |

None of the four [portal roles](portal-roles.md) holds these.

## System checks

The checks run only when `AgreementMiddleware` is in `MIDDLEWARE`.

| ID | Severity | It reports |
|---|---|---|
| `mvp_compliance.E001` | Error | The page that asks has no address, because `mvp_compliance.urls` is not mounted |
| `mvp_compliance.E002` | Error | Nothing that identifies the signed-in user comes before `AgreementMiddleware` |
| `mvp_compliance.E003` | Error | `MVP_COMPLIANCE_AGREEMENT_EXEMPT_URLS` or `MVP_COMPLIANCE_AGREEMENT_EXEMPT_USERS` is a string where a list is needed |
| `mvp_compliance.E004` | Error | `MVP_COMPLIANCE_AGREEMENT_CHECK_INTERVAL` is not a number |

## Related pages

- [Settings](settings.md) for every `MVP_COMPLIANCE_*` setting
- [How to link to a legal document](../how-to/link-to-a-legal-document.md)
- [How to configure the agreement check](../how-to/configure-the-agreement-check.md)
- [How to write and publish a legal document](../../administrators/how-to/write-and-publish-a-legal-document.md), for the person who writes the text
