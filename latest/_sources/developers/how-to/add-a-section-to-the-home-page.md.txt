# How to add a section to the home page

The landing page a visitor sees at `/` is a stack of sections, each in a template block of its own. You add a section of your own when the portal has something to say that FairDM's sections do not, such as a funder or a notice that the records are examples.

## Before you start

You need a templates directory in one of your portal's apps. The blocks and their order are listed in [Home page](../reference/home-page.md).

## Steps

1. Create `templates/fairdm/landing.html` in your portal. Your template is found before FairDM's, because a portal's apps are listed ahead of FairDM's ([ADR 0004](../../adr/0004-portal-apps-precede-framework-apps.md)).

2. Extend FairDM's template and fill the block that sits next to where you want the new section. `{{ block.super }}` draws the section FairDM puts in the block, so content before or after it adds a section at that point.

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

3. To put a navigation bar above the hero, fill the empty `landing.header` block.

   ```django
   {% block landing.header %}
     <c-app.header />
   {% endblock landing.header %}
   ```

4. Open `/` while signed out.

## The result

Your section appears after the about section. A block filled without `{{ block.super }}` replaces FairDM's section instead of adding to it. To change what an existing section contains, see [How to change what a home page section shows](change-what-a-home-page-section-shows.md). The components you can draw on a page of your own are listed in [Components](../reference/components.md#landing-page-sections).
