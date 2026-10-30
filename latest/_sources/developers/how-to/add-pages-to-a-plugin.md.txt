# How to add pages to a plugin

A plugin often needs more than one page: a list, a form to add an item and a form to edit one. You declare the other pages on the plugin, and they share its address prefix and its one tab.

## Before you start

You need a plugin. See [How to create a plugin](create-a-plugin.md). This guide adds a list of notes with pages to add and edit a note. `Note` stands for a model of your own with a `sample` foreign key to `Sample` and a `text` field.

## Steps

1. Write each additional page as a `Plugin` subclass over the view it needs. Give each a `url_path` and the rule that decides who may open it.

   ```python
   from fairdm.plugins import Plugin, reverse
   from fairdm.views import FairDMCreateView, FairDMTemplateView, FairDMUpdateView
   from myapp.models import Note


   class NoteCreate(Plugin, FairDMCreateView):
       model = Note
       fields = ["text"]
       url_path = "add"
       permission = "myapp.add_note"

       def form_valid(self, form):
           form.instance.sample = self.base_object
           return super().form_valid(form)

       def get_success_url(self):
           return reverse(self.base_object, "notes")


   class NoteEdit(Plugin, FairDMUpdateView):
       model = Note
       fields = ["text"]
       url_path = "<int:pk>/edit"
       permission = "myapp.change_note"

       def get_queryset(self):
           return Note.objects.filter(sample=self.base_object)

       def get_success_url(self):
           return reverse(self.base_object, "notes")
   ```

   A route converter such as `<int:pk>` in `url_path` is how a view names something other than the record. A plugin's own `get_queryset` reads the record's model, so a view over another model, such as `NoteEdit`, overrides `get_queryset` or sets `queryset`.

2. Register the main plugin and list the additional pages in `extra_views`.

   ```python
   from django.utils.translation import gettext_lazy as _

   from fairdm import plugins
   from fairdm.core.sample.models import Sample


   @plugins.register(Sample, label=_("Notes"), icon="note", order=200)
   class Notes(Plugin, FairDMTemplateView):
       template_name = "myapp/plugins/notes.html"
       url_path = "notes"
       extra_views = [NoteCreate, NoteEdit]

       def get_context_data(self, **kwargs):
           context = super().get_context_data(**kwargs)
           context["notes"] = Note.objects.filter(sample=self.base_object)
           return context
   ```

3. Give every additional page the `check` or `permission` it needs. Restricting the main plugin does not restrict its additional pages. See [How to restrict a plugin to some users](restrict-a-plugin-to-some-users.md).

4. Link between the pages with `plugin_url`, in `myapp/templates/myapp/plugins/notes.html`.

   ```django
   {% extends "page_view.html" %}
   {% load plugin_tags %}

   {% block page.content %}
     <a href="{% plugin_url 'notes-note-create' %}">Add a note</a>
     <ul>
       {% for note in notes %}
         <li>
           {{ note.text }}
           <a href="{% plugin_url 'notes-note-edit' pk=note.pk %}">Edit</a>
         </li>
       {% endfor %}
     </ul>
   {% endblock page.content %}
   ```

## The result

The three pages are served at:

| Page | Address | URL name |
|---|---|---|
| The list | `/samples/<uuid>/notes/` | `sample:notes` |
| Add | `/samples/<uuid>/notes/add/` | `sample:notes-note-create` |
| Edit | `/samples/<uuid>/notes/<pk>/edit/` | `sample:notes-note-edit` |

The sample has one tab, **Notes**, that leads to the list. The additional pages have no tab of their own.

Registration is refused, and the portal does not start, when an additional page is not a plugin, is the plugin itself, declares `extra_views` of its own, or claims the same segment as another. The full list is in [Plugins](../reference/plugins.md).
