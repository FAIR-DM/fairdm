# How to grant object permissions on a polymorphic model

A permission declared on a polymorphic base is stored under the base's content type, so django-guardian's own functions miss it when you give them a subclass instance. Use FairDM's helpers when your portal's code grants, removes, lists or looks up a stored permission on an organization or on a polymorphic model of your own.

## Before you start

- The helpers cover models that name their polymorphic base with `type_of`. `Contributor` does, so its subclasses `Person` and `Organization` are covered. A model of your own is covered when it declares `type_of` in the same way.
- Do not use them to give a person access to a project, dataset, sample or measurement. A permission stored for one of those four grants nothing. List the person as a contributor at the level they need instead. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) and [Contribution levels and record access](../reference/contribution-levels-and-record-access.md).
- Do not grant `manage_organization`. A person holds it through a current owner affiliation and no stored row is honoured.

## Steps

1. Import the helpers from `fairdm.core.utils` rather than from `guardian.shortcuts`:

    ```python
    from fairdm.core.utils import (
        assign_perm,
        get_objects_for_user,
        get_perms,
        remove_perm,
    )
    ```

2. Grant the permission to a person or a group. The permission is declared on `Contributor`, so it is stored against the base record even though you pass an `Organization`:

    ```python
    assign_perm("change_contributor", user, organization)
    ```

3. Check it with Django's usual call. Name the permission with its app label:

    ```python
    user.has_perm("contributors.change_contributor", organization)
    ```

4. List what a person or group holds on the record. The result merges rows stored against the subclass and against its base, and is sorted:

    ```python
    permissions = get_perms(user, organization)
    ```

5. Find the records a person holds a permission for. Name the permission after the subclass, here `change_organization`. The helper works out the base permission, `change_contributor`, and narrows your queryset by it:

    ```python
    from fairdm.contrib.contributors.models import Organization

    organizations = get_objects_for_user(
        user, "contributors.change_organization", Organization
    )
    ```

6. Take the permission away:

    ```python
    remove_perm("change_contributor", user, organization)
    ```

## The result

The permission is stored once, under the base's content type, and every call above reads and writes the same row. A call with guardian's own function would instead file the grant under `Organization`'s content type, where the permission declared on the base is never looked for.

The helpers retarget a record to its base only when the base declares the permission. A plain record that is not polymorphic, and a subclass permission such as `change_organization`, which the subclass owns, pass through unchanged.
