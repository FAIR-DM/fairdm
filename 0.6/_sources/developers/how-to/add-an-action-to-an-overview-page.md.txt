# How to add an action to an overview page

A record's overview page has no central editing menu. Each part of the record is edited from the panel that shows it, and the header carries the actions that concern the whole record. You add an action of your own when a record has one that belongs on its page, such as importing data into it.

## Before you start

You need the template of the page you are changing. For a sample or measurement type this is the type's own overview template, described in [How to give a sample or measurement type its own overview page](give-a-sample-or-measurement-type-its-own-overview-page.md). The shared editing pages and the links to them are described in [Record editing pages](../reference/record-editing-pages.md#the-edit-links).

## An action on the whole record

1. In the template, fill the `overview.manage` block and keep what it holds with `{{ block.super }}`. The block holds the header's Edit, which opens the record's details.

   ```django
   {% block overview.manage %}
     {{ block.super }}
     {% if can_manage %}
       <c-button href="{{ import_url }}" text="Import data" icon="upload" size="sm" />
     {% endif %}
   {% endblock overview.manage %}
   ```

2. Supply `import_url` from the plugin's `get_context_data()`, or write the address in the template.

## An action on one part of the record

1. Put the panel that shows that part in its block, drawn with [`c-overview.panel`](../reference/components.md#c-overviewpanel), and give the panel the action's address as `edit_url`. The panel draws it as its Edit control, beside its "See all" link.

   ```django
   {% block overview.properties %}
     <c-overview.panel title="Properties"
                       edit_url="{% if can_manage %}{{ properties_url }}{% endif %}"
                       edit_text="Edit properties">
       …
     </c-overview.panel>
   {% endblock overview.properties %}
   ```

2. Inside any other element, draw [`c-overview.edit`](../reference/components.md#c-overviewedit) with the address. It draws nothing when the address is empty, so leave it empty for anyone who may not use the action.

3. Open the record as someone who may change it, and as a visitor.

## The result

The team sees your action where the part it changes is shown, and a visitor sees none. The shared parts already carry theirs: the header's Edit and the keywords' Edit, Edit on the descriptions, key dates and identifiers, Manage on People, and Delete as the last line of the Details panel.
