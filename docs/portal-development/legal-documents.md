# Legal documents

A portal's privacy policy, terms of use and impressum are kept in the database, not in templates.
FairDM installs [django-mvp-compliance](https://github.com/django-mvp/django-mvp-compliance) for
this. A portal that calls `fairdm.setup()` has it with nothing to configure:

- each published document is a page under `/legal/`,
- the portal keeps a record of who agreed to which version, and when,
- a signed-in person finds what they agreed to under **Agreements** in the account area,
- a signed-in person who has not agreed to a required document is asked to before they go on.

FairDM ships no documents. Until a portal publishes one, there are no pages under `/legal/` and
nobody is asked anything. What the documents say is the portal's own business, and installing
this does not make a portal compliant with anything.

## Writing and publishing a document

Documents are written in the admin, under **Compliance**. A document has a name, an address and
any number of versions. A version is written in Markdown and is a draft until it is published.
Publishing puts the version in force at once and it can never be edited again. A correction is a
new version.

Writing a draft needs the `add_version` and `change_version` permissions of the `mvp_compliance`
app. Publishing needs `publish_version`, which is held separately. See the package's notes on
[writing and publishing](https://github.com/django-mvp/django-mvp-compliance/blob/main/docs/authoring.md).

A document can be created from code as well, for example in a data migration or a management
command of your own:

```python
from mvp_compliance.models import Document

terms = Document.objects.create(name="Terms of use", slug="terms-of-use")
terms.versions.create(markdown="# Terms of use\n\n...").publish()
```

## Linking to a document

A document with the slug `terms-of-use` is served at `/legal/terms-of-use/`. The address always
shows the version in force. Link to it by its slug:

```html
<a href="{% url 'mvp_compliance:document' 'terms-of-use' %}">Terms of use</a>
```

FairDM adds no link to any document to its own pages or menus, because it cannot know which
documents a portal has. An address with no published document answers "not found".

| URL name | Address | Page |
| --- | --- | --- |
| `mvp_compliance:document` | `/legal/<slug>/` | A document, in the version in force |
| `mvp_compliance:agree` | `/legal/agree/` | Asks a signed-in person to agree to what is outstanding for them |
| `mvp_compliance:agreed` | `/legal/agreed/` | A signed-in person's own list of what they agreed to |

## Who is asked to agree

Each document is one of three things, chosen on the document in the admin:

| The document is | A signed-in person who has not agreed |
| --- | --- |
| Required (`enforced` on, the default for a new document) | Is sent to `/legal/agree/` from any page, and back to where they were going once they agree |
| Optional (`enforced` off) | Is offered it on `/legal/agree/` and never held up |
| A notice, such as an impressum | Is never asked. A notice is read, not agreed to |

A new version of a required document is outstanding for everybody again, including the people who
agreed to the one before.

A visitor who is not signed in is never asked. Superusers are never held up, and neither is an
account that holds the `mvp_compliance.skip_agreement` permission, which you can give to a group
in the admin.

A person who is being asked can still read the documents, sign out, and load static and media
files. An administrator who is acting as that person through the admin's "hijack" button can still
go back to their own account. Every other address sends them to the page that asks. This includes
the addresses under `/api/` for somebody using the API with their browser session. A request that
carries an API token and no session is not checked.

## Settings

All of these are django-mvp-compliance's own settings. Set them in your portal's settings module,
after `fairdm.setup()`.

Keep more of your own pages reachable for a person who has not agreed yet. FairDM sets this to
`["/hijack/"]`, so add to it:

```python
MVP_COMPLIANCE_AGREEMENT_EXEMPT_URLS += ["/help/", "/contact/"]
```

Record the address a person agreed from. It is off by default, because it is personal data:

```python
MVP_COMPLIANCE_RECORD_IP_ADDRESS = True
```

Send a person somewhere other than the home page after they agree, when they were not on their
way to another page:

```python
MVP_COMPLIANCE_AGREEMENT_REDIRECT_URL = "/welcome/"
```

To stop asking altogether, take the check out of `MIDDLEWARE`. The document pages and the
acceptance records stay:

```python
MIDDLEWARE.remove("mvp_compliance.middleware.AgreementMiddleware")
```

The package documents the rest, including how long a person who has agreed goes unchecked and
what the check costs a page cache, under
[enforcement](https://github.com/django-mvp/django-mvp-compliance/blob/main/docs/enforcement.md).
