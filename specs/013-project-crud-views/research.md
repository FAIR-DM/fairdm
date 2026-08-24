# Research — 013 Managing a project through the portal

Dated 2026-08-23. Everything below was read in the working tree or executed against it. Claims
carry a `file.py:LINE`; the few things that were run rather than read say so.

## The finding that changes the plan

**The portal already has a second project editing page, and it is the only one anyone can click.**

`ProjectConfigure` (`fairdm/core/project/plugins.py:40-48`) is a registered plugin — label
"Configure", icon `settings`, route `project/<uuid>/project-configure/`. It is a `FairDMUpdateView`
over `["name", "visibility", "owner"]`. Confirmed registered by listing the registry:

```
DatasetList          dataset-list/
ProjectExportView    project-export-view/
ProjectConfigure     project-configure/
ContributionList     contributors/  (+ add/, <pk>/edit/, <pk>/remove/)
```

So the project pages divide like this:

| | `project-update` | `project-configure` |
|---|---|---|
| Fields | image, name, status, visibility, owner | name, visibility, owner |
| Permission | `change_project`, object-level only (`views.py:163`) | `project.change_project`, model **or** object level (`plugins.py:44`, `contrib/plugins/access.py:43-73`) |
| Redirect | explicit, to the project (`views.py:174`) | none; falls back to `get_absolute_url()` |
| Template | `project/project_form.html` | the same |
| Reachable from the project page | **no** | **yes**, as a tab |
| Tested | yes, 4 tests (`test_views.py:254-300`) | **no test names it** |

The complete, tested, correctly-redirecting page is unlinked. The narrow, untested one is the tab.
They also answer to two different permission strings, one of which (`"change_project"`, unlabelled)
no standard Django backend can grant — only the object-level layer.

**This corrects what I reported at the specification gate.** I said there were no edit or delete
links anywhere. There is an edit route: the Configure tab. What is true is narrower and cheaper to
fix than I implied — see the next section.

## Navigation is a switch, not a build

The shell's own detail template already draws Edit and Delete buttons. `detail_view.html:8-23`
consumes `directory.update_url` and `directory.delete_url` and renders them into the page title's
actions slot (`page_view.html:16-23`, `cotton/page/title.html:10`). `project_detail.html:1` extends
that template and overrides only the tray, the content and the scripts, so it inherits the buttons.

They do not appear because nothing switches them on. Two attributes govern it, both on
`CRUDDirectoryMixin` (`.venv/…/mvp/views/detail.py:14`):

- `directory` — the list of actions resolved into context. `get_directory()` loops over this and
  nothing else (`detail.py:151-163`). `MVPDetailView` defaults it to `["update", "delete"]`
  (`detail.py:212`).
- `show_<action>_action` — a bool or a callable taking the user, defaulting to `False`
  (`detail.py:53-57`).

`ProjectDetailView` sets neither, so both resolve to `None` and the buttons are dropped. The FairDM
view layer is a thin `MetadataMixin` composition and sets none of this either (`fairdm/views/base.py`,
every class body empty or `pass`).

The deprecated names still in the project views (`views.py:44-45, 150-151`) are read first by
`show_action()` (`detail.py:111-121`), warn, and are honoured. Of the four, one is dead: the list
view's `has_list_permission` is never consulted, because `"list"` is not in a list view's
`directory`.

**The empty Back button, exactly.** `MVPDeleteView.get_back_url` ends
`return self.resolve_crud_url("list") or ""` (`edit.py:558-574`). `delete_view.html:64-68` draws
the button unconditionally, and `cotton/button.html:15` picks the element with
`href|yesno:"a,button"`. Rendered both ways:

- `back_url=""` → `<button class="btn btn-outline …" href="">Back</button>`
- `back_url="/projects/"` → `<a class="btn btn-outline …" href="/projects/">Back</a>`

A visible button that is not a link and does nothing. `ProjectDeleteView` never sets
`show_list_action`, so it takes the first path.

## The deletion refusal

The shell has a contract for exactly this and the project code invented a parallel one beside it.

The shell populates `is_protected` (a bool) and `protected_objects` (a list of instances) in
`MVPDeleteView.get_context_data` (`edit.py:614-642`), from Django's own `Collector`.
`delete_view.html:4-15` renders a red alert listing each blocker by `str()`, and the `{% else %}`
branch — the warning, the related-object summary, the type-to-confirm field and both submit buttons
— is skipped entirely (`:16-62`, `:68`). A protected page is breadcrumbs, title, alert, Back.

`ProjectDeleteView.form_valid` instead passes `protected_datasets=e.datasets` (`views.py:211-219`).
Two independent reasons it shows nothing:

1. No template reads that name. It appears twice in the repository: where it is written, and in the
   test asserting it was written.
2. Even under the right names it would not survive. Keyword arguments enter context inside
   `super().get_context_data(**kwargs)` and are then overwritten by `edit.py:619-620`.

Django's `Collector` cannot see the guard, which is a `pre_delete` signal
(`fairdm/core/project/models.py:280-298`), so the shell's own pre-flight check at `edit.py:644-656`
passes and the exception only surfaces from `self.object.delete()`. That also means a user opening
the deletion page for a blocked project today gets a fully armed confirmation form and only learns
it is refused after typing the name.

Populating the shell's two keys is a six-line change with no template surface. Overriding
`delete_view.html` in the project would copy about eighty-five lines of shell template to rename one
variable, and would drift at every release. No fairdm template overrides it today, and the loader
order would let one shadow it (`fairdm/conf/settings/apps.py:154-178` plus django-cotton's loader
injection), which is the argument for not starting.

## Editing related records — three mechanisms, one of them ours

The repository depends on two inline-formset systems and uses a third.

| Mechanism | Where it is used |
|---|---|
| `django-extra-views` `InlineFormSetView` | `fairdm/contrib/generic/plugins.py:27, 55` — the only live use in the codebase |
| The shell's own `InlineFormSet` / `MVPInlineUpdateView` (`mvp/views/inline.py:25, 420, 429`) | **nowhere** |
| Plain Django `BaseInlineFormSet` | the Django admin inlines (`project/admin.py:24`, `dataset/admin.py:74`) and `CoreInlineFormset` |

There is no recorded decision between them. `docs/adr/` (0001–0007) says nothing about formsets, and
the constitution names the shell as the default UI without reaching this far
(`memory/constitution.md:213, 313`).

**The shell's system is complete and unused.** `InlineFormSet` declares a related model and a field
list; a view lists them on `inlines`; the formsets arrive in context as `inlines`
(`mvp/views/inline.py:319`) and `form_view.html:23` renders each through
`cotton/form/formset/index.html`, which ships the management form, an inert `<template>` empty-form,
an Add-row button and `static/js/formset.js` for cloning. Saving is one atomic transaction, parent
first, and nothing is written unless every formset validates (`inline.py:322-358`).

Two defaults matter: `extra` is Django's 3 and `can_delete` is True, because the shell omits
anything left unset (`inline.py:114-116`). Three blank rows per set unless told otherwise.

**The date validation will not work by default, and the fix already exists.** `ProjectDate.clean()`
(`models.py:196-231`) compares against its sibling row by querying the database
(`_sibling_value`, `:233-239`). In a formset the sibling is usually unsaved, so:

- on a creation page the parent has no primary key, `related_id` is `None`, and `clean()` returns at
  `models.py:209-210` without checking anything;
- when both rows are submitted together, each compares against the *stored* value, giving both false
  positives and false negatives.

The correct place is a formset-level `clean()` reading across sibling forms, and that class is
already written — `DateInlineFormSet` (`fairdm/core/project/admin.py:24-66`), whose docstring states
this problem verbatim. The shell passes a `formset` attribute straight to
`inlineformset_factory` (`inline.py:60, 111`), so reusing it is one line.

**Identifier collisions surface correctly**, on the field. `AbstractIdentifier.clean()`
(`fairdm/core/abstract.py:354-371`) raises `ValidationError({"value": …})`, which `_update_errors`
attaches to the `value` field. Two conditions: `value` must be in the inline's `fields`, or
`add_error` raises `ValueError` and the page 500s; and the `(related, type)` uniqueness is *not*
checked per form, because `_post_clean` excludes the foreign key, so only same-submission duplicates
are caught.

## The descriptions machinery exists, is unregistered here, and is broken where it is registered

`fairdm/core/project/plugins.py:52-70` defines `Descriptions`, `Keywords` and `KeyDates` with their
`model` and `inline_model` set correctly and **no `@plugins.register` decorator**. Nothing else
registers them. They are unreachable.

The same base classes *are* registered on Dataset (`dataset/plugins.py:20-42, 62-79`) and Sample
(`sample/plugins.py:44-56, 70-79`), with a permission and a label. There they resolve to the wrong
template. Neither base declares `template_name` and `Plugin` supplies none, so resolution falls
through to the detail suffix. Confirmed by instantiation:

```
dataset.Descriptions.get_template_names() -> ['dataset/dataset_detail.html']
```

That file exists, so the page returns 200 rendering the record's detail page and the formset is
never drawn. The one test covering it asserts only `status_code == 200`
(`tests/test_contrib/test_plugins/test_pages.py:28-35`), so it passes over the defect. The intended
templates `fairdm/contrib/theme/templates/plugins/descriptions.html` and `plugins/key-dates.html`
exist and are referenced by nothing.

**A formset is the wrong shape for what this feature specifies anyway.** The project description
vocabulary is a closed set of seven types (`core/vocabularies.py:346-361`) with one row allowed per
type (`abstract.py:294-303`). FR-030 asks for one labelled area per type. That is a form with seven
fields, not a list you add rows to.

## What a plugin provides

Registering gives a URL, a menu entry, a permission gate, the parent record and breadcrumbs
(`fairdm/contrib/plugins/registration.py:177-218`, `base.py:104-322`). It does **not** give a
template — the co-mixed view class must supply one, which is the defect above.

The permission gate and the menu filter are the same function, which is the property worth having:
`menu_check` (`access.py:130-150`) and `Plugin.has_permission` (`base.py:243`) both call `can_open`,
so a plugin a user may not open is a tab they are not shown. That satisfies FR-042 for free.

The trap is the default. A plugin with no `permission` is open to everyone including anonymous
users (`access.py:99-127`), and `base.py:195-205` says so explicitly.

## Test material

Factories for all three related models exist: `ProjectDescriptionFactory` (`fairdm/factories/core.py:126`),
`ProjectDateFactory` (`:136`), `ProjectIdentifierFactory` (`:146`), each taking `related=<project>`.
`ProjectDateFactory` is **not** re-exported from `fairdm/factories/__init__.py` while its dataset,
sample and measurement equivalents are, so existing tests import it from the module directly
(`tests/test_core/test_project/test_admin.py:21`).

The suite is pytest-function style. Django's `assertContains` / `assertTemplateUsed` /
`assertInHTML` appear **nowhere** in `tests/`, so a "this link is on the page" assertion is a new
pattern; the closest existing idiom is a raw substring check against `response.content`
(`test_views.py:155-156`).

Warnings are not errors: `pyproject.toml:381` sets `filterwarnings = ["ignore", "default:::keywords"]`,
so the first entry silences everything. Asserting the deprecation is gone needs an explicit
`pytest.mark.filterwarnings("error::mvp.warnings.MVPDeprecationWarning")` on the test, which
overrides the file-level list.

## Found here, not this feature's work

Verified by running requests against the test client, not by reading alone.

- **The contributor plugin pages have no permission gate.** `ContributionList`, `ContributionCreate`
  and `ContributionRemove` all carry `permission = None` and `check = True`
  (`contrib/contributors/plugins/shared.py`), so `can_open` returns `True` for everyone. An
  anonymous GET of `project/<uuid>/contributors/` returns **200**. The dataset plugins one module
  over declare `dataset.change_dataset` with a comment explaining why.
- **`contributors/add/` returns 500 to an anonymous request**, not 403.
  `QuickAddContributionForm` reaches `fairdm/forms/base.py:110` with an `instance` keyword its base
  does not accept. The absence of the gate and the crash are separate faults; the crash is what
  currently stops the write.
- **Contributor child views are not scoped to the parent.** `ContributionUpdate` and
  `ContributionRemove` set `model = Contribution` and override no queryset, so any contribution id
  resolves under any project's address.
- **Dataset and sample description and key-date pages render the record's detail page**, as above.
- **`ProjectDateFactory` is missing from the factories package exports.**

## Risks carried into planning

1. **The shell's inline system has no user in this repository.** It ships templates, JavaScript and
   an atomic save, and none of it is exercised here. Committing to it means being its first caller.
2. **`PartialDateField` inside a cloned formset row is unverified.** The Add-row button clones by
   string substitution on the empty form (`static/js/formset.js:39-41`), which breaks any widget
   needing initialisation beyond Alpine's own tree walk. Must be checked on a real page.
3. **Retiring `ProjectConfigure` removes a tab that exists today.** It is untested and narrower than
   its replacement, but it is the surface a user currently sees.
4. **`AbstractIdentifier.clean()` queries once per concrete subclass per row** (`abstract.py:361-365`).
   With several rows this multiplies.
