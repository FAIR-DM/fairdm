# Contribution levels and record access

This page lists the classes, functions and querysets that turn a contribution level into a permission answer on a project, dataset, sample or measurement: `ContributionLevel`, `REQUIRED_LEVEL`, `RecordAccess`, `RecordLevelBackend`, the queryset methods `with_level`, `accessible_to` and `visible_to`, and `ManagerOnlyFieldsMixin`. It does not explain why access works this way, which is in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) and in [ADR 0025](../../adr/0025-a-level-on-the-contribution-decides-rights-over-a-core-record.md), or the methods that change a level, which are in [Crediting](crediting.md).

## ContributionLevel

`ContributionLevel` is an `IntegerChoices` in `fairdm.contrib.contributors.choices`. Each level includes the ones before it, and the values are integers so that "at least this level" is a comparison. A level is stored in `Contribution.level`.

| Name | Value | Label | Lets its holder |
|---|---|---|---|
| `VIEW` | 1 | Can view | Open the record |
| `EDIT` | 2 | Can edit | Also change the record and the data in it |
| `MANAGE` | 3 | Can manage | Also change its contributors and their levels, change its visibility and delete it |

`Contribution.level` is empty for an organization, which holds no level, and may be empty for a person credited without one. A level on a project applies to its datasets. A level on a dataset applies to its samples and measurements. A measurement follows its own dataset, not its sample's.

## REQUIRED_LEVEL

`fairdm.contrib.contributors.access.REQUIRED_LEVEL` maps each permission codename that a core record type declares to the level that carries it. A codename that is not in the mapping is refused.

| Level | Codenames |
|---|---|
| `VIEW` | `view_project`, `view_dataset`, `view_sample`, `view_measurement` |
| `EDIT` | `add_` and `change_` for each of `project`, `dataset`, `sample` and `measurement`, and `import_data`, `modify_metadata`, `change_project_metadata`, `change_dataset_metadata` |
| `MANAGE` | `delete_` for each of the four models, and `add_contributor`, `modify_contributor`, `change_project_settings`, `change_dataset_settings`, `can_publish` |

A registered type's own default permissions, such as `plants.view_plantsample`, are read as the core model's. A permission that your own record type adds in `Meta.permissions` must be added to `REQUIRED_LEVEL` with the level that carries it, or it is refused.

## RecordAccess

`RecordAccess(record)` answers what people may do on one record from the levels on its contributions. `record` is a project, dataset, sample or measurement of any registered type. It is in `fairdm.contrib.contributors.access`.

| Member | Returns | What it does |
|---|---|---|
| `RecordAccess.is_core_model(model)` | `bool` | Whether `model` is one of the four core models. A registered subtype is not |
| `RecordAccess.is_core_record(obj)` | `bool` | Whether `obj` is an instance of one of the four core models or a registered subtype. `None` gives `False` |
| `RecordAccess.key(record)` | `(content_type_id, object_id)` | The pair that names a record on a contribution. A polymorphic record is resolved to its real type first |
| `model` | Property, model class | The core model the record belongs to, whatever its registered type |
| `kind` | Property, `str` | The verbose name of that model: `project`, `dataset`, `sample` or `measurement` |
| `above` | Cached property, `list` | The records this one takes levels from, nearest first. A sample's list is its dataset and that dataset's project |
| `required_level(perm)` | `ContributionLevel` or `None` | The level `perm` needs on the record. `perm` may carry its app label or not. `None` for a permission the mapping does not know |
| `level_of(user)` | `ContributionLevel` or `None` | The highest level the user holds on the record or any record above it. `None` for a visitor, an inactive user and anyone who holds no level. Reads the record and the records above it in one query |
| `levels_held(person_id)` | `list` of `(record, level)` | Every level the person holds on the record or above it |
| `levels_for(person_ids)` | `dict` | The `levels_held` result for each of several people, in one query |
| `own_level(person, held=None)` | `ContributionLevel` or `None` | The level the person holds from being listed on this record. Pass the `levels_for` result as `held` to skip a query |
| `level_from_above(person, held=None)` | `(level, record)` | The highest level the person holds from a record above, and that record. `(None, None)` when there is none |
| `people_above()` | `list` of `(person, level, source)` | Everyone who holds a level from a record above, at the highest they hold, ordered by name |
| `managers()` | `set` of person ids | The people who can sign in and hold the manage level on the record or above it. A holder of a portal role does not count |
| `can_manage(user)` | `bool` | Whether the user holds the manage level on the record or above it, or holds `change_<model>` for the whole portal, as a superuser and a Data Curator do. A visitor and an inactive user give `False` |
| `refuse_move_without_manager(parent_field)` | `None` | Raises `ValidationError` with the code `no_manager`, attached to `parent_field`, when a change of parent would leave a record that had someone who can manage it with nobody. `parent_field` is `"project"` for a dataset and `"dataset"` for a sample or measurement. A new record, a record whose parent did not change and a record that had no manager are never refused |
| `on_chain(include_record=...)` | `(queryset, keys)` | The contributions with a level on the record and the records above it, or on the records above alone. Used by the methods above |

`Dataset.clean`, `Sample.clean` and `Measurement.clean` call `refuse_move_without_manager`.

```python
from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel

access = RecordAccess(sample)

access.above                       # [dataset, project]
access.level_of(request.user)      # ContributionLevel.EDIT, for example, or None
access.can_manage(request.user)
access.required_level("sample.change_sample")   # ContributionLevel.EDIT

level = RecordAccess(dataset).level_of(request.user)
may_edit = level is not None and level >= ContributionLevel.EDIT
```

## Permission backends

The `AUTHENTICATION_BACKENDS` that `fairdm.setup()` provides, in order:

| Backend | Answers |
|---|---|
| `django.contrib.auth.backends.ModelBackend` | Model-level permissions that were granted to the user or their groups |
| `allauth.account.auth_backends.AuthenticationBackend` | Sign-in by email address |
| `fairdm.core.permissions.PolymorphicObjectPermissionBackend` | Stored django-guardian rows for models other than the four core ones. It normalises a polymorphic instance to its base before the check. For a core record it answers `False`, so a stored row grants nothing there |
| `fairdm.contrib.contributors.permissions.OrganizationPermissionBackend` | `manage_organization` on an organization. See [Contributor models](contributor-models.md#management-of-an-organization) |
| `fairdm.contrib.contributors.permissions.RecordLevelBackend` | Every `has_perm(perm, record)` question about a core record of any registered type |
| `fairdm.permissions.PortalRolePermissionBackend` | Object-level questions for a permission held through a shipped portal role. See [Portal roles in code](portal-roles.md) |

`RecordLevelBackend` grants a permission when the user's level on the record, or on a record above it, is at least the level `REQUIRED_LEVEL` gives the permission. It refuses an inactive user and a visitor. For an object that is not a core record, or a question with no object, it returns `False` and the other backends answer.

```python
user.has_perm("dataset.change_dataset", dataset)        # edit level or above
user.has_perm("plants.delete_plantsample", plant_sample)  # manage level or above
```

A permission stored with django-guardian for a project, dataset, sample or measurement grants nothing. For other models the stored rows work as usual. See [How to grant object permissions on a polymorphic model](../how-to/grant-object-permissions-on-polymorphic-models.md).

## Queryset methods

The querysets of the four core models take their level methods from `fairdm.core.managers.RecordLevelMixin`. `ProjectQuerySet`, `DatasetQuerySet`, `SampleQuerySet` and `MeasurementQuerySet` mix it in.

| Method | Returns | What it does |
|---|---|---|
| `with_level(user, level)` | Queryset | The records on which the user holds at least `level`, on the record itself or from a record above, in one query. An empty queryset for `None`, a visitor and an inactive user |
| `accessible_to(user, level)` | Queryset | `with_level(user, level)`, plus every record when the user holds the portal-wide right for the model. That right is `view_<model>` for `VIEW` and `change_<model>` for `EDIT` and `MANAGE`. A superuser and a Data Curator hold it. Choice lists and filters offer what this returns |
| `visible_to(user)` | Queryset | On the sample and measurement querysets only. The records of released datasets (public and published), and the records the user holds `VIEW` on. A user who holds `view_dataset` or `change_dataset` for the whole portal sees every record. A visitor sees released records only |

Two more methods keep a public listing to public records:

| Method | On | Keeps |
|---|---|---|
| `get_visible()` | `ProjectQuerySet` | Projects whose visibility is public |
| `get_visible()` | `DatasetQuerySet` | Public datasets that are not inside a private project |

`Dataset.objects` leaves out private datasets. Use `Dataset.all_objects` when a query must reach them.

```python
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import Dataset
from fairdm.core.sample.models import Sample

Dataset.all_objects.with_level(request.user, ContributionLevel.EDIT)
Dataset.all_objects.accessible_to(request.user, ContributionLevel.EDIT)
Sample.objects.visible_to(request.user)
```

Use these querysets in your own views and filters in place of django-guardian's `get_objects_for_user`, which finds nothing for the four core models.

## ManagerOnlyFieldsMixin

`fairdm.core.forms.ManagerOnlyFieldsMixin` leaves the fields that decide who gets into a record out of a form for anyone who cannot manage the record. A form for a record that does not exist yet leaves nothing out.

| Member | Type | What it does |
|---|---|---|
| `manager_only_fields` | `tuple` of field names, default `()` | The fields to leave out |
| `withhold_manager_only_fields(request)` | Method | Removes those fields from `self.fields` unless `RecordAccess(self.instance).can_manage(request.user)` is true. A `request` of `None` counts as someone who cannot manage |

Call `withhold_manager_only_fields` once the form's fields exist. The shipped forms set:

| Form | `manager_only_fields` |
|---|---|
| `ProjectForm` | `visibility`, `owner` |
| `DatasetForm` | `visibility`, `project` |
| `SampleFormMixin` | `dataset` |
| `MeasurementFormMixin` | `dataset` |

`ProjectForm` and `DatasetForm` take the request as a `request` keyword. `SampleFormMixin` and `MeasurementFormMixin` do the same for `dataset`. See [Form and filter mixins](form-and-filter-mixins.md).

## Related pages

- [Crediting](crediting.md) lists `Crediting`, the one place a record's contributors change.
- [Template tags](template-tags.md) lists `holds_level`, which shows part of a page to a record's team.
- [Portal roles](../../administrators/reference/portal-roles.md) lists the portal-wide rights that add to a level.
