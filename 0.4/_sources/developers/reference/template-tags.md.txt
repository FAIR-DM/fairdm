# Template tags

This page lists the template tags and filters that FairDM ships, in three tag libraries. Each entry gives the tag's form, its arguments, what it returns and what it does when something is missing. It does not cover the Cotton components, which are on [Components](components.md), or the tags of the packages FairDM installs, such as Django's own, which are in the [Django documentation](https://docs.djangoproject.com/en/stable/ref/templates/builtins/).

A template loads a library before it uses the library's tags:

```django
{% load fairdm plugin_tags contributor_tags %}
```

| Library | Holds |
|---|---|
| [`fairdm`](#the-fairdm-library) | Markdown, units, the registry, fields and permissions |
| [`plugin_tags`](#the-plugin_tags-library) | Plugin addresses and the viewer's level on a record |
| [`contributor_tags`](#the-contributor_tags-library) | Contributions, roles and contributor names |

The functions behind the tags, with their docstrings, are in {py:mod}`fairdm.templatetags.fairdm`, {py:mod}`fairdm.contrib.plugins.templatetags.plugin_tags` and {py:mod}`fairdm.contrib.contributors.templatetags.contributor_tags`.

A tag written `{% name ... %}` returns its value into the page. Add `as variable` to keep the value in a variable instead, as for any Django simple tag. A filter is written `{{ value|name }}` or `{{ value|name:"argument" }}`.

## The `fairdm` library

### `is_active`

```django
{% is_active "/datasets/" %}
```

- **Arguments**: `url`, a path prefix.
- **Returns**: `"active"` when the current request's path starts with `url`, and `""` otherwise.
- **Needs**: `request` in the template context. Without it the tag raises `KeyError`.

### `notation`

```django
{{ description.type|notation }}
```

- **Value**: a vocabulary concept, such as the `type` of a description or a date, or `None`.
- **Returns**: the concept's `skos:notation`, the code it was stored as before it had an address. For the terms DataCite also lists, such as the description and contributor types, that is DataCite's own value. An empty string when there is no concept or it has no notation.

### `unit`

```django
{{ "m/s"|unit }}
```

- **Value**: a unit name that the unit library understands, such as `"m"` or `"g/cm**3"`, or a unit object.
- **Returns**: the unit written as HTML with its symbols.
- **Raises**: `UndefinedUnitError` for a name the unit library does not know. Any value that is neither a string nor a unit makes the filter fail with `UnboundLocalError`.

### `get_registry_info`

```django
{% get_registry_info object as info %}
```

- **Arguments**: a model class, a model instance or a queryset.
- **Returns**: the [registry](registry.md) configuration of the model, or `None` when the model is not registered. Python code calls `registry.get_for_model()`, which raises for an unregistered model instead.

### `display_url`

```django
{% display_url "https://www.example.org/data" %}
```

- **Arguments**: `url`, a string.
- **Returns**: the address with `https://`, `http://` and `www.` removed, for showing as link text. Here, `example.org/data`.

### `get_field`

```django
{% get_field object "rock_type" as field %}{{ field.verbose_name }}
```

- **Arguments**: `obj`, a model instance or class, and `fname`, a field name.
- **Returns**: the model field, or `None` when the model has no field of that name.

### `get_field_and_value`

```django
{% get_field_and_value object "rock_type" as pair %}{{ pair.field.verbose_name }}: {{ pair.value }}
```

- **Arguments**: `obj`, a model instance, and `fname`, a field name.
- **Returns**: a dictionary with `field`, the model field, and `value`, the instance's value for it.
- **Raises**: `FieldDoesNotExist` when the model has no field of that name.

### `get_fields`

```django
{% get_fields object field_names as pairs %}
{% for field, value in pairs %}{{ field.verbose_name }}: {{ value }}{% endfor %}
```

- **Arguments**: `obj`, a model instance, and `fields`, a list of field names from the context.
- **Returns**: a list of `(field, value)` pairs in the order of `fields`.
- **Raises**: `FieldDoesNotExist` for a name the model does not have.

### `edit_url`

```django
{% edit_url object %}
```

- **Arguments**: `obj`, a model instance with a `uuid`, and `fields`, an optional list of field names.
- **Returns**: the address of the URL named `<model name>-update`, with `?fields=` and the names joined by commas when `fields` is given.
- **Raises**: `NoReverseMatch` for every FairDM model, because FairDM defines no URL with a name of that form. Use [`plugin_url`](#plugin_url) with the name of an editing page instead, as [Record editing pages](record-editing-pages.md) lists.

### `avatar_url`

```django
{% avatar_url person %}
```

- **Arguments**: `contributor`, a person or organization, or `None`.
- **Returns**: the address of the contributor's uploaded image. When the contributor is `None` or has no image, it returns the markup of FairDM's default person icon, an `<svg>` element, not an address.

To draw a contributor's picture, use the [`c-contributor.avatar`](components.md) component, which picks the right size and falls back to initials.

### `plugin_url` in `fairdm`

The `fairdm` library holds a copy of [`plugin_url`](#plugin_url) from `plugin_tags`, and it behaves the same. Load it from `plugin_tags`.

### `safe_markdown`

```django
{{ project.description|safe_markdown }}
```

- **Value**: markdown text.
- **Returns**: the HTML, sanitised and marked safe, so the template does not escape it again. The extensions applied are those in [`FAIRDM_MARKDOWN_EXTENSIONS`](settings.md#fairdm_markdown_extensions). The editor's live preview uses the same function, so what a person previews is what the page shows.

[How to render markdown in a template](../how-to/render-markdown-in-a-template.md) uses it, and [How markdown is sanitised](../explanation/how-markdown-is-sanitised.md) explains what is removed.

### `has_perms`

```django
{% if perms_list|has_perms:"project.change_project,project.delete_project" %}...{% endif %}
```

- **Value**: a collection of permission names, such as a list from the context.
- **Argument**: permission names separated by commas, with no spaces.
- **Returns**: `True` when the collection holds at least one of them.

### `has_permission`

```django
{% has_permission "dataset.change_dataset" as may_edit %}
```

- **Arguments**: permission names separated by commas, with no spaces.
- **Returns**: `True` when `user_permissions` in the template context holds one of them, or, failing that, when `user` holds one of them for the whole portal. It does not ask about a particular record. To ask whether the viewer may work on a record, use [`holds_level`](#holds_level).

### `get_related_field`

```django
{% get_related_field sample "dataset__project__name" as found %}
```

- **Arguments**: `obj`, a model instance, and `field_name`, a path of attribute names joined by double underscores.
- **Returns**: a pair: the object that holds the last attribute, and the name of that attribute. It does not return the value. Here it returns the project and `"name"`. When an object part-way along the path is `None`, it returns `(None, None)`.
- **Raises**: `AttributeError` when a name before the last does not exist.

## The `plugin_tags` library

### `plugin_url`

```django
{% plugin_url "contribution-list" %}
{% plugin_url "edit" %}
```

- **Arguments**: `view_name`, the URL name of a [plugin](plugins.md) page, then any positional or keyword arguments the address takes.
- **Returns**: the address of that page for the record in the context. The record is `non_polymorphic_object` when the context holds it, and otherwise `object`. The arguments the record's addressing needs, such as its `uuid`, are filled in from the record. Returns `""` when the context holds neither.
- **Raises**: `NoReverseMatch` when the record's type has no page of that name.

The Python function behind it is `fairdm.contrib.plugins.utils.reverse`, on [Plugins](plugins.md#reverse).

### `holds_level`

```django
{% holds_level "edit" object as can_edit %}
{% if can_edit %}<a href="{% plugin_url 'edit' %}">Edit</a>{% endif %}
```

- **Arguments**: `level`, one of `"view"`, `"edit"` or `"manage"`, and `record`, a project, dataset, sample or measurement.
- **Returns**: `True` when the viewer holds that level on the record or a higher one, through a contribution on the record, on a record above it or for the whole portal. `False` for a visitor who is not signed in, for a record that is none of the four, and when the context holds no `request`.
- **Raises**: `ValueError` for any other level.

The answer is the one the record's own pages are opened with. [Contribution levels and record access](contribution-levels-and-record-access.md) lists what each level allows, and [How to show part of a page to a record's team](../how-to/show-part-of-a-page-to-a-records-team.md) uses the tag.

## The `contributor_tags` library

### `by_role`

```django
{{ dataset.contributors.all|by_role:"https://w3id.org/fairdm/vocabularies/contributor-roles/creator,https://w3id.org/fairdm/vocabularies/contributor-roles/contact-person" }}
```

- **Value**: a queryset of contributions.
- **Argument**: role addresses separated by commas, or a list of addresses. A role's address is its concept's URI in the contributor roles vocabulary, such as `https://w3id.org/fairdm/vocabularies/contributor-roles/creator`.
- **Returns**: the contributions that hold at least one of the roles. With no argument, the queryset unchanged.

### `has_role`

```django
{% if contribution|has_role:"https://w3id.org/fairdm/vocabularies/contributor-roles/contact-person" %}...{% endif %}
```

- **Value**: one contribution.
- **Argument**: role addresses separated by commas, or a list of addresses. A role's address is its concept's URI in the contributor roles vocabulary, such as `https://w3id.org/fairdm/vocabularies/contributor-roles/creator`.
- **Returns**: `True` when the contribution holds one of the roles. With no argument it returns the contribution itself, which a template reads as true.

### `as_contributor`

```django
{% with person=contribution|as_contributor %}{{ person.name }}{% endwith %}
```

- **Value**: a contribution, a contributor or `None`.
- **Returns**: the person or organization behind a contribution, or the contributor itself. A plain contributor is turned into its person or organization. Returns `None` for `None` and for a contribution whose contributor was deleted.

### `as_contributors`

```django
{% for contributor in dataset.contributors.all|as_contributors %}...{% endfor %}
```

- **Value**: a list of contributions or contributors, or `None`.
- **Returns**: a list of persons and organizations, leaving out contributions whose contributor was deleted. `None` gives an empty list.

### `contributor_name`

```django
{% contributor_name person "family_given" %}
```

- **Arguments**: `contributor`, a person or organization, and `name_format`, an optional name format.
- **Returns**: the contributor's `name`. With a format, a person's name in that format, as for the `format` attribute of [`c-contributor.name`](components.md). An organization ignores the format. `None` gives `""`.

### `split_contributors`

```django
{% split_contributors dataset.contributors.all 3 as split %}
{% for contributor in split.shown %}...{% endfor %}
{% if split.more %}and {{ split.more }} more{% endif %}
```

- **Arguments**: `values`, contributions or contributors, `limit`, how many to show, where `0` shows everyone, and `total`, the real count when `values` is already cut short.
- **Returns**: a dictionary with `shown`, the contributors to name, `more`, how many are left out, and `total`. When only one would be left out, it names that one too, because a count takes as much room as the name.
