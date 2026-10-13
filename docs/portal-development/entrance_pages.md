# Entrance pages

The entrance pages are the ones a visitor sees before signing in: sign in, create an account,
reset a password, confirm an email address and the second step of a two-factor sign-in. This guide
covers how FairDM lays them out and how a portal changes that.

## What the pages show

Every entrance page uses one layout. The form takes one half of the window, with the portal's logo
above it. The other half is a pane that names the portal, on a background drawn in your theme's
colours. On a window narrower than 1024 pixels the pane is left out and the form has the page.

The pane shows:

| Line | Where it comes from |
| --- | --- |
| The portal's name | The name saved in the portal identity, or the `SITE_NAME` setting when none has been saved |
| The portal's description | The description saved in the portal identity, or the `PORTAL_DESCRIPTION` setting when none has been saved. Left out when there is neither |
| Who runs the portal | The authority saved in the administration interface, linked when it has an address. Left out when no authority has been saved |

Nothing in the pane is needed to sign in. It is there so that someone who arrives from a link deep
in the portal can see which portal they are signing in to.

The layout is the split sign-in page from
[daisy-cotton-ext](https://github.com/django-mvp/daisy-cotton-ext), which FairDM installs. The
pages themselves, with their forms and buttons, come from
[django-mvp-accounts](https://github.com/django-mvp/django-mvp-accounts).

## Changing the pane

The pane is the component `c-entrance.aside`. To say something else beside the form, add a
template named `cotton/entrance/aside.html` to your portal. Django finds your template first
because your portal's apps are listed ahead of FairDM's.

The component is given four attributes: `name`, `description`, `authority` and `authority_url`.

```django
{# templates/cotton/entrance/aside.html #}
<c-vars name description authority authority_url />
<div class="dce:flex dce:max-w-xl dce:flex-col dce:gap-4">
  <p class="dce:text-4xl dce:font-bold dce:tracking-tight">{{ name }}</p>
  <p class="dce:text-lg">Heat flow measurements from five continents, open to everyone.</p>
</div>
```

Write the portal's name as a paragraph and not as a heading. Each entrance page already has one
top-level heading, on its form.

## Changing the layout

To lay the pages out another way, add a template named `mvp_accounts/entrance/base.html` to your
portal and wrap `{{ block.super }}` in the layout you want. This example puts the pane on the
leading edge and draws it on a dark surface:

```django
{# templates/mvp_accounts/entrance/base.html #}
{% extends "mvp_accounts/entrance/layout.html" %}
{% load static %}

{% block styles %}
  {{ block.super }}
  <link rel="stylesheet" href="{% static 'css/daisy-cotton-ext.css' %}" />
{% endblock styles %}

{% block layout %}
  <c-sign-in.split reverse>
    <c-slot name="background"><c-background.grid /></c-slot>
    <c-slot name="aside">
      <c-entrance.aside :name="page_config.brand.text" />
    </c-slot>
    {{ block.super }}
  </c-sign-in.split>
{% endblock layout %}
```

Three things to know:

- **Link the stylesheet.** The entrance pages do not extend FairDM's base template, so
  daisy-cotton-ext's stylesheet reaches them only through this template.
- **One layout covers every entrance page.** A layout with a page heading of its own, such as
  `c-sign-up.pitch`, gives every page but sign-in and sign-up two top-level headings.
- **Wrap `{{ block.super }}` in a Cotton component.** Plain HTML around it raises an error.

The layouts daisy-cotton-ext ships, and the attributes and slots each one takes, are listed in its
own documentation. django-mvp-accounts documents the pieces `{{ block.super }}` hands to the
layout, under "Choosing the entrance layout".
