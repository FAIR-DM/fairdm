# How to add an entry to the Manage menu

The Manage menu in a record's header lists the editing pages the viewer may use. You add an entry of your own when a record has an action that belongs there, such as importing data into it.

## Before you start

You need the template of the page you are changing. For a sample or measurement type this is the type's own overview template, described in [How to give a sample or measurement type its own overview page](give-a-sample-or-measurement-type-its-own-overview-page.md). The menu is described in [Record editing pages](../reference/record-editing-pages.md#the-manage-menu).

## Steps

1. In the template, fill the `overview.manage` block.

2. Draw [`c-actions.manage`](../reference/components.md#c-actionsmanage) with the shared entries, passed as `manage_menu`, and put your own `c-menu.item` entries in its slot.

   ```django
   {% block overview.manage %}
     <c-actions.manage :entries="manage_menu">
       <c-menu.item text="Import data" icon="upload" href="{{ import_url }}" />
     </c-actions.manage>
   {% endblock overview.manage %}
   ```

3. Supply `import_url` from the plugin's `get_context_data()`, or write the address in the template.

4. Put any button that belongs before the menu in the same block, ahead of the component.

5. Open the record as someone who may change it.

## The result

Your entry sits in the same menu as the shared ones, after them. The menu is drawn when the slot has content even if the person has none of the shared pages. The project and dataset templates already fill `overview.manage` to put Add dataset or Publish before the menu, so to add an entry to those pages, copy that block and add your item to the slot.
