# Home page

The address `/` shows two pages. A signed-in user gets a dashboard (`fairdm/dashboard.html`). Everyone else gets the landing page (`fairdm/landing.html`), which this page describes: its sections, the template blocks that hold them and the view that feeds them. What a visitor sees on the screen is described in [the home screen](../../users/home.md). The settings that change the page are described in [Settings](settings.md): `HOME_PAGE_CONFIG`, `PORTAL_DESCRIPTION` and `ACCOUNT_ALLOW_REGISTRATION`.

The landing page is built from daisy-cotton-ext page blocks, whose stylesheet FairDM links for you. The view is `fairdm.views.generic.FairDMHomeView`, routed at `/` in `fairdm.conf.urls`.

## Sections

The page has no navigation bar, so the hero starts at the top of the window. The sections come in this order. Each is a template block, a component and a context entry the view provides. A section with nothing to show draws nothing.

| Section | Block | Component | Context entry | Left out when |
|---|---|---|---|---|
| Hero | `landing.hero` | [`c-landing.hero`](components.md#c-landinghero) | `hero`, `allow_registration` | never |
| Figures | `landing.stats` | [`c-landing.stats`](components.md#c-landingstats) | `portal_counts` | every count is zero |
| About | `landing.about` | [`c-landing.about`](components.md#c-landingabout) | `about` | never |
| Latest datasets | `landing.datasets` | [`c-landing.datasets`](components.md#c-landingdatasets) | `latest_datasets` | there is no public dataset |
| Samples and measurements | `landing.types` | [`c-landing.types`](components.md#c-landingtypes) | `sample_types`, `measurement_types` | no type is registered |
| Community | `landing.community` | [`c-landing.community`](components.md#c-landingcommunity) | `people`, `people_count`, `organizations` | there are no people and no organizations |
| New projects | `landing.projects` | [`c-landing.projects`](components.md#c-landingprojects) | `latest_projects` | there is no public project |
| API | `landing.api` | [`c-landing.api`](components.md#c-landingapi) | none: the template builds the address of the dataset endpoint | never |
| Invitation | `landing.join` | [`c-landing.join`](components.md#c-landingjoin) | `about`, `allow_registration` | never |
| Footer | `landing.footer` | [`c-landing.footer`](components.md#c-landingfooter) | `about`, `allow_registration` | never |

Two more blocks complete the template:

| Block | Holds |
|---|---|
| `landing.header` | Empty. Fill it to put a navigation bar above the hero, for example `<c-app.header />`. |
| `title` | The page title, the portal's name. |

`hero` has the keys `eyebrow`, `title`, `lead`, `image` and `logo`. `about` has `name`, `description`, `keywords`, `authority` and `authority_url`.

`landing.footer` fills the shell's `app.footer` block, and `landing.header` fills its `app.header` block.

## What a section may show

Every method that feeds a section returns only what a visitor who has not signed in may open. A private dataset, a public dataset inside a private project, and the samples and measurements of a dataset that is not published are never counted or named.

## `FairDMHomeView`

### Attributes

| Attribute | Default | What it limits |
|---|---|---|
| `latest_limit` | `3` | Datasets in the latest datasets section, and projects in the new projects section. |
| `record_type_limit` | `5` | Sample types, and measurement types, listed before the rest are counted. |
| `people_limit` | `8` | People in the community section. |
| `organization_limit` | `6` | Organizations named in the community section. |
| `hero_defaults` | a dictionary | The hero's content where `HOME_PAGE_CONFIG` leaves a key out: `logo` (`True`), `eyebrow`, `title`, `lead` and `image` (`None`). |
| `landing_template_name` | `fairdm/landing.html` | The template a visitor gets. |
| `dashboard_template_name` | `fairdm/dashboard.html` | The template a signed-in user gets. |

### Methods

| Method | Returns | Feeds |
|---|---|---|
| `get_landing_context(context)` | The context with every entry below added. | The landing template. |
| `get_portal_name()` | The name saved in the portal identity, else `SITE_NAME`. | `hero` and `about` |
| `get_hero()` | A dictionary of `eyebrow`, `title`, `lead` (with `{site_name}` filled in, empty where the setting is `False`), `image` (an address, or empty) and `logo`. | `hero` |
| `get_about()` | A dictionary of `name`, `description` (the saved one, else `PORTAL_DESCRIPTION`), `keywords`, `authority` and `authority_url`. | `about` |
| `get_counts()` | A list of dictionaries with `title`, `icon` and `value` for public datasets, samples, measurements, people and organizations, leaving out any that is zero. | `portal_counts` |
| `get_latest_datasets()` | At most `latest_limit` public datasets, most recently modified first, loaded with `with_list_data()`. | `latest_datasets` |
| `get_latest_projects()` | At most `latest_limit` public projects, most recently added first, loaded with `with_list_data()` and `with_contributors()`. | `latest_projects` |
| `get_record_types(base, models)` | A dictionary of `shown` (at most `record_type_limit` types, each with `name`, `description`, `count` and `url`, most public records first) and `more`. `base` is `Sample` or `Measurement`. | `sample_types`, `measurement_types` |
| `get_people()` | At most `people_limit` people, credited on the most records first. | `people` |
| `get_organizations()` | At most `organization_limit` organizations, credited on the most records first. | `organizations` |

The view also adds `people_count` (the number of people the portal lists) and `allow_registration` (the `ACCOUNT_ALLOW_REGISTRATION` setting).

## Tasks

- [How to add a section to the home page](../how-to/add-a-section-to-the-home-page.md)
- [How to change what a home page section shows](../how-to/change-what-a-home-page-section-shows.md)
