# How to change the entrance layout

The sign-in, sign-up and password pages share one layout, with the form in one half and a pane in the other. You change the layout when you want the pane on the other side, another background, or another arrangement from daisy-cotton-ext.

## Before you start

You need a templates directory in one of your portal's apps. The layout is described in [Entrance pages](../reference/entrance-pages.md). To change only the words in the pane, use [How to change the entrance pane](change-the-entrance-pane.md).

## Steps

1. Create `templates/mvp_accounts/entrance/base.html` in your portal. It replaces the template FairDM ships under the same name.

2. Extend `mvp_accounts/entrance/layout.html`, link the stylesheets, and wrap `{{ block.super }}` in the layout component you want. This example puts the pane on the leading edge:

   ```django
   {# templates/mvp_accounts/entrance/base.html #}
   {% extends "mvp_accounts/entrance/layout.html" %}
   {% load static %}

   {% block styles %}
     {{ block.super }}
     <link rel="stylesheet" href="{% static 'css/daisy-cotton-ext.css' %}" />
     <link rel="stylesheet" href="{% static 'css/fairdm.css' %}" />
   {% endblock styles %}

   {% block layout %}
     {% firstof identity.dataset.description config.portal_description as portal_description %}
     <c-sign-in.split reverse surface="dce:bg-base-200 dce:text-base-content">
       <c-slot name="background">
         <c-background.aurora />
         <c-background.grid />
       </c-slot>
       <c-slot name="aside">
         <c-entrance.aside :name="page_config.brand.text"
                           :description="portal_description"
                           :authority="identity.authority.name"
                           :authority_url="identity.authority.url" />
       </c-slot>
       {{ block.super }}
     </c-sign-in.split>
   {% endblock layout %}
   ```

3. Open the sign-in page and the sign-up page. Both use the template.

## Things to know

- **Link the stylesheets.** The entrance pages do not extend FairDM's base template, so the layout's utilities, which are all prefixed `dce:`, reach them only through this template.
- **One layout covers every entrance page.** Each page already has one top-level heading, on its form. A layout that draws a heading of its own gives every page two.
- **Wrap `{{ block.super }}` in a Cotton component.** Plain HTML around it raises an error.

## The result

Every entrance page uses your layout. The layouts daisy-cotton-ext ships, and the attributes and slots of each, are listed in its documentation. django-mvp-accounts documents what `{{ block.super }}` hands to the layout, under "Choosing the entrance layout".
