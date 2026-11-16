# How to show part of a page to a record's team

A template on a record's page often shows something only to the people who work on the record, such as an edit link. You ask the template tag `holds_level` whether the viewer holds a level on the record, and the template needs no view code to work out the answer.

## Before you start

The record must be a project, dataset, sample or measurement. The levels are `"view"`, `"edit"` and `"manage"`, and each includes the ones before it. They are described in [Contribution levels and record access](../reference/contribution-levels-and-record-access.md).

## Steps

1. Load the library at the top of the template.

   ```django
   {% load plugin_tags %}
   ```

2. Ask for the level and store the answer.

   ```django
   {% holds_level "edit" object as can_edit %}
   ```

   On a plugin page, `object` is the record. Use `base_object` when your view has an object of its own.

3. Show the part only when the answer is true.

   ```django
   {% if can_edit %}
     <a href="{% plugin_url 'contribution-list' %}">Manage contributors</a>
   {% endif %}
   ```

4. If you need the same answer in Python, call the function.

   ```python
   from fairdm.plugins import holds_level

   if holds_level(request, "edit", record):
       ...
   ```

## The result

The part appears for people who hold the level and is left out for everyone else.

The answer follows the rule the record's own pages use: the `view_<model>`, `change_<model>` or `delete_<model>` permission that the level stands for. A level held on a record above counts, such as a dataset's team on the dataset's samples, and so does a portal role that holds the permission for the whole portal.

Check these limits before you rely on the tag:

- A visitor who is not signed in holds no level, on a public record as on a private one. The tag tells you who is on the record's team, not who may read the record.
- The tag is `False` for anything that is not a project, dataset, sample or measurement.
- A level that does not exist raises `ValueError`, so a mistyped one is found the first time the template renders.
- The tag decides what a page shows. It never decides who may open another page. A link it hides still leads somewhere, and that page needs its own `check` or `permission`. See [How to restrict a plugin to some users](restrict-a-plugin-to-some-users.md).

The answer for a record is remembered for the rest of the request. Ask about the record the page belongs to. For a list of records, work the answers out in the view. The tag is described in [Template tags](../reference/template-tags.md).
