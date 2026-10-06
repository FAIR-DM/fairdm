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

## Where a plugin appears

A registration names one place for its plugin with `place`. The default is the record's local
navigation, so every registration that names none behaves as it always has.

| Place | What it gives the plugin |
| --- | --- |
| `Place.NAVIGATION` (`"navigation"`) | An entry in the record's local navigation. This is the default. |
| `Place.ACTION` (`"action"`) | An entry in the dropdown of page actions on the record's overview. |
| `Place.CARD` (`"card"`) | A card drawn inside the record's overview. |

The place is a `Place` member or its value, so these two registrations are the same:

```python
from fairdm.contrib.plugins import Place

plugins.register(Dataset, place=Place.ACTION)
plugins.register(Dataset, place="action")
```

Whichever place a plugin names, it is a plugin like any other, and `check` and `permission` decide
both whether it is offered and whether it opens. A page and a page action have their own address
and are served by their own view. A card is drawn inside the overview and has no address of its
own.

## A page action

A page action is something a visitor does with a record, such as following a dataset or reporting
a problem with it. It is offered in a dropdown among the buttons in the header of the record's
overview, and choosing it takes the visitor to the plugin's page for that record.

```python
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins import Place, Plugin
from fairdm.core.dataset.models import Dataset
from fairdm.views import FairDMTemplateView


@plugins.register(Dataset, place=Place.ACTION, label=_("Follow"), icon="bell", order=10)
class Follow(Plugin, FairDMTemplateView):
    template_name = "myapp/plugins/follow.html"
    check = staticmethod(lambda request, obj: request.user.is_authenticated)
```

That serves `/datasets/<uuid>/follow/` and adds Follow to the dropdown on every dataset's
overview, for signed-in visitors. The dropdown has no entry for it in the local navigation.

The label, icon and position come from the registration, with the same defaults a navigation
entry has. Actions are listed by `order`, lowest first, and by name when two share an order, so the
list is the same on every start of the portal.

What decides who is offered an action is what decides who may open it:

- A visitor is offered an action when `check` and `permission` let them open it for this record,
  signed in or not. A plugin with neither is offered to everyone.
- A visitor who types the address of an action they are not offered is refused, as for any plugin.
- A `check` that raises hides the action and logs the failure. The page is still served.
- `menu=False` serves the plugin at its address and does not offer it.

When no action is offered to a visitor, the overview draws no dropdown.

The overview of a project, dataset, sample, measurement, person and organization draws page
actions. A person's and an organization's overviews are one registration against `Contributor`, so
an action for people only narrows itself:

```python
from fairdm.contrib.contributors.models import Contributor, Person
from fairdm.contrib.plugins import is_instance_of


@plugins.register(Contributor, place=Place.ACTION, label=_("Message"), icon="email")
class Message(Plugin, FairDMTemplateView):
    template_name = "myapp/plugins/message.html"
    check = staticmethod(is_instance_of(Person))
```

The page actions are separate from the Manage menu. The Manage menu holds what people with rights
over the record can do to it, and a plugin cannot register an entry there.

A record type draws page actions when one of its registered plugins is built on `OverviewPlaces`,
which `OverviewPlugin` carries, so a subclass of any shipped overview has it. An overview that
replaces the header buttons keeps the dropdown, which sits in its own block,
`overview.page_actions`. See [Overview pages](overview-pages.md).

## An overview card

An overview card is a block of content drawn inside the overview of a record, among the cards the
page already has. A project's recent activity is one. It is not a page: it has no address, no entry
in the local navigation and no place among the page actions.

A card is a `Card`, which is a plugin with a template and no view of its own. The overview asks it
to draw itself with the record being viewed and the current request, and the template receives them
as `record` and `request`. The record is also given as `base_object`.

```python
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins import Card, Column, Place, Plugin, reverse
from fairdm.core.dataset.models import Dataset
from fairdm.views import FairDMTemplateView


class Subscribe(Plugin, FairDMTemplateView):
    url_path = "subscribe"
    template_name = "myapp/plugins/subscribe.html"


@plugins.register(Dataset, place=Place.CARD, column=Column.WIDE, order=10)
class RecentActivity(Card):
    template_name = "myapp/cards/recent_activity.html"
    extra_views = [Subscribe]
    check = staticmethod(lambda request, obj: request.user.is_authenticated)

    class Media:
        css = {"all": ["myapp/recent-activity.css"]}
        js = ["myapp/recent-activity.js"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["events"] = latest_events(self.base_object)
        context["subscribe_url"] = reverse(self.base_object, "recent-activity-subscribe")
        return context
```

That draws Recent activity at the end of the wide column of every dataset's overview, for signed-in
visitors, and serves the subscribe page at `/datasets/<uuid>/recent-activity/subscribe/`. The card
has no address at `/datasets/<uuid>/recent-activity/`.

A card that draws something other than a template overrides `render_card(request, record)` and
returns the HTML. A card needs a `template_name` or its own `render_card`, and registration refuses
one that has neither.

### The column and the order

`column` is `Column.WIDE` or `Column.SIDE`, or the value `"wide"` or `"side"`. A card that names no
column goes in the side column. Contributed cards follow the cards the page already has in their
column. Among themselves they are drawn by `order`, lowest first, and by name when two share an
order, so the cards come out in the same order on every start of the portal.

The label and icon of a registration mean nothing for a card, and `menu=False` is refused because
a card has no entry to decline.

### Who sees a card

A card is drawn when `check` and `permission` let the visitor open it for this record. For anyone
else nothing of the card is in the page, including its stylesheets and scripts. The overview is
decided first: a card is never drawn on a page the visitor was refused.

- A `check` that raises hides the card and logs the failure.
- A card that raises while it is being drawn is left out, the rest of the page is served, and the
  failure is logged with the card's name and the record.
- A card with nothing to say is still drawn. What it shows then is the card's own business.

The same plugin cannot be both a page and a card. That is two plugins, one registered for each
place.

### A card's further views

A card can own further views, such as the address a form inside it posts to. They are listed in
`extra_views`, served beneath the card's name and named after it, as `dataset:recent-activity-subscribe`
above.

A further view of a card is refused unless the card would be drawn for that visitor. Three things
must hold in turn:

1. The record type's overview opens for them. A card with no `check` on a private project does not
   serve its views to a stranger, because the overview itself is refused.
2. The card's own `check` and `permission` pass.
3. The view's own `check` and `permission` pass.

A further view of a page is decided by its own rule only, as it always was.

### Assets

A card declares stylesheets and scripts with an inner `Media` class, as a page does. They are added
to the overview's own when the card is drawn and left out when it is not.

### Which record types draw cards

The overview of a project, dataset, sample, measurement, person and organization draws cards. A
person's and an organization's overviews are one registration against `Contributor`, so a card for
people only narrows itself with `is_instance_of(Person)`.

The cards are written by `overview/page.html` in two blocks, `overview.contributed_main` after the
wide column and `overview.contributed_side` after the side column. A portal that overrides the
template and drops them shows no cards, and everything else keeps working. See
[Overview pages](overview-pages.md).

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

**A worked example.** `check` does not carry from a registration to its extra views — the owner is
read from `plugin_class`, which only exists on the view instance, while `has_permission` passes the
class — so an extra view that wants the same visibility rule as its owner writes it again rather
than relying on inheritance. `fairdm.core.project.plugins` builds its checks as small functions so
each page states its own rule explicitly without repeating the logic:

```python
def project_is_visible(request, obj):
    """A public project always, a private one only with project.view_project."""
    if obj is None:
        return True
    if obj.visibility == Visibility.PUBLIC:
        return True
    return has_perm(request, "project.view_project", obj)


def visible_to_holder_of(permission):
    """Like project_is_visible, except a private obj also stays visible to a
    user holding `permission` on it specifically, at record level."""

    def check(request, obj):
        if project_is_visible(request, obj):
            return True
        if obj is None:
            return False
        return request.user.has_perm(permission, obj)

    return check
```

`Update` and `Delete` each set `check = staticmethod(visible_to_holder_of("project.change_project"))`
(and `"project.delete_project"` respectively) rather than the bare `project_is_visible` their owner
uses: their own `permission` is the change/delete right, not the view right, and a record-level grant
of a page's own permission is already evidence of legitimate access.

`fairdm.core.dataset.plugins.dataset_is_visible` is the same rule for a dataset, reading
`dataset.view_dataset`. Write one of these for every record type you register pages against, even
when the model's default manager already hides private records: a registered page resolves its
record through `Plugin.get_base_object`, which reads past that manager on purpose, so that a
private record's owner can still open it. The manager is not the gate; the check is.

**Refusing without confirming the record exists.** The default refusal redirects an anonymous
visitor to sign in and gives a signed-in stranger a permission error. Both answers tell whoever
typed the address that there is something at it, which is the wrong answer for embargoed metadata.
Where that matters, override `handle_no_permission` to raise `Http404` while the record is private,
and fall through to the default once it is public — a refusal on a public record should say plainly
why it was refused:

```python
def handle_no_permission(self):
    obj = self.base_object
    if obj is not None and obj.visibility != Visibility.PUBLIC:
        raise Http404("No dataset matches the given query.")
    return super().handle_no_permission()
```

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

## What a record type serves

The registry keeps every registration as it was made. `registry.get_plugins_for_model(Dataset)`
returns the `(plugin class, options)` pairs in the order they arrived.

`registry.resolve(Dataset)` works out from them what the record type actually serves. It returns
one `Mount` per registration. A `Mount` is read-only and carries the `plugin_class`, the `name` it
is served under, its `url_path` (`None` for the record's own address), its `place`, and the
`label`, `icon` and `order` of its entry. `listed` is false when the registration declined its
entry. `column` is the column of a card and `None` for anything else. The URL patterns, the navigation and the page actions are all built from this list, and so
are the checks that refuse a registration that cannot work. `registry.get_page_actions(Dataset)`
returns the listed actions among them, by `order` and then name, and `registry.get_cards(Dataset)`
returns the cards the same way.

## When a registration is wrong

A registration that cannot work is refused when it is made, and the portal does not start. The
message names the plugin, the record and the problem. When the portal starts, every record type's
registrations are checked together, and the same applies to what that finds. Refused cases:

- no model given, or something that is not a model
- two plugins claiming the same name or the same segment on one record
- two plugins whose generated address names would collide
- a segment that cannot appear in a route
- a `check` that is neither callable nor a bool
- a `place` that does not exist
- a `column` given for anything that is not a card, or a column that does not exist
- a card registered with `menu=False`
- a card whose class is not built on `Card`, or has neither a `template_name` nor its own
  `render_card`
- a `Card` registered as a page or a page action, since it has no page of its own
- a page action or a card registered for a record type whose overview draws none, such as a
  location. The portal does not start, and the message names the plugin and the record type
- an `extra_views` entry that is not a plugin, that collides with a sibling or the parent, or that
  declares `extra_views` of its own

The same plugin name on two different records is fine. Names are unique per record, not globally.

## Reusable plugins

A plugin is an ordinary class, so a package can ship a base and a portal can subclass it:

```python
# In the distributed package
class CitationsPlugin(Plugin, FairDMUpdateView):
    form_class = CitationForm


# In the portal
@plugins.register(MySample, label=_("Citations"), icon="quote", order=520)
class Citations(CitationsPlugin):
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
