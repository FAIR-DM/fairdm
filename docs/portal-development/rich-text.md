# Rich text and markdown

Several FairDM fields hold markdown rather than plain text: a contributor's profile
biography, and the descriptions attached to projects, datasets and samples. This page
covers how that markdown is edited, how it is turned into HTML, and how to render it in
your own templates.

## Rendering markdown in a template

Use the `safe_markdown` filter from the `fairdm` template library:

```html
{% load fairdm %}

<div class="description">{{ dataset.description|safe_markdown }}</div>
```

The filter returns HTML that is ready to insert into the page, so do not add `|safe`
after it and do not wrap it in `{% autoescape off %}`.

Behind the filter is `fairdm.utils.markdown.markdownify`, which you can call directly
from Python:

```python
from fairdm.utils.markdown import markdownify

markdownify("**bold** <script>alert(1)</script>")
# '<p><strong>bold</strong> </p>'
```

Both paths sanitise their output. Markdown permits raw HTML, and these fields are filled
in by portal users, so the rendered HTML has scripts, event-handler attributes such as
`onerror`, and unsafe URL schemes such as `javascript:` removed before it reaches a page.
Links come back carrying `rel="noopener noreferrer"`. Ordinary markdown — headings,
emphasis, lists, links, images, tables, fenced code, footnotes and strikethrough — passes
through untouched.

## Adding a markdown field to your own form

Use `MarkdownxFormField`, which renders a side-by-side editor and live preview:

```python
from django import forms
from markdownx.fields import MarkdownxFormField


class NoteForm(forms.Form):
    body = MarkdownxFormField(required=False, label="Notes")
```

The editor needs its own JavaScript, so the template rendering the form must emit the
form's media:

```html
{% block extra_js %}
  {{ block.super }}
  {{ form.media.js }}
{% endblock extra_js %}
```

The live preview renders through the same sanitising function as the page, so what an
author sees while typing is what the page will show. Image upload is not enabled: pasting
or dragging an image into the editor does nothing, and there is no endpoint that accepts
uploaded files.

## Settings

### `FAIRDM_MARKDOWN_EXTENSIONS`

The list of [Python-Markdown](https://python-markdown.github.io/) extensions applied when
markdown is rendered. It is read by both the template filter and the editor's preview, so
changing it changes both. The default is:

```python
FAIRDM_MARKDOWN_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.nl2br",
    "markdown.extensions.smarty",
    "markdown.extensions.sane_lists",
    "pymdownx.magiclink",
    "pymdownx.tilde",
]
```

To add task lists to every markdown field in your portal, append the extension in your
portal's settings:

```python
FAIRDM_MARKDOWN_EXTENSIONS = [
    *FAIRDM_MARKDOWN_EXTENSIONS,
    "pymdownx.tasklist",
]
```

Adding an extension does not widen what the sanitiser allows. An extension that emits
markup outside the permitted set will have that markup stripped, so check the result on a
page before relying on it.

### `FAIRDM_INVITATION_ONLY_SIGNUP`

Set to `True` to close self-service signup, so that accounts are created by
administrators rather than by visitors:

```python
FAIRDM_INVITATION_ONLY_SIGNUP = True
```

The default is `False`. Profile claiming is unaffected either way — someone holding a
valid claim link can still claim their profile on a portal with signup closed.

## Upgrading from an earlier release

FairDM previously used martor for markdown editing and django-invitations for the signup
gate. Both are licensed under the GPL, which a portal built on FairDM cannot rely on, so
both have been replaced. Three changes affect existing portals.

**Replace `INVITATIONS_INVITATION_ONLY` with `FAIRDM_INVITATION_ONLY_SIGNUP`.** The
values and the behaviour are the same; only the name has changed. A portal that never set
it needs no change.

**Remove any `MARTOR_*` settings from your portal's settings module.** Nothing reads them
any more. If you had customised `MARTOR_MARKDOWN_EXTENSIONS`, carry your additions over to
`FAIRDM_MARKDOWN_EXTENSIONS`.

**Replace `{% load martortags %}` with `{% load fairdm %}`** in your own templates. The
filter is still called `safe_markdown` and still takes the same argument, so the tag using
it does not change.

Stored content renders as it did before, with one exception: `++inserted++` no longer
renders as underlined text and now appears literally. Strikethrough with `~~two tildes~~`
still works. If your portal has content using the insert syntax, search for it and rewrite
those passages before upgrading.
