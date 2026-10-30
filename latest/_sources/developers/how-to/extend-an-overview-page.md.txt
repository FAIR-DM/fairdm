# How to extend an overview page

A project, dataset, sample, measurement, person and organization each open on an overview page built from template blocks. You extend a page by overriding its template and filling the blocks you want to change, so you add a card or replace one without rewriting the page.

## Before you start

You need a templates directory in one of your portal's apps. The blocks of each page are listed in [Overview page blocks](../reference/overview-page-blocks.md), and the context they read in [Overview plugins](../reference/overview-plugins.md). For a sample or measurement type with its own fields, use [How to give a sample or measurement type its own overview page](give-a-sample-or-measurement-type-its-own-overview-page.md) instead.

## Steps

1. Create a template in your portal with the same name as the one you want to extend. Your template is found before FairDM's, because a portal's apps are listed ahead of FairDM's ([ADR 0004](../../adr/0004-portal-apps-precede-framework-apps.md)). The names are:

   | Page | Template |
   |---|---|
   | Project | `project/project_detail.html` |
   | Dataset | `dataset/dataset_detail.html` |
   | Person | `contributors/overview/person.html` |
   | Organization | `contributors/overview/organization.html` |

2. Extend the template you are replacing, so that every block you do not fill keeps FairDM's content.

3. Fill the block you want to change. Put `{{ block.super }}` first to keep what FairDM draws there. This adds a card to the end of a project's side column:

   ```django
   {% extends "project/project_detail.html" %}

   {% block overview.side %}
     {{ block.super }}
     <c-mvp.card title="Our funder's reporting" class="bg-base-100">
       Reports for {{ record.name }} are filed with the funder each year.
     </c-mvp.card>
   {% endblock overview.side %}
   ```

4. To change what one piece says, fill the block that draws it and leave `{{ block.super }}` out. This replaces the people row in a project's header:

   ```django
   {% extends "project/project_detail.html" %}

   {% block overview.byline %}
     <p class="text-sm">Led by {{ header_people|join:", " }}</p>
   {% endblock overview.byline %}
   ```

5. To add data a block needs, subclass the page's plugin and add it to the context. See [Overview plugins](../reference/overview-plugins.md) for the methods you can override.

6. Open a record of that kind.

## The result

The page shows your change and every card you did not touch. A block that wraps other blocks (`overview.main`, `overview.side`, `overview.details`) keeps its content only when you include `{{ block.super }}`. The design is explained in [ADR 0023](../../adr/0023-an-overview-page-is-extended-through-blocks-plugin-methods-and-type-templates.md).
