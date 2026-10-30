# How markdown is sanitised

This page explains why FairDM cleans the HTML that markdown produces, where the cleaning happens, and what it does and does not promise. It does not show how to render markdown, which is a task in [How to render markdown in a template](../how-to/render-markdown-in-a-template.md).

## Why the output is cleaned

Several fields hold markdown that portal users type: a profile, and the descriptions of projects, datasets and samples. Markdown allows raw HTML. A person could write a script tag or an `onerror` attribute into a description, and every visitor who opened the page would run it.

FairDM therefore never sends the HTML a markdown library produces straight to a page. It renders the markdown, then cleans the result, and only the cleaned HTML reaches a visitor. The cleaning removes scripts, event-handler attributes and unsafe URL schemes such as `javascript:`, and gives links `rel="noopener noreferrer"`.

## One function renders it

`fairdm.utils.markdown.markdownify` is the only place markdown becomes HTML. It works in two steps:

1. The `markdown` library renders the text with the extensions in `FAIRDM_MARKDOWN_EXTENSIONS`.
2. The `nh3` library cleans the HTML with its default rules. FairDM does not change them.

The `safe_markdown` template filter, which draws the text on a page, calls it. Anything else that turns a portal's markdown into HTML, such as the live preview of an editor a portal adds, calls it too, so it shows what the page shows and is never an unclean route to a page.

## The cleaning happens when the page is drawn

The stored text is the markdown the author wrote, unchanged. Cleaning happens each time a page renders it. A change to the cleaning rules applies to old text without a migration, and the original is never lost.

## What `safe_markdown` promises

The filter marks its output safe, which tells Django not to escape it. That is only correct because `markdownify` has just cleaned the HTML. This is why you never add `|safe` after the filter. It would add nothing.

A plain-text summary needs no such trust. `get_abstract_summary()` renders the abstract through `markdownify`, strips the tags and returns text. Django escapes that text like any other string, so it is never marked safe.

## Limits

- **An extension cannot widen what is allowed.** Cleaning runs after the extensions. An extension that emits a tag or attribute outside the cleaner's allowed set has that markup removed. Check the result of a new extension on a page before you rely on it.
- **Removal is silent.** The cleaner drops what it forbids and says nothing, so an author who wrote a script tag sees it vanish without a message.
- **Cleaning is not a content check.** It makes the HTML safe to show. It does not judge whether the text is accurate or appropriate.

The extensions are listed in [Settings](../reference/settings.md).
