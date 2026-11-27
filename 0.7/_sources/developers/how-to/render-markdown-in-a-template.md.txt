# How to render markdown in a template

Several FairDM fields hold markdown, such as a person's profile and the descriptions of a project, dataset or sample. You render a field in your own template with the `safe_markdown` filter, which returns sanitised HTML.

## Steps

1. Load the `fairdm` library at the top of the template.

   ```django
   {% load fairdm %}
   ```

2. Apply the filter to the markdown text.

   ```django
   <div class="prose max-w-none">{{ dataset.description|safe_markdown }}</div>
   ```

   Do not add `|safe` after the filter, and do not wrap it in `{% autoescape off %}`. The filter has already marked its output safe.

3. To render markdown in Python, call the function behind the filter.

   ```python
   from fairdm.utils.markdown import markdownify

   markdownify("**bold** <script>alert(1)</script>")
   # '<p><strong>bold</strong> </p>'
   ```

## The result

The page shows the formatted text. Scripts, event-handler attributes and unsafe URL schemes in the source are removed, and links gain `rel="noopener noreferrer"`. The filter and the function render with the extensions in `FAIRDM_MARKDOWN_EXTENSIONS`, which is described in [Settings](../reference/settings.md). Why the output is safe, and what the sanitiser leaves out, is explained in [How markdown is sanitised](../explanation/how-markdown-is-sanitised.md).

## Show plain text instead

A card, a listing or a search result needs the words without the markup. A card that prints a description directly shows `##` and `**` to the reader, and a long description sets the height of the card.

Every project, dataset, sample and measurement has `get_abstract_summary()`. It renders its abstract through the same sanitiser, drops the tags, collapses the whitespace and cuts the result at 400 characters. It returns an empty string when the record has no abstract, so a template can test it directly.

```django
{% with summary=project.get_abstract_summary %}
  {% if summary %}<p class="text-sm">{{ summary }}</p>{% endif %}
{% endwith %}
```

The result is plain text and Django escapes it like any other string. Do not add `|safe` or `safe_markdown` after it. Use `safe_markdown` for the formatting and `get_abstract_summary` for the words.

The filter is listed in [Template tags](../reference/template-tags.md).
