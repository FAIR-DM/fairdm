# Create a plugin

A plugin is a Django view attached to one of the core record types. Write the view, register it
against the record, and the framework supplies the address, the entry in that record's local
navigation, and access to the record itself.

Nothing else in the framework has to change, which is the point: an addon distributed as a package
can add pages to a portal that has never heard of it.

## A working plugin in one file

Create `plugins.py` in your app. FairDM imports it at startup.

```python
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.sample.models import Sample
from fairdm.views import FairDMTemplateView


@plugins.register(Sample, label=_("Analysis"), icon="chart", order=100)
class Analysis(Plugin, FairDMTemplateView):
    template_name = "myapp/plugins/analysis.html"
```

That serves `/samples/<uuid>/analysis/` and adds an Analysis entry to every sample's navigation.

In the template, the record is `base_object`:

```django
{% extends "fairdm/plugin.html" %}

{% block content %}
  <h2>{{ base_object }}</h2>
{% endblock content %}
```

## The address

The path segment is the class name, slugified — `Analysis` becomes `analysis`. Set `url_path` to
choose your own:

```python
class Analysis(Plugin, FairDMTemplateView):
    url_path = "analysis-report"
```

The address is reversible through the record's namespace:

```python
reverse("sample:analysis", kwargs={"uuid": sample.uuid})
```

A segment may carry a route converter, which is how a view that acts on something other than the
record identifies its target:

```python
class EditNote(Plugin, FairDMUpdateView):
    url_path = "<int:pk>/edit"
```

## Reaching the record

`base_object` is the core record the plugin hangs from, available on the view and in the template
context. It is a separate thing from `self.object`, which stays whatever your view class decides it
is — so a plugin over an `UpdateView` keeps its own object, its own form and its own `form_valid`,
and registration changes none of them.

```python
@plugins.register(Sample, label=_("Notes"))
class Notes(Plugin, FairDMListView):
    model = Note

    def get_queryset(self):
        return Note.objects.filter(sample=self.base_object)
```

Requesting a record that does not exist returns 404.

## The navigation entry

Label, icon and position come from the registration, and nowhere else:

```python
@plugins.register(Sample, label=_("Analysis"), icon="chart", order=100)
```

- `label` — the text shown. Defaults to the class name.
- `icon` — defaults to `circle`.
- `order` — position among the record's entries. Lower comes first. Defaults to `0`.

A plugin reached only from a button inside another page can decline its entry and stay reachable at
its address:

```python
@plugins.register(Sample, menu=False)
class PrintView(Plugin, FairDMTemplateView):
    ...
```

## Who can see it, and who can open it

Two things decide, and they answer different questions.

`check` decides whether the **entry appears**, for this user and this record. It takes the request
and the record:

```python
from fairdm.contrib.plugins import is_instance_of
from myapp.models import RockSample


@plugins.register(Sample, label=_("Petrology"))
class Petrology(Plugin, FairDMTemplateView):
    check = staticmethod(is_instance_of(RockSample))
```

`permission` decides whether the **page may be opened**, and it belongs to each view class, so a
plugin's read view and its edit view can differ:

```python
@plugins.register(Sample, label=_("Curate"))
class Curate(Plugin, FairDMUpdateView):
    permission = "sample.change_sample"
```

**The two are one guarantee.** A surface that is not shown cannot be reached, and one that is not
reachable is not shown. You cannot hide a page with `check` and leave it open to anyone who types
the address, and you cannot restrict a page with `permission` and still advertise it.

Permission is satisfied by a model-level grant or an object-level one, so a user given rights over
a single record can open its pages without holding the permission globally.

Write `check` as a plain function, a lambda or a `staticmethod`. A `classmethod` is refused at
registration, because it is truthy but not callable and would quietly permit everyone.

## A feature that is more than one page

Declare the other views on the plugin. They share its address prefix and its single navigation
entry, and each carries its own permission:

```python
class NoteCreate(Plugin, FairDMCreateView):
    url_path = "add"
    permission = "myapp.add_note"


class NoteEdit(Plugin, FairDMUpdateView):
    url_path = "<int:pk>/edit"
    permission = "myapp.change_note"


@plugins.register(Sample, label=_("Notes"), icon="note", order=200)
class Notes(Plugin, FairDMListView):
    url_path = "notes"
    extra_views = [NoteCreate, NoteEdit]
```

That serves `/samples/<uuid>/notes/`, `/samples/<uuid>/notes/add/` and
`/samples/<uuid>/notes/<pk>/edit/`, under the names `sample:notes`, `sample:notes-note-create` and
`sample:notes-note-edit`.

An additional view inherits its plugin's `check`, so restricting the plugin restricts everything it
owns.

## Templates, assets and context

Template selection is Django's. Set `template_name`, or override `get_template_names()`.

Declare stylesheets and scripts with an inner `Media` class, as on a Django form:

```python
class Analysis(Plugin, FairDMTemplateView):
    class Media:
        css = {"all": ["myapp/analysis.css"]}
        js = ["myapp/analysis.js"]
```

Add context the ordinary way; what the framework supplies is preserved alongside it:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["summary"] = summarise(self.base_object)
    return context
```

## When a registration is wrong

A registration that cannot work is refused when it is made, and the portal does not start. The
message names the plugin, the record and the problem. Refused cases:

- no model given, or something that is not a model
- two plugins claiming the same name or the same segment on one record
- two plugins whose generated address names would collide
- a segment that cannot appear in a route
- a `check` that is neither callable nor a bool
- an `extra_views` entry that is not a plugin, that collides with a sibling or the parent, or that
  declares `extra_views` of its own

The same plugin name on two different records is fine. Names are unique per record, not globally.

## Reusable plugins

A plugin is an ordinary class, so a package can ship a base and a portal can subclass it:

```python
# In the distributed package
class KeywordsPlugin(Plugin, FairDMUpdateView):
    form_class = KeywordForm


# In the portal
@plugins.register(MySample, label=_("Keywords"), icon="tag", order=520)
class Keywords(KeywordsPlugin):
    pass
```

## What a record needs to accept plugins

A record type needs its plugin addresses mounted in a URL configuration:

```python
from fairdm.plugins import registry

urlpatterns = [
    path(
        f"samples/{registry.route_for(Sample)}/",
        include((registry.get_urls_for_model(Sample), "sample")),
    ),
]
```

Most records are found by `uuid`, which is the default. A record identified some other way declares
how, and the plugin machinery resolves and reverses it without further help:

```python
registry.declare_addressing(
    Point,
    route="<str:lon>/<str:lat>",
    lookup={"lon": "x", "lat": "y"},
)
```

Measurements are the exception: a measurement is a component of the sample page rather than a record
with a page of its own, so it has no navigation and nothing to attach to.
