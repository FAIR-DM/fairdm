# Changelog

All notable changes to the FairDM project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **A keywords page on projects, datasets, samples and measurements.** Each record type has the URL
  name `keywords`, at `<record address>/keywords/`, reached from the Manage menu after the
  descriptions entry. The Manage menu now offers all six pages in one order on every record type: edit
  details, descriptions, keywords, key dates, identifiers and delete. The readiness items for
  keywords on a project's and a dataset's page lead to it. See
  [Record editing pages](docs/portal-development/record-editing-pages.md).
- **A delete page on projects, datasets, samples and measurements.** Each record type has the URL
  name `delete`, at `<record address>/delete/`, reached from the last entry of the Manage menu. A
  sample and a measurement can be deleted through the portal for the first time. The page asks for
  the record's name, or a measurement's portal ID when it has no name, and says what goes with the
  record before anything is deleted. A record that cannot be deleted, such as a project with a
  public dataset or a sample with measurements, says what is in the way and offers no way to
  confirm. Measurements the viewer may not see are counted and not named. Afterwards a sample or a
  measurement leads to its dataset. `manage_menu` entries now carry a `destructive` flag. See
  [Record editing pages](docs/portal-development/record-editing-pages.md).
- **Key dates and identifiers pages on projects, datasets, samples and measurements.** Each record
  type has the URL names `key-dates` and `identifiers`, at `<record address>/key-dates/` and
  `<record address>/identifiers/`, reached from the Manage menu after the descriptions entry. A
  measurement's dates and identifiers can be edited for the first time. A date is kept as
  precisely as it was entered, and a project and a dataset still refuse an end that falls before
  the start. New row sets `SampleDateInline`, `SampleIdentifierInline`, `MeasurementDateInline`
  and `MeasurementIdentifierInline` are in `fairdm.core.related_records`. See
  [Record editing pages](docs/portal-development/record-editing-pages.md).

### Removed

- **The project's Manage menu no longer has a contributors entry.** The Contributors tab is where
  a project's contributors are managed, as on a dataset.
- **The sample keywords page is replaced by the shared one.** The sample `Keywords` plugin,
  `KeywordsPlugin` (the module `fairdm.contrib.generic.plugins`) and the `urls` and `can_edit`
  entries of the sample overview context are gone, along with the Edit keywords item the sample
  template passed through the Manage menu. The address and URL name `sample:keywords` stay, and now
  serve the shared page. A portal that subclassed `KeywordsPlugin` for its own page builds on
  `FairDMUpdateView` and `Plugin`.
- **The project and dataset delete pages are replaced by the shared one.** The project `Delete` and
  dataset `Delete` plugins, the `overview-delete` URL names on both, `DeletePlugin`, the
  `show_delete_action` method, the `directory` and `crud_views` attributes and the
  `CRUDDirectoryMixin` base on both overview plugins, and the `urls.delete` entry of both overview
  contexts are gone, along with `visible_to_holder_of` in the project and dataset plugin modules.
  The address `<record address>/delete/` stays. A portal that reversed `overview-delete` reverses
  `delete` in the record's namespace instead, and a portal that subclassed `DeletePlugin` for its
  own page builds on `FairDMDeleteView` and `Plugin`.
- **A project's and a dataset's dates and identifiers are no longer rows on the details page.**
  They are edited on the key dates and identifiers pages. A portal that posted `dates-` or
  `identifiers-` fields to the `edit` page now posts them to `key-dates` or `identifiers`.
- **The sample's key dates page is replaced by the shared one.** `KeyDatesPlugin`, the sample
  `KeyDates` plugin and the `plugins/key-dates.html` template are gone. The sample's key dates
  address and URL name `sample:key-dates` stay, and now serve the shared page.
- **The project, dataset and sample editing pages are replaced by shared ones.** A project's
  `Update` and `Descriptions` pages, a dataset's, and a sample's `Edit` and `Descriptions` pages are
  gone, with the `overview-update` and `overview-descriptions` URL names on projects and datasets
  and the `/update/` address of both, the sample's `basic-information` page and its address, and
  `UpdatePlugin` and `DescriptionsPlugin` with the `plugins/descriptions.html` template. A project,
  a dataset, a sample and a measurement now have the URL names `edit` and `descriptions`, at
  `<record address>/edit/` and `<record address>/descriptions/`, reached from the Manage menu. The
  old addresses are not redirected. A portal that linked to one reverses `edit` or `descriptions`
  in the record's namespace instead, and a portal that subclassed `UpdatePlugin` for its own page
  builds on `FairDMUpdateView` and `Plugin`. See
  [Record editing pages](docs/portal-development/record-editing-pages.md).
- `SamplePermissionBackend` and `MeasurementPermissionBackend`, with their modules
  `fairdm.core.sample.permissions` and `fairdm.core.measurement.permissions`. They passed a
  dataset's stored permissions down to its samples and measurements. A level on a dataset now
  reaches them, through `RecordLevelBackend`. A portal that names either backend in its own
  `AUTHENTICATION_BACKENDS` removes it.
- The receiver that withdrew a person's stored permissions when their credit was deleted. The
  level is on the credit and goes with it.
- `give_level` in `demo/seed/common.py`. `grant_team_rights` lists the account at the manage level.
- `Contribution.set_default_affiliation`. A contribution made without an organization holds none
  and is no longer given the person's primary affiliation. The Contributors tab selects the primary
  affiliation to begin with, and `Contribution.add_to()`, `Contributor.add_to()` and
  `add_contributor()` leave the organization empty unless one is passed.
- `UserProfileForm`, which nothing used. `PersonProfileForm` is the form a person edits their own
  profile with.
- The Statistics and Network tabs of a contributor's page. Both were blank.
- The templates `person/plugins/overview.html` and `organization/plugins/overview.html`. A
  contributor's page is drawn from `contributors/overview/person.html` and
  `contributors/overview/organization.html` now, so a portal that extended either old file extends
  one of those.
- The `overview/includes/pending_action.html` include is replaced by the `c-actions.pending`
  component, which no longer shows a "Coming soon" badge on the button. A portal template that
  includes the old file uses `<c-actions.pending label="..." reason="..." />` instead.
- **The two dependencies licensed under the GPL are gone**, so a portal built on FairDM is
  not obliged to adopt that licence. Markdown editing moves from martor to django-markdownx,
  and the signup gate django-invitations provided is now FairDM's own setting. Portals that
  customised either need a small change — the settings and template changes involved, and
  the one piece of markdown syntax that renders differently afterwards, are covered in
  [Rich text and markdown](docs/portal-development/rich-text.md).
- **The `groups` fixture and its three empty, ungoverned groups are gone**, replaced by the four
  portal roles described below. A portal already using the three previous groups keeps every
  member: they are renamed in place, not deleted, the next time the database is brought up to
  date.
- **The `c-cards.statistic` component is gone.** Use `c-stats` with `c-stats.item` for a row of
  figures. A portal template that includes `c-cards.statistic` needs the same change.
- **`MeasurementDetailView` and the `measurement/detail.html` template are gone.** The measurement
  page is now the overview plugin's, drawn by `measurement/measurement_overview.html` and its
  `overview.*` blocks. A portal that subclassed the view or extended the template overrides the
  matching block or plugin method instead, as described in
  [Overview pages](docs/portal-development/overview-pages.md).

### Fixed

- **The browser tab shows the FairDM icon in dark mode.** FairDM shipped `brand/icon.svg` and no
  `brand/icon_dark.svg`, so a browser set to a dark colour scheme was given django-mvp's own dark
  icon. FairDM now ships both. A portal that replaces `brand/icon.svg` with its own icon should
  replace `brand/icon_dark.svg` as well.
- **The description and date filters of the sample lists answer instead of failing.** On the
  portal's sample pages and in the API, filtering by description, "date after" or "date before"
  raised a server error, because the filters read fields the sample models do not have. They now
  read the description text and the key dates.

- **`PersonFactory` builds a new person on every call.** Its email was made from the random first
  and last name, and the factory returns the existing person when the email is already in use, so
  two calls that drew the same name gave back one person. Tests that then affiliated "both" people
  with one organization failed now and then on the unique person and organization rule. The email
  is now a sequence, `person<n>@fakeuser.org`. Passing an `email` that is already in use still
  returns that person.

- **The keywords form builds for every record type.** `KeywordForm` read a setting named after the
  concrete model, such as `FAIRDM_ROCKSAMPLE`, which does not exist, so it raised for every sample
  type. It now offers the free keywords field alone on every record type and reads no keyword
  vocabulary from settings. It shows a record's free keywords as chosen, saves them, and leaves the
  record's vocabulary keywords as they are. It no longer rebinds its own class to the model of the
  last record it was built for.
- **Signing in works in development without Redis.** With `DJANGO_ENV=development` and no
  `REDIS_URL`, every sign-in returned "429 Too Many Requests", because the rate limiter could not
  reach its cache. The development settings now hold every cache in memory when `REDIS_URL` is
  unset. They also run Celery tasks in-process in that case, which the settings had always
  claimed to do and never did. Other environments are unchanged.
- A portal's profile form that leaves the languages field out of `Meta.fields`, as the contributors
  guide says it may, raised `KeyError` when it was built. An organization form without the website
  field also hid the first stored link from the links field, so saving it dropped that link. Both
  forms now work without those fields.
- An organization created from ROR could not be saved from its editing page or in the
  administration interface, because `Organization.clean()` accepted only the bare ROR identifier
  and the identifier is stored as the full address. It now accepts both, and still refuses a
  malformed one.
- Saving a profile whose stored record fails validation on a field the form does not carry, such
  as a malformed identifier, answered with a server error. The form is now invalid, the problem is
  reported on the form as a whole and nothing is saved.
- Saving a profile returned to a page that failed with an unknown icon error while its "saved"
  message was waiting, because `MESSAGE_TAGS` still held the old Bootstrap tag names. The setting
  is removed, so Django's own message tags reach the alert. A portal that styles messages by the
  old tag strings needs to set `MESSAGE_TAGS` itself.
- `Contributor.get_update_url()` raised `NoReverseMatch` because it reversed a name no URL carried.
  It returns the address of the profile editing page.
- A person's own page now counts a primary affiliation toward their checklist only when it is
  verified and has not ended, as the header does, and `Person.get_location_display()` follows the
  same rule instead of naming the organization of a pending or ended primary affiliation.
- The Projects and Datasets figures on a contributor's overview, and its "View all" links, did
  not link to the matching tab.
- `reverse("account-center")` is `/account-center/` again after the update to django-mvp 0.25.
- **The contributor components did not render** (#349). `c-contributor.names` raised
  `TemplateDoesNotExist` on every use, and `c-contributor.avatar` drew Bootstrap markup the
  stylesheet does not define, with the text "None" in place of initials.

- **A measurement with no value recorded was shown as "None".** Wherever it was printed,
  including its breadcrumbs and lists of measurements, a measurement whose type declares a
  value but has none recorded read "None". It is now shown by its name, or by its portal ID
  when it has no name either.

- **Migrating any database other than `default` failed.** Ten data migrations queried
  through the ORM without saying which database they were being applied to, so they read
  and wrote `default` instead. A portal that migrates a second database — to check its
  migrations, to build a fresh copy, or to run a second tenant — got either an error about
  a column that exists in one of them and not the other, or a silent write to the wrong
  place. Each of those migrations now routes to the database it is given, and the test
  suite fails if a new one does not.
- **The ICP-MS example's admin form was missing every field the measurement itself
  carries** — its name, sample, dataset and image, along with the value it records. A
  measurement admin that lists its own fieldsets replaces the standard ones rather than
  adding to them, which the three demo measurement admins did not account for.
- **Deleting a project or dataset that has a person credited on it raised an error.** The
  record's credits are removed alongside it, and withdrawing that person's rights over the
  record was attempted after the record itself had gone. Every project and dataset created
  through the portal credits its creator, so this affected the ordinary delete path.
- **Crediting the same contributor twice through `add_contributor()` raised a database
  error** instead of adding the new roles to the credit already recorded. It now behaves
  like the other two ways of recording a credit, all three of which accumulate roles.
- **A deactivated account kept its management rights over an organisation.** The right is
  worked out from the person's affiliation each time it is checked, and that check did not
  consider whether the account was still active.
- Error messages naming an invalid URL, ORCID or ROR value could not be translated, because
  the value was substituted into the message before translation could look it up.
- **`ProjectFactory`, `DatasetFactory`, `PersonFactory` and `OrganizationFactory` no longer
  write a real image file on every instantiation.** Every portal that installs FairDM uses
  these factories in its own test suite, and none of them had asked for an image — so if
  your project's test suite creates projects, datasets, people or organisations, it has
  probably been filling its own `MEDIA_ROOT` with a new JPEG and a new directory per object,
  every test run, forever. Nothing removed them. A test that genuinely needs one now asks
  for it: `ProjectFactory(with_image=True)` produces exactly the placeholder the factory
  used to generate on its own, and `image=<file>` still takes a specific one.

### Changed

- **The REST API is complete, and a portal with API clients or serializers of its own has changes
  to make.** See [The REST API](docs/portal-development/restful-api.md) and
  [Limits on the API](docs/portal-administration/api-limits.md). What to change:
  - **Records refer to each other by short identifier, and no response carries a database number.**
    The `id` field is gone from every record. `project`, `dataset` and `sample` are
    `{"uuid", "url"}` objects, or `null` when the caller may not see the record, where they were
    numbers. A request names a parent by its short identifier, as a bare string or as that object,
    and a database number is refused. A serializer of your own declares each relation it adds as a
    `fairdm.api.serializers.RecordReferenceField` or a `StringRelatedField`.
  - **A relation filter matches on the short identifier.** `?dataset=`, `?sample=` and a type's
    filters on a project or a contributor take the related record's short identifier and refuse a
    database number. A filter on a relation whose model has no short identifier, such as a content
    type, is not offered. Every sample list takes `?dataset=` and every measurement list also takes
    `?sample=`.
  - **Every sample and measurement carries the common fields**, whatever its registration lists:
    `url`, `html_url`, `uuid`, `name`, `dataset`, `added` and `modified`, and `local_id` and
    `status` for a sample and `sample` for a measurement, then the metadata (`descriptions`,
    `dates`, `identifiers`, `keywords`, `contributors`). The fields a type declares come after
    them, and a measurement's measured values are included.
  - **Tokens come from the account pages, and the password login is gone.** A person creates a
    token at `/account/tokens/`, shown once and revocable, and a script sends it as
    `Authorization: Token <token>`. The addresses under `/api/v1/auth/`, which exchanged a
    password for a token and managed accounts, no longer exist, and `dj-rest-auth` and
    `djangorestframework-guardian` are no longer dependencies. The tokens are kept by
    django-rest-knox, which FairDM installs and configures through `REST_KNOX`. Existing Django
    REST framework tokens stop working, so scripts need new ones. A portal that listed
    `dj_rest_auth` or `rest_framework.authtoken` in its settings removes them.
  - **A serializer of your own builds on the base, and a registration is checked at start-up.** A
    serializer for a sample type must subclass `BaseSampleSerializer` and one for a measurement
    type `BaseMeasurementSerializer`, however it is supplied (`serializer_class` or an overridden
    `get_serializer_class`). Otherwise the portal refuses to load its API routes with
    `ImproperlyConfigured`. The check `fairdm.E600` reports at start-up, and in
    `manage.py check`, a registration whose API fields leave out a field the model requires.
  - **The two lists of registered types are removed.** `GET /api/v1/samples/` and
    `GET /api/v1/measurements/` answer `404`. `/api/v1/` links to every list, a list reports how
    many records the caller may see in `count`, and the generated API documentation describes each
    type.
  - **Every list takes `modified_after` and `modified_before`.** Each is an ISO 8601 date or
    date-time, compared with the record's `modified` time, so a harvester can ask for what changed
    since it last read. A value that cannot be read is answered `400`, naming the parameter, and
    both appear in the generated API documentation. They are added to every list by
    `FairDMFilterBackend`, which now stands in `REST_FRAMEWORK["DEFAULT_FILTER_BACKENDS"]` in place
    of django-filter's own backend.
  - **The API documentation describes each registered type.** On the documentation page the operations
    of every sample type are under `Samples` and those of every measurement type under
    `Measurements`, and each operation is titled with the type's plural name and what it does.
    A type's list operation carries the description from its registration, with the authority,
    the citation, the keywords and a link to the repository. A maintainer's name and email address
    are left out. Projects, datasets and contributors keep a heading each. The description of each type's record, and its
    `Patched` variant, is the type's own and its `title` is the type's `verbose_name`, where it
    was the base serializer's docstring. The schema gains a top-level `tags` list. The headings
    are built by `fairdm.api.schema.describe_api`, so a portal that replaces
    `SPECTACULAR_SETTINGS["POSTPROCESSING_HOOKS"]` keeps that hook in it.
  - **`FAIRDM_API_DOCS_URL` is removed.** Nothing read it. The API documentation is at
    `/api/v1/docs/`, and the sidebar has a single API entry that leads to it.
  - **New limits and page sizes, each a setting.** The rates `anon` and `user` (100 and 1,000
    requests an hour) are replaced by four in `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`:
    `anon_burst` (30/minute), `anon_day` (2000/day), `user_burst` (120/minute) and `user_day`
    (20000/day). A portal that set the old names changes them to the new ones, or the API fails
    with a missing-rate error. A page holds 100 records instead of 25 (`REST_FRAMEWORK["PAGE_SIZE"]`)
    and a caller may ask for up to 1,000 instead of 100 (the new `FAIRDM_API_MAX_PAGE_SIZE`). A
    refused caller receives `429` with a `Retry-After` header. Behind a proxy, set
    `REST_FRAMEWORK["NUM_PROXIES"]`, since the limits count per address only once it is set;
    `manage.py check --deploy` warns (`fairdm.W601`) until it is.
  - **The samples and measurements of a dataset that is public but not published are not public
    through the API**, as on the portal's pages. They are listed, counted and returned only to a
    person with a level on them. The dataset's own record stays readable.
  - **Any origin may call the API.** `CORS_ALLOW_ALL_ORIGINS` is now `True` for the addresses under
    `/api/`, to read and, with a token, to write. A portal's sign-in cookie is never accepted from
    another site. A portal that wants the old behaviour sets `CORS_ALLOW_ALL_ORIGINS = False` and
    lists its sites in `CORS_ALLOWED_ORIGINS`.

- **django-mvp moves to 0.28 and django-mvp-accounts to 0.2.** django-mvp now takes its basic
  components from daisy-cotton and puts the ones it keeps under an `mvp.` prefix. FairDM's own
  settings install `daisy_cotton`, so a portal that writes no templates of its own has nothing
  to do. A portal with its own templates checks them against django-mvp's upgrade notes for
  [0.27.0](https://github.com/django-mvp/django-mvp/releases/tag/v0.27.0) and
  [0.28.0](https://github.com/django-mvp/django-mvp/releases/tag/v0.28.0). The changes FairDM's
  own templates needed were these:
  - `<c-card>`, `<c-card.wrapper>`, `<c-avatar>`, `<c-dropdown>`, `<c-grid>`, `<c-group>`,
    `<c-text>`, `<c-data-field>`, `<c-form.formset>`, `<c-placeholder.card>`, `<c-section.hero>`
    and `<c-addons.share-dropdown>` are written with the prefix: `<c-mvp.card>`,
    `<c-mvp.avatar>` and so on. An unprefixed `<c-card>`, `<c-avatar>` or `<c-dropdown>` raises
    no error. It draws daisy-cotton's component of that name, which takes different attributes.
    FairDM's own components, such as `<c-card.details>` and `<c-contributor.avatar>`, keep their
    names.
  - `<c-menu.item>` takes `text` where it took `label`. This includes an entry a record's
    template adds to `<c-actions.manage>`.
  - `<c-menu.group label="…">` is a `<c-menu.title text="…" />` followed by its entries, and
    `<c-menu.divider />` is an empty `<li></li>`.
  - `<c-menu>` no longer fills its parent. Pass `class="w-full"` where it should.
  - `<c-avatar.group>` has no `size`. The overlap is a class, `-space-x-4` for what `sm` gave.
  - The `app.header.widgets` block of `base.html` is `app.navbar.end`.
  - `MVP_CONFIG["layout"]["navbar"]` has one widget list, `end`. `desktop.end` and `mobile.end`
    are no longer read.
  - On a table page the add button is in the `page.controls` block. `page.actions` is an empty
    block at the end of the toolbar.
- A listing with no records and no search or filter applied has no toolbar, so no search box. A
  search or filter that matches nothing gets a message of its own and a link that clears it.
- **A record names its people before its organizations.** Its overview and its citation take the
  people in the order set on the Contributors tab, then the organizations in theirs, so reordering
  a list reorders the citation. Which contributors are named, and how, is as before.
  `RecordOverviewPlugin.get_credits()` no longer falls back to a person's primary affiliation: a
  person credited with no organization is shown with none.
- **`Crediting.move(contribution, direction)` reorders a record's contributors**, `"up"` or
  `"down"` among its own kind, under the same row lock as the other changes. The Contributors tab's
  move page calls it. `Contribution.objects.people()` and `.organizations()` narrow contributions by
  kind, each in order.
- **Permissions stored in django-guardian for a project, dataset, sample or measurement grant
  nothing.** Bringing a portal up to date converts them once. Each permission of a person, and of
  each current member of a group, is mapped to a level (view, add or change, and delete or manage
  map to view, edit and manage) and the person is listed on the record at the highest level their
  permissions map to, under the record's own type. Contributors with no permissions are given the
  view level, an organization already stored with a person's entry is kept and listed on the
  record, and the converted permissions are deleted. Permissions stored for organizations and for
  models a portal defines are untouched. The conversion does not reverse.
- **Creating a project or dataset, or a sample or measurement through the API, lists the creator
  at the manage level** and stores no permission. A superuser who creates one is not listed.
- **Deleting a sample or a measurement now needs the manage level** on it, on its dataset or on its
  project. The right to change a dataset used to be enough for a sample.
- On the update forms of a project, dataset, sample and measurement, visibility and the record it
  sits under (a project's owner, a dataset's project, a sample's or measurement's dataset) are
  offered only to someone who can manage the record. For anyone else they are left out of the
  form, so a request cannot change them. The API applies the same rule to a `PUT` or `PATCH`,
  answering 403, refuses a move that would leave the record with nobody to manage it with a 400,
  and accepts as a `project`, `dataset` or `sample` only a record the requester holds the edit
  level on, so a record is created only inside a parent they can edit. The project choices on the
  dataset create and update forms are limited the same way.
- The dataset choices on the sample and measurement forms and the measurement filter, the project
  choices on the dataset filter, and the count of other datasets in a project on a dataset's page
  read levels in place of stored permissions.

- Deleting an organization no longer fails while a contribution names it as the organization a
  person is credited from. `Contribution.affiliation` is set to none, and the person stays on the
  record. The migration changes the column's `on_delete` and no data.
- `c-contributor.item` and `c-contributor.card.person` show the organization named on a
  contribution they are given, or none when it names none. They no longer fall back to the
  person's primary affiliation for a contribution. Given a person, they show it as before.
- A contributor's Projects and Datasets tabs, and the figures and cards on their overview, list
  only public projects and public datasets, and a public dataset inside a private project is left
  out. This holds for every viewer, including the contributor and the members of a private
  project.
- **The contributor components were rebuilt on django-mvp and DaisyUI, and some attributes
  changed.** `c-contributor.names` no longer takes `role` or `separator`, `c-contributor.name` and
  the person and organization cards take the contributor as an attribute rather than reading it
  from the context, and `c-contributor.avatar` takes a size token rather than pixels. The
  components are described in [Contributors](docs/portal-development/component_library/contributors.md).

- **The project is built and developed with uv instead of Poetry.** Contributors run
  `uv sync` to install and `uv run` in place of `poetry run`. The lockfile is now `uv.lock`,
  and the published package is built with hatchling.
- **Django 5.1 is no longer supported.** It reached end of life, and the development toolchain
  now requires Django 5.2 or later. The Django requirement is `>=5.2,<6.0`.
- **The demo application moved from `fairdm_demo/` to `demo/`** and is imported as `demo`. Its
  Django app label changed with it, which moves the database tables it owns. Nothing about how it
  behaves changed. Portals that install it, import from it, or name its models by label need a
  small change — the steps are in
  [Migration guides](docs/more/migration-guides.md#the-demo-application-moved-to-demo).
- Withdrawing a contributor's rights when their credit is deleted now happens in one place
  rather than two. The behaviour is unchanged for every path that already worked.
- **A model-level permission held through one of the four portal roles below now applies to
  every instance of that model**, not only the record it was granted for. A permission granted
  any other way — directly to a person, or through a group the portal made up itself — is
  unchanged from before. See [Portal roles](docs/portal-administration/roles.md).
- **The `has_permission` template tag no longer treats membership in a group named directly
  in a template as authorization on its own.** It now asks Django's ordinary permission check
  for each permission string passed to it, so a template using the bare codename spelling its
  `user_permissions` context convention expects (for example `change_dataset`) no longer
  matches for anyone — use the app-labelled form (`dataset.change_dataset`) instead.
- **django-mvp moves to 0.23 and django-accounts-center to 0.8.** django-mvp took over the
  Account Center that django-accounts-center used to provide, and django-accounts-center
  dropped its own copy in the same release cycle, so the two versions move together. A portal
  with a view of its own still setting the pre-0.16 `has_<action>_permission` attributes
  renames them to `show_<action>_action` — django-mvp now raises `ImproperlyConfigured` rather
  than reading them. A portal setting `MVP_CONFIG["layout"]["sidebar"]["footer"]` drops the
  key — the sidebar footer is now a fixed composition that already draws a superset of what
  that list configured, and django-mvp only warns and discards the setting. A portal including
  `dac.urls` for its Account Center route mounts `mvp.urls` at the same prefix, immediately
  above it, since the landing page and its `account-center` URL name now come from django-mvp.
- The development settings accept any host name, so a development server answers under the
  machine's network name as well as `localhost`. Production is unchanged: its allowed hosts
  still come from `DJANGO_SITE_DOMAIN` and `DJANGO_ALLOWED_HOSTS`, and a wildcard there still
  fails the configuration checks.
- **django-mvp moves to 0.26, and django-mvp-accounts replaces django-accounts-center.**
  Forms are now drawn by django-mvp-forms as daisyUI components, and the sign-in, sign-up and
  account management pages come from django-mvp-accounts. FairDM's own settings carry all of
  it, so a portal that changes none of the following has nothing to do:
  - A portal that lists `crispy_tailwind`, `dac` or `dac.allauth` in its own `INSTALLED_APPS`
    removes them. `mvp_forms` and `mvp_accounts` are already installed by FairDM.
  - A portal that sets `CRISPY_TEMPLATE_PACK` or `CRISPY_ALLOWED_TEMPLATE_PACKS` to `tailwind`
    sets `daisyui`, or drops the setting.
  - A portal template that loads `tailwind_filters`, or overrides a template under `tailwind/`,
    drops the load and moves the override to the matching template under `daisyui/`.
  - A portal that includes `dac.urls` includes `allauth.urls` instead. The addresses under
    `account-center/` are unchanged.
  - A portal that lists `dac.icons.DAC_ICONS` in `EASY_ICONS` removes it, and one that overrides
    a `cotton/dac/` component removes the override, since nothing draws it any more.
  - The `ACCOUNT_MANAGEMENT_GET_AVATAR_URL` setting is gone. Nothing read it.
  - A portal that builds its own stylesheet runs `python manage.py mvp_tailwind` again.
- **django-mvp moves to 0.24, and FairDM now requires django-mvp-charts and pyecharts.** The
  overview pages draw their charts with them, so a portal installing FairDM gets both, and adds
  `mvp_charts` to `INSTALLED_APPS` if it does not build its apps from FairDM's own list.
- **Breadcrumbs show the full name of each page** instead of a shortened one.

### Added

- **A measurement can be edited through the portal.** Its overview page gains a Manage menu, and the
  edit details and descriptions pages open at `/measurement/<uuid>/edit/` and `/descriptions/`.
  Every registered sample and measurement type receives both pages with no work by the portal
  developer.
- `RecordEditingPage`, the class the shared editing pages inherit, which decides who may open a
  page on every request. A visitor is sent to sign in, a signed-in person who may see the record and
  may not use the page gets a 403, and someone who may not see the record gets a 404. A private
  project's or dataset's edit page used to answer 404 to a signed-in person who could open the
  project.
- `<c-actions.manage>` and the `overview.manage` block, which draw the Manage menu on all four
  overview pages. A record's template adds its own entries through the component's slot.
- **Access to a project, dataset, sample or measurement is a level on a person's contribution**:
  view, edit or manage, each including the one before it. `RecordLevelBackend`
  (`fairdm.contrib.contributors.permissions`) answers every permission question about these
  records from the levels, reading up through the dataset and the project, so a level on a dataset
  reaches its samples and measurements and a level on a project reaches its datasets. Every
  permission the four models declare is mapped to a level, and a permission the table does not
  know is refused. `with_level(user, level)` on the four querysets lists the records a user holds
  at least a level on, and `accessible_to(user, level)` adds every record for someone a portal
  role gives the right to change datasets. `Crediting.update` takes a `level`, refusing one
  below what the person holds from above with the code `below_inherited`, and
  `Crediting.make_creator` lists whoever made a record at the manage level.
- The Contributors tab, and every page of it, opens exactly when the record's overview does, and
  shows what each person may do to people who can manage the record only.
- **A record always keeps someone who can manage it.** `Crediting.update` and `Crediting.remove`
  refuse, with the code `last_manager`, a change that would leave a project, dataset, sample or
  measurement with nobody who can sign in and holds the manage level on it or on the record above,
  whoever asks. The edit page shows the refusal beside the level, and the page for removing a
  contributor offers no way to go ahead. `Crediting.would_leave_no_manager` answers the question
  without changing anything. A dataset, sample or measurement cannot be moved to a project or
  dataset that would leave it without a manager: `clean` refuses it with the code `no_manager`.
  Every change to a record's contributors first locks the record's row, so two changes to one
  record cannot overlap. Merging two profiles that are listed on the same record keeps the higher
  level, and no stored permission row is copied for these four kinds of record. See
  [Crediting a record](docs/user-guide/crediting-a-record.md).
- A person credited with `Contribution.add_to()`, `Contributor.add_to()` or `add_contributor()`
  for the first time starts at the view level.
- `ManagerOnlyFieldsMixin` in `fairdm.core.forms`, and `CreatorCreditMixin` in
  `fairdm.api.serializers`.
- A data migration, `contributors.0023_levels_from_stored_permissions`, which turns the permissions
  stored for projects, datasets, samples and measurements into levels. See Changed.

- The pages for adding a person and adding an organization to a record offer three ways side by
  side: someone already in the portal, someone looked up in ORCID or ROR, and someone entered by
  hand. A registry match makes a profile with the name and the identifier, or uses the profile the
  portal already holds under that identifier. A person entered by hand needs both names, and no
  email address is asked for or kept. A name the portal already has is offered before anything is
  made. A registry that cannot be reached leaves the other two ways working.
  `Orcid` and `Ror` in `fairdm.contrib.contributors.services.registries` search, fetch and make
  the profiles, and raise `RegistryUnavailable`. The portal's server needs to reach
  `pub.orcid.org` and `api.ror.org`. See [Crediting a record](docs/user-guide/crediting-a-record.md)
  and [Looking up contributors in ORCID and ROR](docs/portal-administration/looking-up-contributors.md).
- The organization a person is credited from on a record is chosen when the person is added and on
  the edit page: one of their affiliations with the primary one selected, another organization by
  name, or none. It is kept with the record, listed among the record's organizations once, and
  does not follow the person's profile. An organization cannot be removed from a record while
  anyone on it is credited from it, and the refusal names them. `Crediting.add()` and
  `Crediting.update()` take an `organization`, `Crediting.credited_from()` reports who is credited
  from each organization, and `Crediting.remove()` raises `ValidationError` with code
  `credited_from`. See [Crediting a record](docs/user-guide/crediting-a-record.md).
- Projects, datasets, samples and measurements have a **Contributors** tab, including every sample
  and measurement type a portal registers. It lists a record's people and organizations separately,
  and people who manage the record add a person or an organization already in the portal, set a
  contributor's contribution roles and remove a contributor. A signed-in person who cannot manage
  the record is refused and a visitor is sent to sign in. The overview of every record leads its
  People card to the tab through `people_url`.
- `Contribution.level` stores what a person may do on a record: `ContributionLevel.VIEW`, `EDIT` or
  `MANAGE`. `RecordAccess(record)` in `fairdm.contrib.contributors.access` reads it for the record
  and the records above it, and `Crediting(record)` in
  `fairdm.contrib.contributors.services.crediting` is the one place a record's contributors change.
  The migration adds an empty column; existing contributions hold no level until a person is given
  one. `Person.can_sign_in()` is the rule that decides whether an account is in use, which
  `Person.is_editable_by()` now asks. See
  [The Contributors tab](docs/portal-development/contributors.md#the-contributors-tab) and
  [Crediting a record](docs/user-guide/crediting-a-record.md).
- **A Data Curator can step in on any record.** Holding the Data Curator role, a person opens any
  project, dataset, sample or measurement and manages its contributors without being listed on it,
  and is refused what anyone is refused: removing or lowering the last person who counts as able to
  manage it, and removing an organization people are credited from. The other roles gain nothing
  here, and no role holds a permission it did not hold before. See
  [Portal roles](docs/portal-administration/roles.md#stepping-in-on-a-record).
- `manage.py seed_contributors` loads every state of the Contributors tab, including a private
  dataset the seeded Data Curator account (`data.curator@fairdm.org`) is not listed on and whose
  only manager cannot sign in. `--keep-records` adds what a newer version needs to an earlier run's
  records without changing their addresses. `manage.py seed_profiles` credits each person it
  affiliates from their primary affiliation. See
  [Development accounts](docs/portal-development/development_accounts.md#accounts-for-the-contributors-tab).
- A person can edit their own profile. The edit action in the header of their page, the prompt to
  write a biography and the photo, biography and links items on their checklist now lead to a page
  for changing the photo, given and family name, display name, alternative names, biography, links and languages. While the
  account is active nobody else is offered it, and a request for it by anyone else is refused. A portal changes the fields by
  naming its own form in the new `FAIRDM_PROFILE_FORMS` setting. A portal that overrides
  `contributors/overview/person.html` keeps the disabled edit button, the disabled prompt and the
  unlinked checklist items until it adopts the new `can_edit` and `update_url` values. See
  [Editing a profile](docs/portal-development/contributors.md#editing-a-profile).
- An organization's owner and administrators can edit its profile. **Edit details** in the
  **Manage** menu, the description prompt and the logo, type, city and country, description and
  website items on its checklist now lead to a page for changing the logo, name, alternative names,
  type, the organization it is part of, city, country, description, website and other links. An
  ordinary member, a stranger and a Data Curator are not offered it, and a request for it by any of
  them is refused. A portal changes the fields through the `organization` entry of
  `FAIRDM_PROFILE_FORMS`. A portal that overrides `contributors/overview/organization.html` keeps
  the disabled **Edit details** entry, the disabled description prompt and the unlinked checklist
  items until it adopts the new `can_edit` and `update_url` values. See
  [Editing a profile](docs/portal-development/contributors.md#editing-a-profile).
- `Organization.get_descendant_ids()` returns every organization beneath one, at any depth. An
  organization can no longer be made part of itself or of one of its own sub-organizations, in the
  editing page or in the administration interface.
- A Community Manager can edit the profile of any organization and of any person who does not have
  an active account: one nobody has claimed, one whose owner has not yet signed in, and one whose
  account has been deactivated. A Community Manager who does not keep an organization is offered a
  single **Edit details** button and no checklist. A person with an active account stays the only
  one who can edit their profile, including an account that signed in without being marked claimed.
  An edit is not marked as the Community Manager's, and it does not claim the profile, activate the
  account or change an organization's members. The Data Curator and Developer roles give no right
  to edit a profile, and the permissions of every role are unchanged.
- `PortalRoles.is_held_by(user, role)` says whether a user is an active member of a role's group.
- `manage.py seed_profiles` creates `admin.user@example.com`, `member.user@example.com` and
  `former-admin.user@example.com` around the organization `regular.user@example.com` owns, and
  `community-manager.user@example.com` and `data-curator.user@example.com`, which hold those roles.
- `Contributor.is_editable_by(user)` says whether a user may edit a contributor's profile in the
  portal. `LinesField` is a form field for a list typed one entry per line.
- A person's page now tells a visitor who the person is, where they work, whether their ORCID iD
  is authenticated, which public projects and datasets they are credited on, the contribution
  roles they hold and who they work with most. The side column lists their identifiers, links and
  affiliations. An unclaimed profile and an inactive account each say so, and capabilities FairDM
  cannot offer yet, such as claiming a profile or contacting the person, are shown as not
  available. The blocks are described in
  [Overview pages](docs/portal-development/overview-pages.md#the-person-page), including the new
  `overview.name`.
- An organization's page now shows what it is, where it sits among the organizations around it,
  its current members with the people who run it marked, and the public projects it owns or is
  credited on and the public datasets inside the projects it owns. Its members' own credits are
  not counted as the organization's. The people who keep the record see a checklist, and a
  signed-in person who is not a member is shown asking to join as not available yet. The blocks
  are described in
  [Overview pages](docs/portal-development/overview-pages.md#the-organization-page).
- The Projects and Datasets tabs of an organization list the same records as its overview, so a
  figure on the page equals the number of entries behind its link.
- A person sees a checklist of what a complete profile has on their own page, with editing the
  profile offered as not available yet, and the owner and administrators of an organization see
  the checklist of its record and a menu of management actions. Nobody else sees either, whatever
  their portal role. Who sees what is described in
  [Overview pages](docs/portal-development/overview-pages.md#the-profile-checklist).
- The card `c-card.hierarchy`, and `Organization.get_current_memberships()`, `has_member()`,
  `is_managed_by()`, `get_hierarchy()`, `get_public_projects()` and `get_public_datasets()`, are
  documented in [Cards](docs/portal-development/component_library/cards.md#c-cardhierarchy) and
  [Contributors](docs/portal-development/contributors.md#organization-properties).
- The cards `c-card.records`, `c-card.roles`, `c-card.links` and `c-card.affiliations`, and the
  `c-missing` notice, are documented in
  [Cards](docs/portal-development/component_library/cards.md).
- `Contributor.get_public_projects()`, `get_public_datasets()`, `get_visible_contributions()`,
  `get_role_counts()`, `get_collaborators()` and `to_public_schema_org()`, and the helpers in
  `fairdm.contrib.contributors.profiles`, are documented in
  [Contributors](docs/portal-development/contributors.md#what-a-profile-may-show).
- `manage.py seed_profiles` loads a person and an organization in every state the pages answer for.
  It refuses to run outside development.
- Pillow is a declared dependency of FairDM.
- **Components for showing contributors.** `c-contributor.item`, `c-contributor.row` (a list
  row with an `actions` slot), `c-contributor.byline`, `c-contributor.stack`,
  `c-contributor.summary` and `c-contributor.affiliation` join the existing name, names, avatar and
  card components. Each takes a person, an organization or a contribution. They are described in
  [Contributors](docs/portal-development/component_library/contributors.md).
- **The person card shows the portal roles a person holds**, as a badge per role.
- **`Person.objects.for_cards()`** prefetches everything a person's card reads, so a page listing
  people costs the same number of queries however many it shows. The people listing and the team
  page use it. `Person.primary_organization`, `Person.portal_roles`, `Organization.summary` and
  `Contributor.is_organization` are new, and `get_initials()` now gives a person's given and family
  initials and an organization's leading acronym.
- **Avatars show contributors' photos and logos.** FairDM sets django-mvp's avatar resolver, so
  every `<c-avatar :for="...">`, including the signed-in user's in the menu, draws the
  contributor's image, or their initials when there is none.

- **Projects, datasets, samples and measurements open on one consistent overview page.** The
  four pages share one layout (header, notices, a strip of figures, then content beside a side
  column of shared cards) and one list of `overview.` template blocks, documented in
  [Overview pages](docs/portal-development/overview-pages.md). The project page lists its five
  most recently updated datasets, charts records by type and growth by month, shows the team a
  readiness checklist, and counts for a visitor only the datasets they may see. The cards are
  the `c-card.*` components, described in
  [Cards](docs/portal-development/component_library/cards.md), and a portal changes a page by
  overriding one block, or one method of `RecordOverviewPlugin`, which every overview plugin now
  subclasses. Dates on these pages follow the active language, and every string on them is
  translatable.
- **The dataset page answers a reuser's questions in the order they ask them.** It shows whether
  the data is published and under which licence, charts of its records by type and how they grew,
  a timeline card of its key dates, its citation and its related publications worded from the
  publication's side. A public dataset that is not published shows a visitor its description,
  counts and charts, and never a record. The team sees a "Ready to publish?" checklist of seven
  required and three recommended items until the dataset is published. See [Overview pages](docs/portal-development/overview-pages.md).
- **The sample page follows the specimen, and a sample type adds its own fields by providing one
  template.** It shows the type and status, a timeline joining each step's date, people and
  notes, the measurements made on the sample (including those another team recorded in its own
  dataset), a citation in DataCite's form for a physical object, a map and the related samples.
  A measurement or related sample in a dataset the viewer may not see is counted and never named or
  linked. A portal gives a sample type its page with `<app_label>/<model_name>_overview.html`, a
  subtype inherits its parent type's page, and the demo's rock sample is the worked example. `SampleQuerySet` and `MeasurementQuerySet` now get `published()`
  and `visible_to()` from `fairdm.core.managers.RecordVisibilityMixin`. See
  [Overview pages](docs/portal-development/overview-pages.md).
- **The measurement page shows the result and how it was obtained, and a measurement type adds its
  own fields by providing one template.** It shows the result with its uncertainty, a timeline of
  how the measurement was set up, made and taken down, the sample it was made on as a small version
  of the sample's own header, the other measurements on that sample, a citation that suggests the
  dataset when the measurement has no DOI, and a map of the sample's location. A measurement follows
  its own dataset: it opens for everyone once that dataset is public and published, whatever the
  state of its sample's dataset, and a sample in an unpublished dataset is described as one and
  never named, linked or mapped. A portal gives a measurement type its page with
  `<app_label>/<model_name>_overview.html`, and the demo's XRF measurement is the worked example.
  See [Overview pages](docs/portal-development/overview-pages.md).
- **`manage.py seed_overviews` loads development data for the overview pages**, and creates
  `regular.user@example.com`, `staff.user@example.com` and `super.user@example.com` when they are
  missing. It refuses to run outside development, leaves an existing account as it is, and
  replaces only the projects it created. `fairdm.E501` now reports these three addresses on a
  portal that is not in development. See
  [Development accounts](docs/portal-development/development_accounts.md).
- **Description text now has a 20,000-character ceiling.** Project, dataset, sample and
  measurement descriptions previously had no length limit anywhere between the editing page
  and the database. The limit is well beyond any real abstract or methods note, so ordinary
  metadata is unaffected; it stops an accidental paste of an entire document from landing in
  a description field.

#### Portal roles (Feature 017)

- **Four portal roles replace the three ungoverned groups from before**: Portal Administrator,
  Data Curator, Community Manager and Developer, each declared with an exact, named permission
  set and installed into every portal automatically, every time its database is brought up to
  date. Editing a role's permissions by hand no longer sticks — the next update restores the
  declared set. See [Portal roles](docs/portal-administration/roles.md).

#### Portal configuration via `fairdm.setup()` (Feature 001)

- **A single production baseline, layered per environment**: `fairdm/conf/settings/` is production-grade in every environment, and each environment is an override laid over it. Layers apply in a fixed order, later winning: the baseline, FairDM's `conf/<environment>.py`, settings contributed by addons, the portal's `<environment>.py`, then anything the portal assigns after the `setup()` call.
- **Environments are selected by name, and found by existence**: `DJANGO_ENV` names the environment and defaults to `production`. An override module applies if it exists; an environment nobody ships a module for resolves to the production baseline, with no error. There is no list of permitted environment names.
- **The portal's override module is found beside its settings module**, so `config/production.py` works for the recommended project layout without FairDM assuming a directory name.
- **A misconfigured production portal refuses to start**: the production-critical checks — database, cache, secret key, allowed hosts and debug — run automatically whenever the settings in force are the production baseline, and report every failure in one message rather than stopping at the first. The exemption is `development` alone, the one environment FairDM ships a non-production override for. A typo, a case variant such as `Production`, or an empty `DJANGO_ENV` all resolve to the production baseline and are checked against it.
- **`manage.py show_config`** reports the layers considered for the current environment, which were found, and the layer that produced any given setting's final value.

#### Plugin System for Model Extensibility (Feature 008)

- **Declarative Plugin Registration**: Simple decorator-based registration system
  - `@plugins.register(Model)` decorator for registering plugins with model classes
  - Multiple model registration: `@plugins.register(Sample, Measurement)`
  - Global registry singleton for centralized plugin management
  - Auto-discovery of plugins.py modules in Django apps

- **Plugin Mixin Architecture**: Composable plugin behavior with Django CBVs
  - `Plugin` mixin combines with any Django class-based view (TemplateView, UpdateView, DeleteView, etc.)
  - Automatic URL routing under model detail pages (e.g., `/samples/<uuid>/plugin-name/`)
  - Built-in permission checking (model-level and object-level via django-guardian)
  - Automatic object access via `self.object` (standard Django CBV pattern)

- **Tab-Based Navigation**: Automatic tab generation from menu configuration
  - `menu = {"label": "...", "icon": "...", "order": 0}` dict-based configuration
  - Tabs sorted by `order` then `label` for predictable layout
  - Permission-filtered tabs (users only see tabs they can access)
  - Active tab detection for current plugin
  - Cotton component: `<c-plugin-tabs />`for rendering tab UI

- **Hierarchical Template Resolution**: Automatic template discovery  
  - Model-specific templates: `plugins/{model_name}/{plugin_name}.html`
  - Polymorphic model support: `plugins/{parent_model_name}/{plugin_name}.html`
  - Plugin default: `plugins/{plugin_name}.html`
  - Framework fallback: `plugins/base.html`
  - Explicit override via `template_name` attribute

- **Plugin Groups**: Namespace multiple plugins under shared URL prefix and single tab
  - `PluginGroup` composition class wraps related plugins
  - Shared URL namespace (e.g., `/samples/<uuid>/metadata/view/`, `.../metadata/update/`)
  - Single tab entry linking to default (first) plugin
  - Group-level permission checking

- **Permission System Integration**: Two-tier permission checking
  - Model-level permissions: `permission = "app.change_model"` attribute
  - Object-level permissions: django-guardian integration in `has_permission()`
  - Visibility filtering: `check` function for polymorphic/conditional visibility
  - Helper: `is_instance_of(ModelClass)` for polymorphic filtering
  - Automatic 403 Forbidden on unauthorized access

- **Custom URL Patterns**: Override auto-generated URLs
  - `url_path` attribute for custom URL segments
  - `name` attribute for custom URL naming
  - Auto-generated slugified names from class name if not set
  - URL conflict detection via system checks

- **Reusable Plugin Base Classes**: Framework provides inheritablePlugin bases
  - `BaseOverviewPlugin`: Read-only overview with standard menu config
  - `BaseEditPlugin`: Form-based editing with permission checking
  - `BaseDeletePlugin`: Delete confirmation with success URL handling
  - Generic plugins: `KeywordsPlugin`, `DescriptionsPlugin`, `KeyDatesPlugin`
  - Portal developers inherit and customize for domain-specific behavior

- **Static Asset Management**: Django Media class integration
  - Declare CSS/JS dependencies via `class Media:` inner class
  - Automatic inclusion in template context as `plugin_media`
  - Support for both local files and CDN URLs
  - Template blocks: `{% block extra_head %}{{ plugin_media.css }}{% endblock %}`

- **Django System Checks**: Comprehensive validation (E001-E007, W001-W003)
  - **E001**: Missing required attributes (Plugin mixin or Django CBV)
  - **E002**: Duplicate plugin names for the same model
  - **E003**: URL path conflicts between plugins
  - **E004**: Invalid `template_name` (file doesn't exist)
  - **E005**: PluginGroup with empty `plugins` list
  - **E006**: PluginGroup contains invalid plugin classes
  - **E007**: URL prefix conflicts between plugin groups
  - **W001**: Invalid permission string (permission doesn't exist)
  - **W002**: Menu configuration missing required keys
  - **W003**: URL path contains invalid characters

- **Automatic Context & Breadcrumbs**: Plugins receive rich context automatically
  - `object`: Model instance (Project, Dataset, Sample, Measurement, etc.)
  - `tabs`: List of Tab objects for current model
  - `breadcrumbs`: Auto-generated navigation chain
  - `plugin_media`: Static assets if Media class defined
  - `view`: Plugin view instance for template access

- **Documentation & Examples**: Comprehensive guides for all user types
  - Developer guide: Creating plugins, inheritance patterns, advanced features
  - Portal admin guide: Managing plugins, permissions, troubleshooting
  - Demo app examples: 10+ working plugin implementations in `fairdm_demo/plugins.py`
  - Quickstart guide: Step-by-step plugin creation workflow
  - API documentation: Complete docstrings with usage examples

- **Testing Infrastructure**: Full test coverage for plugin system
  - 67 passing tests covering all 8 user stories
  - Unit tests: Plugin registration, tab generation, template resolution, permissions
  - Integration tests: URL routing, permission filtering, PluginGroups, context injection
  - System check tests: All error/warning validations
  - Demo app tests: Real-world plugin examples

#### Core datasets (Feature 004)

- A dataset records who created it.
- A dataset refuses a collection period that ends before it starts, in the administrative inline as
  well as on the record.
- Descriptions, dates and identifiers are all editable from a dataset's administrative page, and the
  list shows which datasets carry an abstract and a DOI.

#### Core samples (Feature 005)

- Creating a bare `Sample` — the polymorphic base every specimen type inherits from — is refused
  everywhere: through validation, a form, the administrative interface, direct saves and the
  manager, and even fixture loading. Only a registered specimen type (`RockSample`, `WaterSample`
  and so on) can be created.
- `Sample.objects` offers `with_related()`, `with_metadata()` and the new `with_keywords()`, each
  chainable with the others and with ordinary queryset methods, so a list of specimens loads with
  its dataset, location, descriptions, dates, identifiers, contributions and keywords in a number
  of queries that does not grow with how many specimens or related records there are.
- **A specimen can be given an IGSN.** The identifier vocabulary for samples previously listed
  identifiers for people, organisations and projects and contained no IGSN member at all, so the
  format check below it was unreachable. It now offers an IGSN and a DOI and nothing else.
- **Typed descriptions, dates and identifiers are validated.** A type outside the sample vocabulary
  is refused with a message naming it. The validators had never run.
- **A right granted on a specimen holds, and a right over a dataset reaches the specimens in it.**
  Reading a dataset confers reading its specimens; changing one confers changing them, deleting
  them and adding to it.
- **`SampleFormMixin` and `SampleFilterMixin` deliver what they document**, and are what the
  registry builds a specimen type's form and filter set from when the type supplies neither.
- The administrative interface finds a specimen by name, laboratory identifier or generated
  identifier, narrows by dataset, status or type, offers inline rows bounded by the vocabulary
  rather than by a hardcoded number, and reaches specimens in private datasets.

#### Core measurements (Feature 006)

- **A measurement type may nominate a `value` and, where the analysis produces one, an
  `uncertainty`, and gets formatted reporting for free.** `get_value()` and `print_value()` read
  those two fields and require nothing else from the type — no method to override, no string to
  build by hand. `ICP_MS_Measurement` ships with both fields as the worked example.
- **The quantity formatter is installed when the application starts, not the first time a
  template loads it.** A value read or rendered outside a template — in a shell, a management
  command, a test, an API response built without a template — now formats the same way a page
  does; previously it fell back to the unit library's own default formatting until some template
  happened to import the tag module that installed it.
- **The measurement type filter offers every registered type, not a fixed pair of applications.**
  It previously drew its choices from two hardcoded application labels, so the measurement record's
  own type was absent from the list, every unrelated model in those two applications appeared, and a
  portal's own measurement types — which live in the portal's own application — could never be
  selected. It now asks the registry, the same source the administrative interface already used.
- **Date filtering accepts a year, a year and month, or a full date**, matching what a measurement's
  own date fields accept. Filtering by an out-of-range or malformed date now reports a form error
  instead of an unhandled exception when the filtered list is rendered.
- **The registry validates a measurement type's administrative class against the class portals were
  already told to inherit from.** It previously validated against, and generated for a type
  supplying none, an unconfigured two-line stand-in — so a measurement type that inherited from
  the documented base as instructed was refused at registration, and one that supplied no
  administrative class of its own received none of the framework's inline editors, autocomplete
  fields or read-only handling. See Removed, below, for the stand-in's deletion.
- **A registered measurement type's generated form and filter set carry the framework's shared
  widgets, dataset scoping, search and date-range filtering without the type writing a form or
  filter class of its own.** That wiring previously existed for specimens and not for measurements,
  so it reached only the portals that wrote their own form and filter classes — the group that
  needed it least.
- **A measurement has an address of its own** (`get_absolute_url()`), rather than deflecting to its
  sample's page. The page that serves it is separate, later work.
- **Rights over a dataset reach its measurements.** A user holding view, change or delete over a
  dataset holds the matching right over the measurements in it; a right granted directly on a
  registered measurement type is honoured the same way.
- Two form defects are fixed: the "add another dataset" control on a measurement form previously
  pointed at an administrative address that does not exist, and the form's field guidance text
  (name, dataset, sample, tags) was declared under the wrong attribute and never reached the
  rendered form. Both mirror fixes already made on the equivalent sample form.
- Creating a bare `Measurement` — the polymorphic base every measurement type inherits from — is
  refused everywhere a bare `Sample` already is, including the framework's own test fixtures, which
  previously built one directly.
- `Measurement.objects` offers `with_related()` and `with_metadata()`, chainable with each other and
  with ordinary queryset methods, so a list of measurements loads its sample, dataset, contributors,
  descriptions, dates and identifiers in a number of queries that does not grow with how many
  measurements there are.

#### Contributors and Contributions (Feature 009)

- **`fairdm.contrib.contributors`**, a new app holding every contributor record.
  `Contributor` is a polymorphic base with two concrete types: `Person` — the account a user
  logs in with (`AUTH_USER_MODEL = "contributors.Person"`) — and `Organization`. Both share a
  public identifier (`uuid`, prefixed `c`), a name, alternative names, a profile, a profile
  image, links, language preferences, a location and a general-purpose `config` JSON store.
- **`Affiliation`** (aliased `OrganizationMember`) links a `Person` to an `Organization` with a
  membership type (`PENDING`, `MEMBER`, `ADMIN`, `OWNER`), a primary flag and partial-precision
  start/end dates. A person cannot hold two affiliations with the same organisation, and at
  most one of a person's affiliations is primary at a time — both enforced by validation and by
  a database constraint.
- **`Contribution`** credits a contributor on a `Project`, `Dataset`, `Sample` or `Measurement`
  through a `GenericForeignKey`, carrying roles drawn from the framework's `fairdm-roles`
  vocabulary. Crediting the same contributor again under a further role accumulates the role on
  the existing credit rather than replacing it (`Contributor.add_to()`, the `Contribution.add_to()`
  classmethod).
- **`ContributorIdentifier`** holds a contributor's external identifiers (ORCID for a person,
  ROR and others for an organisation), each syncing in the background on creation.
- **`Organization.type`**, drawn from ROR schema 2.1's institution types (`OrganizationType`):
  education, funder, healthcare, company, archive, nonprofit, government, facility, other.
- **Derived account state.** `Person.account_state` (`AccountState`: `GHOST`, `INVITED`,
  `CLAIMED`, `INACTIVE`) is computed from `is_active`, `is_claimed` and `email` rather than
  stored, and `Person.objects` carries a matching queryset method for each state — `ghost()`,
  `invited()`, `claimed()`, `inactive()` — plus `real()` (excludes superusers and the
  django-guardian anonymous placeholder) and `unclaimed()`.
- **Derived organisation ownership.** `manage_organization` is not a stored permission —
  `OrganizationPermissionBackend` answers it from whether the user holds an `OWNER` affiliation
  on the organisation at the moment of the check. `Organization.transfer_ownership()` demotes
  the incumbent owner to `ADMIN` and promotes the named member to `OWNER` in one atomic
  operation.
- **`ClaimingAuditLog`**, an immutable record of every profile-claiming event (method, source
  and target person, success, failure reason), with `ClaimingAuditLogManager` filters —
  `for_person()`, `failures()`, `by_method()`, `recent()`.
- Reporting methods on `Contributor`: `projects`, `datasets`, `samples`, `measurements`,
  `get_credit_counts()`, `get_collaborators()`, `has_contribution_to()`,
  `get_recent_contributions()`, `get_contributions_by_type()`.
- Export helpers `Contributor.to_datacite()` and `.to_schema_org()`, backed by
  `DataCiteTransform`, `SchemaOrgTransform`, `CSLJSONTransform`, `ORCIDTransform` and
  `RORTransform` (`fairdm.contrib.contributors.utils.transforms`) — each a transform instance
  with `export()`/`import_data()` methods.

### Changed

#### Core samples (Feature 005) — breaking

- **`fairdm.factories.SampleFactory` is abstract.** It declares the fields every specimen shares
  but can no longer be instantiated directly, matching `Sample` itself. A portal (or test) that
  called `SampleFactory()` now subclasses it — `fairdm_demo.factories.RockSampleFactory` is the
  reference example — the same way a portal already subclasses `Sample` for its own specimen
  types. `MeasurementFactory.sample` and `SampleRelationFactory.source`/`target` have no default
  for the same reason and must be passed a concrete specimen instance.
- **A sample's status describes where the specimen physically is.** The previous vocabulary was
  fetched over plain HTTP from a third-party host while Django loaded its applications, and its
  terms — complete, ongoing, planned, unknown — describe a data-collection activity rather than a
  specimen. It is replaced by a local vocabulary of custody states: available, in use, stored,
  destroyed, unknown. **Every existing status value is rewritten to unknown**, because none of the
  previous terms maps onto a custody state; the previous values are discarded and cannot be
  recovered. A portal that read a sample's status will find it reset.
- **The sample identifier vocabulary is narrowed to IGSN and DOI.** A portal storing any other type
  against a specimen will find it refused by validation.
- **An IGSN is validated as a DataCite identifier, not against the legacy handle prefix.** IGSN
  allocation moved to DataCite in 2023 and identifiers are now spread across dozens of registry
  prefixes, so the previous pattern rejected essentially every identifier in circulation. The
  legacy handle form is still accepted.
- **An identifier value is unique across every record type, not merely within one.** The
  uniqueness was declared on a shared abstract, which gives one index per table, so the same value
  could name a specimen and a dataset at once. Projects and measurements inherit the check too.
- **A sample's descriptions, keywords, key dates and edit pages require the right to change it.**
  They previously opened for anyone holding the specimen's address, including a visitor who had
  not signed in.
- **Object-level permissions resolve for a portal-defined specimen type.** The right is declared on
  the base record and the specimen lives in the portal's own application, so the check raised and
  the grant looked for a permission filed under the wrong content type. A shared backend normalises
  the record before the check, and `fairdm.core.utils.assign_perm` does the same when granting.
  Measurements gain the same repair. `guardian.backends.ObjectPermissionBackend` is no longer in
  `AUTHENTICATION_BACKENDS`; `fairdm.core.permissions.PolymorphicObjectPermissionBackend` replaces
  it and a portal listing the backends by hand should follow.
- **The specimen hierarchy has one traversal.** The queryset's ancestor and descendant walks ran
  opposite to the record's own, so each returned what the other promised. Neither had a caller.
- **A specimen cannot be its own parent, and two specimens cannot each descend from the other**,
  when saved directly rather than only under validation.

#### Portal configuration (Feature 001) — breaking

- **`fairdm.setup()` no longer accepts settings as keyword arguments.** The `**overrides` parameter is gone; assign the setting after the call instead, which was already the documented pattern and is now the only one. A portal passing settings this way will raise `TypeError` until it moves them.
- **`DJANGO_SECRET_KEY` and `DJANGO_SITE_DOMAIN` no longer have working defaults.** FairDM previously shipped a fallback secret key in its own source, so a production portal that never set the variable started on a key anyone could read and had its sessions and signed cookies forgeable. Both variables now hold an unusable value until set, and the production checks refuse the boot. Development is unaffected — the development override supplies clearly-marked local values.
- **Portal apps are registered ahead of FairDM's** in `INSTALLED_APPS`, so a portal's own templates and static files now take precedence over FairDM's at the same path. A portal that already ships a shadowing template will find it served where it was previously inert.
- **The staging environment is no longer supported.** `fairdm/conf/staging.py` is deleted and `DJANGO_ENV=staging` now resolves to the production baseline. A portal that wants staging supplies its own `staging.py` beside its settings module, which applies through the same layering as any other environment. Because those settings are the production baseline, a staging boot is held to the production-critical checks.
- **`THUMBNAIL_DEBUG` is off in the baseline.** easy-thumbnails re-raises rather than degrading to a blank image when it is on, which turned a missing source file into a 500. It is on in development, as before.

#### Core datasets (Feature 004)

- Datasets are private by default. Reading datasets the ordinary way no longer returns private
  ones. `Dataset.all_objects` is the explicit route for code that needs them, and the surfaces
  whose own permission check is the real gate — the API, plugin pages, the sample and measurement
  forms, and the administrative interface — use it so that check still runs.
- Dataset identifiers use a vocabulary that applies to datasets. The type list previously offered
  identifiers for people and organisations.
- Datasets are ordered most-recently-modified first. The previous ordering put the least recently
  touched record first.
- A dataset created without choosing a licence carries the portal's configured default, and the
  licences the framework recommends are seeded when a portal is stood up. A portal that has migrated
  previously had no licence rows at all, which left the default silently unapplied.
- A dataset's descriptions, keywords and key dates now require the `change_dataset` permission.
  These pages previously opened for anyone holding the dataset's address, including an
  unauthenticated visitor, and a portal upgrading will find that contributors who were never
  granted object-level rights over a dataset can no longer reach them.
- Creating a dataset through the portal grants the creator rights over it, matching what
  creating a project has always done. Without it a new dataset was unreachable by the person
  who had just made it, because a dataset is private by default.
- A dataset a user may not see answers 404 rather than 403, so a page no longer confirms that a
  private dataset exists.

#### Contributors and Contributions (Feature 009)

- **Deleting a parent organisation no longer deletes its children.** `Organization.parent` is
  `on_delete=SET_NULL`; a surviving sub-organisation loses its parent link, keeping its own
  members and credits.
- **Crediting the same contributor a second time accumulates the new role onto the existing
  credit instead of discarding the roles recorded the first time.**
- **Deleting a credit withdraws every object-level right it granted, whether the credit is
  deleted on the instance or in bulk through a queryset.** The lifecycle hook alone only
  covered the instance path; a `post_delete` signal receiver now covers the bulk one too.
- **`UserManager` gains `create_user()`.** The queryset methods on `PersonQuerySet`,
  `AffiliationQuerySet` and `ContributionQuerySet` are composed onto their managers with
  `Manager.from_queryset()`, matching the pattern the rest of the framework uses, rather than
  hand-written proxy methods.
- **`Person.email` keeps its field-level `unique=True`** alongside the case-insensitive
  database constraint that actually enforces uniqueness, so Django's own `USERNAME_FIELD`
  check (`auth.W004`) is satisfied by the means Django reads.

### Removed

#### Portal configuration (Feature 001)

- **`fairdm.conf.checks.validate_services()`**, deprecated since January in favour of Django's check framework, together with its documented migration path. `manage.py check --deploy` covers everything it did, and the production-critical subset now runs automatically at boot.

#### Plugin API Migration (Feature 008)

- **New Plugin API**: Simplified registration and configuration
  - **Before**: `@plugin.register('model.Model', category=plugins.EXPLORE)` with string-based registration
  - **After**: `@plugins.register(Model)` with direct model class reference
  - **Before**: `BasePlugin` base class with `menu_item = MenuLink(...)`
  - **After**: `Plugin` mixin with `menu = {"label": "...", "icon": "...", "order": 0}`
  - **Before**: `self.base_object` for instance access
  - **After**: `self.object` (standard Django CBV pattern)
  - **Before**: Category-based grouping (EXPLORE, ACTIONS, MANAGEMENT)
  - **After**: Order-based sorting with `menu["order"]` value
  
- **URL patterns**: No changes required - URLs auto-generated from plugin registration

- **Templates**: Hierarchical resolution now searches multiple paths automatically

- **Permissions**: Permission checking now integrated into Plugin.dispatch() with guardian support

#### Core datasets (Feature 004)

- `Dataset.ROLE_PERMISSIONS`, which mapped two role names the vocabulary does not contain and had no
  readers.
- `DatasetQuerySet.with_private()`, `.get_visible()` and `.for_user()`. The first discarded every
  condition applied before it, the second duplicated the default, and the third gated on a
  permission no model declares.
- The second name each related record carried for its two fields. Nothing read them, and one was an
  ORM path in a filter that raised on every use.

#### Core measurements (Feature 006)

- `fairdm.core.admin.MeasurementAdmin` and the second, unregistered `MeasurementParentAdmin`
  beside it — an unconfigured stand-in the registry validated against and generated from by
  mistake (see Changed, above). A portal's own measurement admin classes inherit from
  `fairdm.core.measurement.admin.MeasurementChildAdmin`, which is what the developer guide has
  always named.

#### Contributors and Contributions (Feature 009)

- **`Contributor.privacy_settings`** and **`Contributor.get_visible_fields()`**. Nothing in the
  codebase called `get_visible_fields` outside its own tests, and the field it read had no
  enforcement anywhere. `privacy_settings` is renamed to a general-purpose `config` JSON store
  whose contents this feature does not define; existing data is cleared in the migration.
- **`Contributor.weight`** and `calculate_weight()`, a stored ranking score nothing computed.

### Migration Guide

#### Upgrading Plugins to New API

**Step 1: Update imports**

```python
# Before
from fairdm.plugins import plugin, MenuLink, BasePlugin

# After
from fairdm import plugins
from fairdm.contrib.plugins import Plugin
```

**Step 2: Update registration decorator**

```python
# Before
@plugin.register('sample.Sample', category=plugins.EXPLORE)

# After
from .models import Sample
@plugins.register(Sample)
```

**Step 3: Update class definition**

```python
# Before
class MyPlugin(BasePlugin, TemplateView):
    menu_item = MenuLink(name="My Plugin", icon="chart")

# After
class MyPlugin(Plugin, TemplateView):
    menu = {"label": "My Plugin", "icon": "chart", "order": 20}
```

**Step 4: Update object access**

```python
# Before
def get_context_data(self, **kwargs):
    sample = self.base_object

# After
def get_context_data(self, **kwargs):
    sample = self.object
```

**Step 5: Run system checks**

```bash
poetry run python manage.py check
```

#### Configuration Checks System (Spec 003)

- **Polymorphic Sample Model**: Flexible sample inheritance with automatic type detection
  - Base `Sample` model with core fields (name, local_id, dataset, location, status, UUID)
  - Polymorphic QuerySet with automatic downcasting to subclass types
  - Support for custom Sample types via model inheritance
  - Integration with django-polymorphic for efficient polymorphic queries

- **Sample Metadata System**: Rich metadata support through related models
  - `SampleDescription`: Multiple descriptions per sample (abstract, methods, other types)
  - `SampleDate`: Temporal metadata with PartialDate support (collected, available, created types)
  - `SampleIdentifier`: Persistent identifiers (IGSN, barcodes, custom types)
  - `SampleContribution`: Track contributors with roles (collector, analyst, owner)
  - Generic relations for flexible metadata attachment

- **Sample Relationships & Provenance**: Track sample hierarchies and processing history
  - `SampleRelation`: Bidirectional relationships between samples
  - Common relationship types: child_of, derived-from, split-from, replicate-of
  - Validation prevents self-reference and direct circular relationships
  - Convenience methods: `get_children()`, `get_parents()`, `get_descendants(depth)`
  - Support for complex multi-level hierarchies

- **Optimized QuerySet Methods**: Performance-focused query patterns
  - `with_related()`: Prefetch dataset, location, contributors, and nested project
  - `with_metadata()`: Prefetch descriptions, dates, identifiers in bulk
  - `by_relationship()`: Filter samples by relationship type and related sample
  - `get_descendants()`: Iterative BFS traversal with depth limiting
  - Performance: <10 queries for 1000 samples, 80%+ query reduction

- **Forms & Filters**: Reusable mixins for Sample CRUD operations
  - `SampleFormMixin`: Standard form configuration with dataset filtering
  - `SampleFilterMixin`: Common filters for name, local_id, dataset, status, type
  - Permission-aware dataset queryset filtering
  - Crispy-forms integration for consistent UI
  - Bootstrap 5 compatible widgets

- **Admin Interface**: Comprehensive Django admin integration
  - Polymorphic parent/child admin for type selection
  - Inline editing for descriptions, dates, identifiers, relationships, contributors
  - Search by name, local_id, UUID
  - Filters by dataset, status, polymorphic type
  - List display with key fields and sample type column

- **Registry Integration**: Automatic component generation
  - Auto-generate ModelForm, FilterSet, Table, and ModelAdmin for custom Sample types
  - Configuration via `ModelConfiguration` class with `@register` decorator
  - Override auto-generated classes with custom implementations as needed
  - Field-level configuration for forms, filters, tables, and serializers

- **Testing Infrastructure**: Comprehensive test coverage
  - Unit tests for models, forms, filters, admin, registry integration
  - Integration tests for polymorphic queries, relationships, permissions
  - Performance tests for query optimization (marked with @pytest.mark.slow)
  - Factory support via fairdm_demo models (RockSample, WaterSample)
  - 99 passing tests across all sample functionality

- **Documentation**: Complete guides for developers and administrators
  - Developer guide: Custom sample types, field patterns, validation, QuerySet optimization
  - Forms & Filters guide: Mixins, customization, testing patterns
  - Admin guide: Managing samples, metadata, relationships, bulk operations
  - Quickstart guide: Step-by-step custom sample creation with working examples
  - API documentation with usage examples in all QuerySet methods

#### Configuration Checks System (Spec 003)

- **Django Check Framework Integration**: Migrated configuration validation from runtime logging to Django's check framework
  - 8 production-readiness checks for database, cache, security, and Celery configuration
  - Custom `DeployTags` class with 'deploy' tag for production-specific checks
  - Error IDs: fairdm.E001, E003-E005, E100-E101, E200, E300-E301
  - `python manage.py check --deploy` command for explicit production validation
  - Tag-based filtering (--tag security, --tag database, --tag caches, --tag deploy)
  - CI/CD friendly with proper exit codes and clear error messages
  - Comprehensive documentation in `docs/portal-administration/configuration-checks.md`
  - **Note**: Removed duplicate checks that Django already provides:
    - SECRET_KEY 'insecure' check (use Django's security.W009)
    - SECRET_KEY length check (use Django's security.W009)
    - SECURE_SSL_REDIRECT check (use Django's security.W008)
    - SESSION_COOKIE_SECURE check (use Django's security.W012)
    - CSRF_COOKIE_SECURE check (use Django's security.W016)

### Changed

#### Configuration Validation Improvements (Spec 003)

- **Removed runtime validation noise**: Configuration validation no longer runs automatically during setup
  - Development workflow is cleaner without constant warning messages
  - Validation is now explicit via `manage.py check` command
  - Production deployments should run `python manage.py check --deploy` in CI/CD pipelines

### Deprecated

#### Legacy Configuration Functions (Spec 003)

- **validate_services()**: Deprecated in favor of Django check framework
  - Function still exists but emits DeprecationWarning
  - Will be removed in a future version
  - Use `python manage.py check --deploy` instead
  - See migration guide in `docs/portal-administration/configuration-checks.md`

#### Core Dataset Models & CRUD Operations (Spec 006)

- **Dataset Model Enhancements**: Comprehensive FAIR-compliant dataset model
  - Enhanced docstrings with image guidelines (16:9 aspect ratio recommended)
  - Role-based permission mapping (Viewer/Editor/Manager → Django permissions)
  - ROLE_PERMISSIONS class attribute for permission management
  - Integration with django-guardian for object-level access control
  - Image field with upload directory and aspect ratio guidance
  - Support for orphaned datasets (project=null permitted)
  - PROTECT behavior on project deletion to prevent accidental data loss

- **DatasetQuerySet & Manager**: Privacy-first data access patterns
  - Default manager excludes PRIVATE datasets automatically
  - `with_private()` method for explicit private dataset access
  - `get_visible()` method returns only PUBLIC datasets
  - `with_related()` optimization (86% query reduction: 21→3 queries)
  - `with_contributors()` lighter optimization for contributor data
  - Method chaining support (combine filters efficiently)
  - Comprehensive docstrings with performance expectations

- **DatasetFilter**: Advanced filtering for list views and APIs
  - Generic search across name, UUID, keywords with Q objects
  - License exact match filtering (ModelChoiceFilter)
  - Project filtering with dynamic user context
  - Visibility filtering (PUBLIC/INTERNAL/PRIVATE)
  - Cross-relationship filters (description_type, date_type)
  - Database indexes for filter performance (10-20x improvement)
  - Comprehensive module docstring with best practices

- **DatasetForm**: User-friendly forms with smart defaults
  - Dynamic project queryset based on user permissions
  - CC BY 4.0 license pre-selected by default (FAIR compliance)
  - Crispy Forms integration with Bootstrap 5 layouts
  - Optional inline contributor management
  - Field ordering optimized for user workflow
  - Help text with documentation links

- **DatasetAdmin**: Powerful admin interface
  - List view with name, project, license, visibility, date added
  - Search across name, UUID, keywords, description text
  - Filtering by project, license, visibility, date added
  - Inline editing for descriptions, dates, identifiers, literature relations
  - Dynamic contributor limit based on vocabulary (max 5 per role)
  - Horizontal filter for contributor management
  - Bulk actions for common operations

- **DatasetLiteratureRelation**: Link datasets with publications
  - Intermediate model with DataCite relationship types
  - Choices: IsDocumentedBy, IsCitedBy, IsSupplementTo, IsDerivedFrom, etc.
  - Bidirectional relationships (dataset ↔ literature)
  - Vocabulary validation for relationship_type field
  - Comprehensive docstring with usage examples

- **Database Migrations**: Performance and structure updates
  - Migration 0008: Indexes for DatasetDescription.type and DatasetDate.type
  - PROTECT on_delete behavior for Dataset.project
  - DatasetLiteratureRelation intermediate model
  - Vocabulary validation for relationship types

#### Testing Infrastructure (Spec 006)

- **Comprehensive Test Suite**: 80+ tests across 8 test files
  - test_models.py: Dataset CRUD, validation, relationships (30+ tests)
  - test_filter.py: All filter types, performance, combinations (30+ tests)
  - test_queryset.py: Privacy-first, optimizations, chaining (25+ tests)
  - test_form.py: Form rendering, validation, user context (15+ tests)
  - test_admin.py: Admin interface, inlines, search/filter (20+ tests)
  - test_description.py: DatasetDescription vocabulary validation
  - test_date.py: DatasetDate vocabulary validation
  - test_identifier.py: DatasetIdentifier creation and DOI support
  - test_literature_relation.py: DataCite relationship types

- **Factory Examples**: Comprehensive test data generation patterns
  - DatasetFactory with CC BY 4.0 default license
  - DOI creation examples via DatasetIdentifier
  - Literature relation examples with DataCite types
  - Complete metadata example combining all patterns
  - Best practices documentation in fairdm_demo/factories.py

#### Demo App Updates (Spec 006)

- **QuerySet Optimization Examples**: 6 complete patterns in fairdm_demo/models.py
  - Privacy-first default usage with permission checks
  - with_related() optimization (86% query reduction)
  - with_contributors() lighter optimization
  - Method chaining examples
  - Performance monitoring with Django Debug Toolbar
  - Custom QuerySet pattern for custom models

- **Filter Examples**: 4 complete classes in fairdm_demo/filters.py
  - Generic search pattern across multiple fields
  - Cross-relationship filtering with indexes
  - ModelChoiceFilter with dynamic querysets
  - 10 best practices sections with rationale

- **Factory Examples**: 7 complete examples in fairdm_demo/factories.py
  - Basic Sample/Measurement factories
  - Dataset with default CC BY 4.0 license
  - DOI creation via DatasetIdentifier
  - Literature relations with DataCite types
  - Complete dataset with all metadata types

#### Documentation (Spec 006)

- **Research Documents**: Technical decisions and rationale
  - Image aspect ratio research (16:9 recommendation, Bootstrap cards, Open Graph)
  - DataCite RelationType vocabulary analysis
  - Performance optimization strategies

- **Model Docstrings**: Comprehensive documentation in code
  - Image Guidelines section with aspect ratio specifications
  - Role-Based Permissions section with permission mapping
  - Usage examples for has_perm() checks
  - Integration with django-guardian

#### Project Admin Interface Enhancements

- **Advanced Search Capabilities**: Enhanced ProjectAdmin with comprehensive search functionality
  - Search projects by name, UUID, and owner organization
  - Fast full-text search across multiple fields for quick project discovery
  - Support for partial name matching and exact UUID lookups

- **Smart Filtering System**: Added powerful filter options for project management
  - Filter by project status (Concept/Active/Completed)
  - Filter by visibility (Public/Private)
  - Filter by date added (Today, Past 7 days, This month, This year)
  - Combine multiple filters for precise project queries

- **Organized Form Layout**: Improved admin form with collapsible fieldsets
  - Basic Information section (always visible)
  - Access & Visibility section (collapsible)
  - Organization section with keywords (collapsible)
  - Metadata section for funding JSON (collapsible)
  - Cleaner, more focused editing experience

- **Inline Metadata Editing**: Edit related project data without leaving the page
  - ProjectDescription inline for adding multiple description types
  - ProjectDate inline for managing project dates
  - ProjectIdentifier inline for external identifiers (DOI, grant numbers)

- **Bulk Operations**: Efficient management of multiple projects at once
  - Bulk status changes (Mark as Concept/Active/Completed)
  - Bulk export as JSON for data portability
  - Bulk export as DataCite JSON for DOI registration
  - User feedback messages confirming operation success

- **Internationalization**: Full i18n support for admin interface
  - All user-facing strings wrapped with gettext_lazy
  - Ready for translation to multiple languages
  - Consistent terminology across admin interface

#### Registry System Enhancements

- **Registry Introspection API**: New properties `registry.samples`, `registry.measurements`, and `registry.models` for programmatic discovery of registered models
  - Enables dynamic iteration over all registered Sample subclasses
  - Provides access to all registered Measurement subclasses
  - Allows retrieval of all registered models (Samples + Measurements combined)
  - Supports filtering and programmatic model discovery workflows

#### Performance & Scalability

- **Performance Benchmarks**: Comprehensive test suite validating registry performance requirements
  - Single model registration: <10ms per model (actual: ~4 microseconds)
  - Component generation: <50ms per component type on first access (actual: ~100 microseconds)
  - Cached access: <1ms for dictionary lookup operations (actual: <1 microsecond)
  - Scalability: Support for 20+ registered models without noticeable startup delay
- **Cached Property Optimization**: Efficient caching of auto-generated components (forms, tables, filters, etc.)

#### Type Safety & Developer Experience

- **Comprehensive Type Hints**: Full mypy compatibility across all registry modules
  - Added type annotations for all method parameters and return types
  - Improved IDE support and static analysis capabilities
  - Enhanced developer experience with better autocomplete and error detection
- **Contract Compliance Testing**: Protocol verification ensuring implementation matches specifications
  - Validates FairDMRegistry Protocol compliance
  - Verifies ModelConfiguration Protocol adherence
  - Tests registration API compatibility and type safety

#### Configuration System Improvements

- **Enhanced ModelConfiguration**: Improved dataclass field inheritance handling
  - Fixed model attribute inheritance from class to instance level
  - Better support for declarative model registration patterns
  - Improved validation and error reporting for configuration issues

### Fixed

- **Model Registration**: Fixed dataclass field inheritance issue where class-level `model` attributes weren't properly inherited by instances
- **Demo App Registration**: Corrected `@register` decorator usage in demo configuration files
- **Test Compatibility**: Resolved Django model name conflicts in test suite for better test isolation

### Technical Details

#### API Additions

```python
# New introspection properties
registry.samples         # Iterator[Type[Sample]] - all registered Sample subclasses
registry.measurements    # Iterator[Type[Measurement]] - all registered Measurement subclasses
registry.models         # Iterator[Type[Model]] - all registered models combined

# Enhanced performance characteristics
# - Registration: 4μs per model (well under 10ms requirement)
# - Component generation: 100μs per component (well under 50ms requirement)
# - Cached access: <1μs per lookup (well under 1ms requirement)
```

#### Performance Metrics

- **Registration Performance**: Average 4 microseconds per model registration
- **Component Generation**: Average 100 microseconds for form/table/filter generation
- **Cached Access**: Sub-microsecond performance for repeated component access
- **Startup Performance**: <500ms for 25+ registered models
- **Memory Efficiency**: <1KB registry overhead per registered model

#### Type Safety

- Full mypy compliance across `fairdm.registry.*` modules
- Comprehensive Protocol definitions for public APIs
- Enhanced IDE support with complete type annotations

#### Test Coverage

- **Core Features**: 61.8% coverage on completed functionality
- **Introspection API**: 100% test coverage with 12 comprehensive test cases
- **Performance Testing**: 7 benchmark tests validating all performance requirements
- **Contract Compliance**: 4 Protocol verification tests ensuring API compatibility

### Breaking Changes

None - All changes are backward compatible additions to the existing API.

### Migration Guide

No migration required. New introspection properties are additive features that don't affect existing code.

#### Using New Introspection Features

```python
from fairdm.registry import registry

# Iterate over all registered Sample models
for sample_model in registry.samples:
    print(f"Sample: {sample_model.__name__}")

# Access all registered Measurement models
for measurement_model in registry.measurements:
    print(f"Measurement: {measurement_model.__name__}")

# Get all registered models (Samples + Measurements)
all_models = list(registry.models)
print(f"Total registered models: {len(all_models)}")
```

### Development

- Enhanced development experience with comprehensive type hints and better error messages
- Improved testing infrastructure with performance benchmarks and contract validation
- Better documentation of registry patterns and API usage examples

---

*This changelog documents registry system enhancements delivered in the 002-fairdm-registry feature branch.*
