# Research — FS-014, managing a dataset through the portal

Written before the plan, from the code as it stands on 2026-08-25. Every claim carries the file and
line it was read from. Where the project's pages already answered a question in 013, the answer is
cited rather than re-derived.

---

## R1 — A record's pages become one registered collection

**Question**: what makes a page belong to a record rather than standing alone, and what makes the
whole set take one navigation entry?

**Answer**: a registration against the model, with the other pages declared as its `extra_views`.
`fairdm/core/project/plugins.py:263-293` is the worked example: `Overview` is registered with
`@plugins.register(Project, …)`, declares `url_path = None` so it is the root of the record's
include, and lists `extra_views = [Update, Delete, Descriptions]`. Those three carry a `url_path`
but no registration of their own, so they get addresses without getting navigation entries.

The links are drawn by `mvp.views.detail.CRUDDirectoryMixin`, mixed into `Overview`. `directory`
names the actions the page offers and `crud_views` reverses each to a real route name — the
mixin's own defaults resolve to `{model_name}-update`/`-delete`, which are exactly the standalone
routes this feature retires, so both must be stated.

**For a dataset**: the same shape. `Dataset` currently has no `Overview` registration at all
(`fairdm/core/dataset/plugins.py` registers only descriptions, keywords and key dates), and its own
page is a standalone `DatasetDetailView` (`fairdm/core/dataset/views.py:24`). A template written for
a dataset overview plugin already sits unused at
`fairdm/core/dataset/templates/dataset/plugins/overview.html` (noted in #190).

---

## R2 — An additional view inherits its owner's visibility rule, and that inheritance does not work

**Question**: does stating a permission and a visibility rule on the overview cover the pages
beneath it?

**Answer**: no, and the reason is recorded in full at `fairdm/core/project/plugins.py:28-53`. An
additional view inherits its owner's `check` but never its `permission`
(`fairdm/contrib/plugins/access.py`, `can_open`), so a page that states no permission is open to
everyone including anonymous visitors (#279). The `check` inheritance is itself broken — the owner
is read from an attribute that exists only on the view instance, while the permission machinery
passes the class — so a page relying on inheriting a visibility rule is not guarded at all. That is
#284, unrepaired, and 013 worked around it by having every page state both for itself.

**For a dataset**: every page states its own permission and its own visibility rule. FR-060 and
FR-061 say so, and this is why.

One difference from projects: a private dataset is already excluded by the model's own default
manager (`fairdm/core/dataset/models.py:159-182`), where `Project` has no privacy-filtered manager.
That does not remove the need for a per-page rule, because the plugin machinery deliberately reads
past filtered managers (`fairdm/contrib/plugins/base.py`, `get_base_object`) on the assumption the
page gates itself.

---

## R3 — Where a dataset's own address comes from

**Question**: what has to change so a dataset's pages sit below the dataset.

**Answer**: three things.

1. `Dataset.get_absolute_url()` is inherited from `BaseModel` (`fairdm/core/abstract.py:73-74`) and
   reverses `f"{model_name}-detail"`. `Project` overrides it to reverse `project:overview`
   (`fairdm/core/project/models.py:144-152`), and that override's own docstring names the dataset as
   the record still doing it the old way, citing #283.
2. `fairdm/core/dataset/urls.py` mounts the record's registered pages under the **singular**
   `dataset/<str:uuid>/` while the dataset itself sits under the plural `datasets/<str:uuid>/`. The
   project's file (`fairdm/core/project/urls.py`) shows the target shape.
3. Declaration order matters. The comment at `fairdm/core/project/urls.py:10-11` records why:
   Django matches in declaration order, so a creation route declared after the record include has
   `create` swallowed as a uuid.

**Blast radius**, from a full sweep of the repository: the four standalone route names are reversed
in `fairdm/core/dataset/views.py:88,219,239` and `fairdm/menus/menus.py:26`, in
`fairdm/templates/cotton/actions/create_new.html:16`, and across
`tests/test_core/test_dataset/test_views.py` and `tests/test_core/test_dataset/test_models.py:1963`.
The namespaced `dataset:descriptions` route is reversed in
`tests/test_contrib/test_plugins/test_pages.py:34,45`. `Dataset.get_absolute_url()` is called from
six templates and from `fairdm/core/plugins.py:121`, `fairdm/contrib/import_export/utils.py:40` and
`fairdm/contrib/plugins/base.py:313`.

The API's own `api:dataset-list` / `api:dataset-detail` names are a separate namespace and are
untouched. `tests/test_api/test_router.py:265-269` asserts that the portal's `dataset-list` still
answers under `/datasets/`, which stays true.

---

## R4 — The shared deletion page has no slot for a warning

**Question**: FR-046 needs a prominent warning that names what a deletion would destroy, while
leaving the deletion available. What does the shared page support?

**Answer**: refusal, yes. Warning, no.

`mvp/templates/delete_view.html` reads `is_protected`/`protected_objects` and, when set, renders an
error alert **and suppresses the submit button** (`{% if not is_protected %}` guards the actions
block). That is a refusal, which FR-048 says a dataset must not have.

The one `variant="warning"` alert in the template is hardcoded generic copy with no variable in it.
There is a `related_objects` channel, but it is a fixed `(label, objects, overflow)` shape rendered
as an informational list of object names — not counts — and `MVPDeleteView.get_context_data`
force-empties it whenever the record is protected. There is no `warnings` variable and no
`{% block warning %}`.

**Route taken**: `mvp.views.base.BaseTemplateNameMixin.get_template_names()` puts Django's own
`<app>/<model>_confirm_delete.html` **ahead** of the shared `delete_view.html`. So a template at
`fairdm/core/dataset/templates/dataset/dataset_confirm_delete.html` that extends the shared page and
overrides `{% block before_form %}` with `{{ block.super }}` plus the dataset's own warning gets a
real, prominent, non-blocking warning without touching the shared package or restating any of its
markup. That is the supported extension point, and it is what the plan uses.

**Raised upstream rather than worked around**: the shared page should offer a `warnings` list and a
block around it, so this is configuration rather than a template per model. Filed against django-mvp
rather than solved here.

---

## R5 — The confirmation input is drawn twice, and the one that posts is empty

**Question**: does `require_confirmation = True` work in a browser?

**Answer**: no, on the version this project runs. Verified by reading the installed package rather
than the source checkout, which has diverged.

`pyproject.toml:88` pins `django-mvp >=0.19.1,<0.20.0` and the environment resolves 0.19.2.

- `delete_view.html:54` draws a confirmation field inside `{% block before_form %}`.
- `form_view.html:11-12` places that block **outside** the `<form>` element, which
  `cotton/form/index.html:3` does not open until afterwards.
- `cotton/form/index.html:9` then renders the bound form, which is `DeleteConfirmForm`
  (`mvp/forms.py:5`), drawing a **second** field with the same name and the same automatic id.
- The enabling script at `delete_view.html:92` reads `getElementById('id_confirmation')`, which
  returns the first in document order — the one outside the form.

So a person types into the field the script is watching, the Delete button enables, and the browser
posts the other, empty field. `clean_confirmation` then reports that the value does not match.

The project's deletion page, merged in #274, has this today. It is invisible to the test suite
because a test posts `confirmation=<name>` directly and never renders the page as a browser does.

**Consequence for this feature**: FR-045 cannot be satisfied through a browser until the shared
package is fixed. The fix already exists in the django-mvp working tree, which deletes the duplicate
field with a comment describing this exact fault — it is unreleased. **Raised upstream and pinned
forward, not worked around here**: forking the shared markup to drop one of the two fields would
hide the defect on one page while it stays live everywhere else.

The behavioural test for FR-045 will be written against the posted form, as the existing ones are,
and a separate test asserts the rendered page carries exactly one field named `confirmation` — which
fails today, and is the check that tells us when the upstream fix has landed.

---

## R6 — The dataset form nests a form element inside another

**Question**: why does the dataset's update page render unlike the project's?

**Answer**: every FairDM form is given a crispy helper automatically —
`fairdm/forms/base.py:135` assigns `self.helper = self._helper()` for all of them — and
`cotton/form/render.html` takes the `{% crispy form %}` branch whenever a helper is present. That
branch emits its own `<form>` element unless the helper says otherwise, and the page has already
opened one.

`ProjectForm` (`fairdm/core/project/forms.py:72`), `SampleForm` (`fairdm/core/sample/forms.py:118`)
and `MeasurementForm` (`fairdm/core/measurement/forms.py:105`) all set `form_tag = False`.
`DatasetForm` sets nothing — it is the only core form that does not. A grep for `form_tag` across
`fairdm/` returns exactly those three plus one deliberate `True` in `import_export`.

**Route taken**: `helper_attrs = {"form_tag": False}` on `DatasetForm.Meta`, which
`FairDMFormMixin._helper` applies (`fairdm/forms/base.py:142-144`). This keeps the automatically
derived layout, the form id and the interaction attributes, where the project's approach of
replacing the helper wholesale in `__init__` discards all three.

---

## R7 — Visibility as a visible choice

**Question**: FR-013 wants visibility presented as a choice between its options, pre-selecting
public, not a hidden default.

**Answer**: `ProjectForm` declares the field explicitly with `RadioSelect` and `initial =
Visibility.PUBLIC` (`fairdm/core/project/forms.py:45-52`) and wraps it in crispy's `InlineRadios` in
its layout. The model's own default is private (`fairdm/core/dataset/models.py:238-244`, the same
arrangement `Project` has), and both defaults are correct for their own reason — recorded as an
architecture decision in 013 and unchanged here.

**For a dataset**: declare `visibility` the same way and put it in the layout. Because R6 keeps the
automatically derived layout rather than hand-writing one, the inline-radio presentation needs
either a `fieldsets` declaration or a small layout override. Settled in the plan.

---

## R8 — The dates row set already has a dataset variant

**Question**: how much of the related-record machinery has to be built?

**Answer**: none of it. `fairdm/core/related_records.py` already declares `DatasetDateInline` and
`DatasetIdentifierInline` alongside the project's, and its module docstring says outright that it is
declarations only, for later stories to register. `fairdm/core/formsets.py`'s `date_ordering_formset`
is parameterised on the start and end type rather than on literals, and the comment at
`fairdm/core/project/plugins.py:86-91` says why: a dataset's dates pair the same base with its own,
differently-typed pair.

`DatasetDate` carries `START_TYPE = "CollectionStart"` and `END_TYPE = "CollectionEnd"`
(`fairdm/core/dataset/models.py:396-397`) and already validates the ordering at the model level
(`clean()`, `:404-440`) through the shared precision-aware comparison in `fairdm.core.dates`.

So the dataset's dates row set is one subclass attaching one formset, exactly like
`ProjectDatesInline`.

---

## R9 — The descriptions form needs no change

**Question**: does the vocabulary-driven descriptions form serve a dataset?

**Answer**: yes, unmodified. `fairdm/core/descriptions.py`'s `VocabularyDescriptionsForm` takes
`related_model` and `instance` as keyword arguments and reads its whole field set from
`related_model.VOCABULARY`. `DatasetDescription.VOCABULARY` is
`FairDMDescriptions.from_collection("Dataset")` (`fairdm/core/dataset/models.py:349`).

The generic `DescriptionsPlugin` the dataset uses today
(`fairdm/contrib/generic/plugins.py:26`) is a different thing — an add-and-remove row editor built on
`django-extra-views` — and is neither used nor repaired here. FR-042 replaces it for datasets.

---

## R10 — What is wrong with the listing's filters

Three separate faults in `fairdm/core/dataset/filters.py`, all on the page this feature owns.

1. **`date_type` raises whenever it is applied.** It is declared
   `field_name="dates__date_type"` (`:160-166`). `date_type` is a Python property on `DatasetDate`,
   not a column; the column is `type`. The sibling `description_type` filter uses the correct path
   (`:152`) and works. The only test touching it asserts the field appears on the form
   (`tests/test_core/test_dataset/test_filters.py:463`), which never runs a query, and the
   behavioural test is skipped at `:298`. This is #186.
2. **`visibility` cannot change the result set.** It offers a choice between private and public
   (`:144-150`) on a listing that shows public datasets only, so one choice is a no-op and the other
   returns nothing.
3. **`project` offers every project in the portal**, private ones included, to anyone who opens the
   page. `__init__` (`:174-191`) branches on whether the user is authenticated and then sets
   `Project.objects.all()` in both arms, with a comment saying views should handle permission
   filtering. No view does.

The module and class docstrings also describe a visibility level called INTERNAL (`:9`, `:93`) that
`Visibility` has never had.

---

## R11 — Counting what a deletion destroys

`Dataset.has_data` (`fairdm/core/dataset/models.py:326-332`) already answers whether any samples or
measurements exist, in a single query, via `self.samples` and `self.measurements`. FR-046 needs the
two counts separately rather than the boolean, which is two aggregate queries on the same relations.

`Dataset.project` is `on_delete=CASCADE` in the other direction
(`fairdm/core/dataset/models.py:272-280`), and samples and measurements hang beneath the dataset, so
a deletion genuinely takes them. Descriptions, dates and identifiers are `CASCADE` on their own
`related` foreign keys (`:350`, `:394`, `:469`).

---

## R12 — What the keywords registration is holding up

`Keywords` (`fairdm/core/dataset/plugins.py:44-59`) is the only registration of
`KeywordsPlugin` anywhere in the framework — no other record type has one, and 013 deferred keywords
for projects rather than building them. Removing it leaves `KeywordsPlugin`
(`fairdm/contrib/generic/plugins.py:16`) and `KeywordForm`
(`fairdm/contrib/generic/forms.py:133`) registered by nothing.

Deleting unused framework surface is a different kind of change with a different risk, so it is
raised (#298) rather than folded in. This feature removes the registration and leaves the base
classes where they are.

---

## Sources read

Installed shared package (authoritative for what runs, and divergent from the working checkout):
`mvp/templates/delete_view.html`, `form_view.html`, `cotton/form/index.html`,
`cotton/form/render.html`, `cotton/form/formset/index.html`, `cotton/form/formset/row.html`,
`mvp/views/edit.py`, `mvp/views/inline.py`, `mvp/views/base.py`, `mvp/forms.py`.

This project: `fairdm/core/dataset/{models,views,forms,filters,plugins,urls}.py`,
`fairdm/core/project/{models,views,forms,plugins,urls}.py`, `fairdm/core/related_records.py`,
`fairdm/core/descriptions.py`, `fairdm/core/abstract.py`, `fairdm/forms/base.py`,
`fairdm/contrib/generic/plugins.py`, `fairdm/views/base.py`, `memory/constitution.md`,
`specs/013-project-crud-views/{spec,decisions,plan}.md`.
