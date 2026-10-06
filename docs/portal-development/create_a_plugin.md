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

A link to a plugin that is not yours may point at nothing, because a portal can remove a plugin
from a record type (see [Removing a plugin](#removing-a-plugin)). Ask for the address with a
default, and draw the link only when you got one:

```python
from fairdm.contrib.plugins import reverse

url = reverse(self.base_object, "contribution-list", default="")
```

Without `default`, `reverse` raises `NoReverseMatch` for a name that does not resolve, as Django
does. In a template, `{% plugin_url "contribution-list" %}` from `plugin_tags` writes an empty
string in the same case, so test it before writing the anchor.

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

## Removing a plugin

A portal or an addon can take a registered plugin away from one record type with `plugins.remove`.
Name the plugin by its class or by the name it is served under, and declare the removal beside the
registrations, in a `plugins.py` module of an installed app:

```python
# myportal/plugins.py
from fairdm import plugins
from fairdm.core.sample.models import Sample
from fairdm.core.sample.plugins import Keywords

plugins.remove(Sample, Keywords)  # or plugins.remove(Sample, "keywords")
```

Nothing is checked when `remove` is called, because the plugin may be registered after the
removal is declared. The result is the same whichever comes first.

A removed plugin is gone from that record type and from no other:

- It has no navigation entry, no page action and no card.
- Its address, and the address of each of its further views, answers as one that never existed.
  There is no redirect.
- Its name does not resolve, so `reverse(sample, "keywords")` raises `NoReverseMatch`.
- Nothing stored changes. Removing the plugin that manages credits leaves every credit as it was.
- `registry.get_plugins_for_model(Sample)` still returns the registration, because it returns what
  was declared. `registry.resolve(Sample)` is what the record type serves, and the plugin is not
  in it.

Pages FairDM ships that link to a plugin are served without the link when the plugin is removed.
The Manage menu of a sample leaves out the entries for pages that are gone, and the Contributors
page of a dataset is served without the button to the project's Contributors page when a portal
has removed that page from projects.

The overview of a record type cannot be removed. The portal does not start when a removal names
it, and a record without an overview has no page of its own. It can be
[replaced](#replacing-the-overview) instead.

## Replacing a plugin

A portal or an addon can serve its own plugin in place of one that is already registered, on one
record type, by registering it with `replaces`. Name the plugin it takes over from by its class or
by the name it is served under. FairDM ships a basic version of a page, and an addon swaps it whole
without touching a template or a URL configuration.

```python
# myportal/plugins.py
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.core.sample.models import Sample
from fairdm.core.sample.plugins import Descriptions


@plugins.register(Sample, replaces=Descriptions)  # or replaces="basic-information"
class GuidedDescriptions(Descriptions):
    name = "guided-descriptions"
    title = _("Guided descriptions")
```

A sample's descriptions are now edited with `GuidedDescriptions`. It answers at
`/samples/<uuid>/basic-information/`, and `reverse(sample, "basic-information")` returns that
address, so every link and bookmark that reached the shipped page reaches the replacement. The
shipped class is not served on samples. On every other record type that registers it, nothing
changes.

### What the replacement takes over, and what it does not

The replacement is served under the name and at the address of the plugin it replaces, and it
appears in the same place on the page: a replacement for a page is a navigation entry, a
replacement for a page action is a page action, and a replacement for a card is a card. A
replacement that names a different place is refused. Leaving `place` out takes the place of the
plugin it replaces. A replacement card still says `place="card"`, because a `Card` is refused as
anything else.

The entry carries over from the plugin that was replaced:

| Carries over | Unless the replacement states its own |
| --- | --- |
| `label`, `icon` and `order` of the entry | `label=`, `icon=` or `order=` in the registration |
| `column` of a card | `column=` in the registration |
| A declined entry (`menu=False`) | `menu=` in the registration |

A replacement that gives no `label` does not get one made from its own class name. It keeps the
label of the plugin it replaced. Each of these is decided on its own: a replacement that states
only an icon keeps the label and the position.

Nothing else carries over:

- The access decision is the replacement's own. Its `check` and `permission` decide who is offered
  it and who opens it, and nothing of the replaced plugin's is asked. A visitor the replaced plugin
  admitted can be refused, and one it refused can be admitted.
- The `url_path` and `name` of the replacement are not used for serving. They are the segment and
  name of the plugin it replaces. The replacement's own name only identifies it, so a second
  replacement or a removal can refer to it.
- The views the replaced plugin owned through `extra_views` are not served. If the replacement
  declares a view at the same segment, that view is served. A replacement built on the plugin it
  replaces inherits the views, and so serves them.
- A view the replacement owns is served beneath the same address and named `<name>-<view>`, where
  `<name>` is the name of the plugin that was replaced.

`registry.get_plugins_for_model(Sample)` still returns both registrations as they were made.
`registry.resolve(Sample)` has one mount for the page, whose `plugin_class` is the replacement and whose `name`
and `url_path` are the replaced plugin's.

### The order does not matter

A replacement may be registered before or after the plugin it replaces, and the portal starts the
same way in both cases. A replacement built on the plugin it replaces keeps that plugin's `url_path`,
and is not refused for sharing it. Addons load in an order a portal developer does not control,
which is why this holds.

A replacement built on a plugin that sets `name` must set its own, as `GuidedDescriptions` does.
The shipped `Descriptions` page of a sample sets `name = "basic-information"`, and a subclass
inherits it, which the registry refuses as a second plugin with the same name.

### Replacing the overview

The overview of a record type can be replaced like any other plugin. Build the replacement on the
shipped overview and it keeps what draws the page actions and the cards, so registered actions and
cards still appear:

```python
from fairdm.core.dataset.models import Dataset
from fairdm.core.dataset.plugins import Overview


@plugins.register(Dataset, replaces=Overview)
class RicherOverview(Overview):
    template_name = "myportal/dataset_overview.html"
```

A replacement overview that is not built on the shipped one draws neither. When a page action or a
card is registered for that record type, the portal does not start, and the message names the
plugin and the record type.

### Replacing a replacement, and removing one

A replacement can itself be replaced, by naming the first replacement. The result is served at the
address of the first plugin of the chain, by the last replacement:

```python
@plugins.register(Sample, replaces="guided-descriptions")
class FullDescriptions(GuidedDescriptions):
    name = "full-descriptions"
```

Each link keeps what the one before it had unless it states its own. Removing the last
replacement of a chain with `plugins.remove(Sample, FullDescriptions)` serves the one before it again.
Removing a plugin that another replacement names is refused, because the replacement would have
nothing to replace.

### When two addons replace one plugin

Two replacements for one plugin on one record type are a conflict, and the portal does not start.
The message names both. The portal settles it by removing the one it does not want, in its own
`plugins.py`:

```python
plugins.remove(Sample, "descriptions-from-the-second-addon")
```

The other is then the replacement. The result is the same whichever addon loads first.

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

An additional view is decided by its own `check` and `permission`, not by its plugin's. Restricting
the plugin restricts the plugin's own page, so give each additional view the rule it needs, as
`NoteCreate` and `NoteEdit` do with `permission` above.

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

`registry.resolve(Dataset)` works out from them what the record type actually serves. It weighs each
registration as a `Candidate`, which holds the `Mount` the registration declares and the options it
was made with. It returns one `Mount` per plugin served: each registration that has not been
removed, with a replacement standing in the mount of the plugin it replaces.

A `Mount` is read-only and carries the `plugin_class`, the `name` it is served under, its
`url_path` (`None` for the record's own address), its `place`, and the `label`, `icon` and `order`
of its entry. `listed` is false when the registration declined its entry. `column` is the column of
a card and `None` for anything else. The URL patterns, the navigation and the page actions are all
built from this list, and so are the checks that refuse a registration that cannot work.
`registry.get_page_actions(Dataset)` returns the listed actions among them, by `order` and then
name, and `registry.get_cards(Dataset)` returns the cards the same way.

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
- a removal that names a plugin not registered against that record type. The message names the
  removal and the record type, so a misspelt name stops the portal instead of removing nothing
- a removal of the record type's overview, which is the plugin built on `OverviewPlaces` or served
  at the record's own address
- a `replaces` that is neither a plugin class nor the name of one
- a replacement that names a plugin not registered against that record type. The message names the
  replacement and the record type
- a replacement for a plugin that is removed from that record type. The message names the
  replacement and the removal
- two replacements for one plugin, unless one of them is removed. The message names both
- replacements that name each other, or one that names itself
- a replacement in a different place from the plugin it replaces, such as a card replacing a page.
  The message names both
- a replacement whose further views would generate an address name another plugin of the record
  type already generates
- a replacement for the overview that is not built on `OverviewPlaces`, on a record type that has a
  page action or a card

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
