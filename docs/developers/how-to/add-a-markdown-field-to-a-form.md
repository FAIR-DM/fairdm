# How to add a markdown field to a form

A markdown field gives the person filling in a form a text box with a live preview. You add one to a form of your own when people need to write formatted text, such as notes on a record.

## Before you start

The portal uses FairDM's URL configuration, `fairdm.conf.urls`. It mounts the preview address `/markdownx/markdownify/` that the editor posts to.

## Steps

1. Declare the field on your form with `MarkdownxFormField`.

   ```python
   from django import forms
   from markdownx.fields import MarkdownxFormField


   class NoteForm(forms.Form):
       body = MarkdownxFormField(required=False, label="Notes")
   ```

   The field takes the same arguments as Django's `CharField`.

2. Make the template that shows the form emit the form's scripts. The editor does not work without them.

   ```django
   {% block extra_js %}
     {{ block.super }}
     {{ form.media.js }}
   {% endblock extra_js %}
   ```

3. Render the stored text on the pages that show it, with `safe_markdown`. See [How to render markdown in a template](render-markdown-in-a-template.md).

## The result

The form shows the text box with a preview beside it. The preview renders through the same function as the page, so what the author sees while typing is what the page will show. The extensions come from `FAIRDM_MARKDOWN_EXTENSIONS`, described in [Settings](../reference/settings.md).

Image upload is not available. Pasting or dragging an image into the editor does nothing, and the portal has no address that accepts uploaded files.

The sanitiser removes markup the extensions emit outside its allowed set, so check the result on a page before you rely on an extension. See [How markdown is sanitised](../explanation/how-markdown-is-sanitised.md).
