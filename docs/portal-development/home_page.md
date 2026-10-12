# Home page

The address `/` shows two different pages. Someone who has signed in gets their dashboard. Everyone
else gets the landing page, which this guide covers: what it shows, the settings that change it,
and how to add sections of your own.

The landing page is built from [daisy-cotton-ext](https://github.com/django-mvp/daisy-cotton-ext)
page blocks, which FairDM installs and whose stylesheet it links for you. A portal that sets
nothing gets a complete page.

## What the page shows

The page has no navigation bar, so the hero starts at the top of the window. Under it come the
sections below, in this order. A section with nothing to show is left out, so a new portal with no
records shows the hero, the about section, the API section, the closing invitation and the footer.

| Section | Block | Component | What it shows | Left out when |
| --- | --- | --- | --- | --- |
| Hero | `landing.hero` | `c-landing.hero` | Title, lead and buttons, from `HOME_PAGE_CONFIG` | never |
| Figures | `landing.stats` | `c-landing.stats` | Counts of public datasets, samples and measurements, and of people and organizations | every count is zero |
| About | `landing.about` | `c-landing.about` | The portal's description, its keywords and who runs it | never |
| Latest datasets | `landing.datasets` | `c-landing.datasets` | The three public datasets changed most recently | there is no public dataset |
| Samples and measurements | `landing.types` | `c-landing.types` | The registered sample and measurement types, with a count and a link to each table | nothing is registered |
| Community | `landing.community` | `c-landing.community` | The most-credited people and organizations | there are no people and no organizations |
| New projects | `landing.projects` | `c-landing.projects` | The three public projects added most recently | there is no public project |
| API | `landing.api` | `c-landing.api` | An example request and a link to the API documentation | never |
| Invitation | `landing.join` | `c-landing.join` | A prompt to create an account, or to sign in when registration is closed | never |
| Footer | `landing.footer` | `c-landing.footer` | Logo, links and the copyright line | never |

Everything counted or listed is what a visitor who has not signed in may open. A private dataset,
a public dataset inside a private project, and the samples and measurements of a dataset that is
not yet published are never counted or named.

Each list of sample or measurement types holds at most five, those with the most public records
first. Any others are summed up in a last row.

## Settings

### `HOME_PAGE_CONFIG`

The hero's words and picture. Every key is optional, and a key you leave out keeps its default.

```python
# config/settings.py

HOME_PAGE_CONFIG = {
    "eyebrow": "Research data portal",
    "title": "Welcome to {site_name}",
    "lead": "Heat flow measurements from five continents, open to everyone.",
    "image": "portal/hero.jpg",
    "logo": True,
}
```

| Key | Default | What it does |
| --- | --- | --- |
| `eyebrow` | `"Research data portal"` | The short line above the title. `False` hides it. |
| `title` | `"Welcome to {site_name}"` | The page's heading. `False` hides it. |
| `lead` | A sentence about FAIR research data | The sentence under the title. `False` hides it. |
| `image` | `None` | A background picture: a path under your static files, or a full address. Without one the hero is drawn in your theme's colours. |
| `logo` | `True` | Shows the portal's logo above the title. `False` hides it. The logo is only drawn when there is no picture. |

`eyebrow`, `title` and `lead` may contain `{site_name}`. It is replaced by the name saved in the
portal identity in the administration interface, or by the `SITE_NAME` setting when no name has
been saved.

With a picture, the picture is dimmed and the hero's text turns light. Choose one that still
reads behind a line of text.

### `PORTAL_DESCRIPTION`

The paragraph in the about section. The description saved in the portal identity takes its place
once one has been saved.

```python
PORTAL_DESCRIPTION = "A community portal for geothermal data from the Upper Rhine Graben."
```

### `ACCOUNT_ALLOW_REGISTRATION`

When this is `False`, the page stops offering account creation. The hero and the footer drop the
link, and the closing invitation asks members to sign in.

## Adding to the page

Add a template named `fairdm/landing.html` to your portal, extend the one FairDM ships, and fill
the block for the section you want to change. Django finds your template first because your
portal's apps are listed ahead of FairDM's.

`{{ block.super }}` draws the section FairDM put in the block. Put your content before or after it
to add a section at that point of the page, or leave it out to replace the section.

```django
{# templates/fairdm/landing.html #}
{% extends "fairdm/landing.html" %}
{% load i18n %}

{% block landing.about %}
  {{ block.super }}
  <c-section class="bg-base-200">
    <c-heading eyebrow="{% translate 'Funding' %}"
               title="{% translate 'Supported by the German Research Foundation' %}" />
  </c-section>
{% endblock landing.about %}
```

The demo portal does this in `demo/templates/fairdm/landing.html`, to say that its records are
examples.

`landing.footer` holds the footer and works the same way. One more block, `landing.header`, is
empty: fill it to put a navigation bar above the hero.

```django
{% block landing.header %}
  <c-app.header />
{% endblock landing.header %}
```

## The components

Each section is a Cotton component that takes its data as attributes, so you can draw one on a
page of your own by passing it a queryset or a list:

```django
<c-landing.datasets :datasets="featured_datasets" />
```

The table gives each component's attributes and the name the landing page's own view,
`fairdm.views.generic.FairDMHomeView`, puts its data under.

| Component | Attributes | In the landing page's context |
| --- | --- | --- |
| `c-landing.hero` | `eyebrow`, `title`, `lead`, `image`, `logo`, `allow_registration`, and an `actions` slot that replaces the buttons | `hero.eyebrow`, `hero.title`, `hero.lead`, `hero.image`, `hero.logo`, `allow_registration` |
| `c-landing.stats` | `counts`: a list of figures, each with a `title`, a whole-number `value` and an `icon` name | `portal_counts` |
| `c-landing.about` | `name`, `description`, `keywords`, `authority`, `authority_url` | `about.name`, `about.description`, `about.keywords`, `about.authority`, `about.authority_url` |
| `c-landing.datasets` | `datasets` | `latest_datasets` |
| `c-landing.types` | `sample_types`, `measurement_types`: each a dictionary with `shown` (the types to list) and `more` (how many were left out) | `sample_types`, `measurement_types` |
| `c-landing.community` | `people`, `people_count`, `organizations` | `people`, `people_count`, `organizations` |
| `c-landing.projects` | `projects` | `latest_projects` |
| `c-landing.api` | `api_url`: the address shown in the example request | none: pass the address yourself |
| `c-landing.join` | `name`, `allow_registration` | `about.name`, `allow_registration` |
| `c-landing.footer` | `name`, `authority`, `allow_registration` | `about.name`, `about.authority`, `allow_registration` |

`c-landing.types` draws each of its lists with `c-landing.type-list`, which takes `title`, `icon`,
`types` and `more`.

## Changing what a section shows

`FairDMHomeView` reads each section's data from one method, and every method returns only what a
visitor may see. Subclass the view to change a limit or a whole section, and route `/` to your
subclass ahead of FairDM's URLs.

```python
# portal/views.py
from fairdm.core.dataset.models import Dataset
from fairdm.views.generic import FairDMHomeView


class HomeView(FairDMHomeView):
    latest_limit = 6
    people_limit = 12

    def get_latest_datasets(self):
        return (
            Dataset.objects.get_visible()
            .with_list_data()
            .filter(published=True)
            .order_by("-modified")[: self.latest_limit]
        )
```

| Attribute | Default | What it limits |
| --- | --- | --- |
| `latest_limit` | `3` | Datasets in the latest datasets section, and projects in the new projects section |
| `record_type_limit` | `5` | Sample types, and measurement types, listed before the rest are summed up |
| `people_limit` | `8` | Faces in the community section |
| `organization_limit` | `6` | Organizations named in the community section |
| `hero_defaults` | see `HOME_PAGE_CONFIG` | The hero's content where the setting leaves a key out |

| Method | Feeds |
| --- | --- |
| `get_hero()` | `hero` |
| `get_about()` | `about` |
| `get_portal_name()` | The name used by the hero's placeholder and the about section |
| `get_counts()` | `portal_counts` |
| `get_latest_datasets()` | `latest_datasets` |
| `get_latest_projects()` | `latest_projects` |
| `get_record_types(base, models)` | `sample_types` and `measurement_types` |
| `get_people()` | `people` |
| `get_organizations()` | `organizations` |

### Record cards

The dataset and project cards on the page are the ones the listings draw. Both are components:

```django
<c-dataset.card :object="dataset" />
<c-project.card :object="project" />
```

Load the dataset with `Dataset.objects.get_visible().with_list_data()` and the project with
`Project.objects.get_visible().with_list_data().with_contributors()`. A queryset without them
costs extra queries for every card.

## Upgrading from the earlier landing page

The landing page used to extend `mvp/landing.html` and draw a single hero. A portal with a
`fairdm/landing.html` of its own that filled that template's blocks changes two things:

1. Move content from `page.hero` into `landing.hero`, and content from `page.content` into the
   block of the section it should follow, after `{{ block.super }}`.
2. Replace any use of the `hero_content` context variable with `hero`. Its `title` and `lead` are
   set through `HOME_PAGE_CONFIG`, and its `image` through the setting's `image` key.
