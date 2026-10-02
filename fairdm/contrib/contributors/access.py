"""What a person may do on one project, dataset, sample or measurement, as a level.

Prototype. A level is read from, and written as, the record-level permissions the framework
already stores, so nothing new is persisted. See ``specs/022-record-contributors-and-access``.
"""

from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import get_user_perms, get_users_with_perms

from fairdm.core.utils import assign_perm, get_non_polymorphic_instance, remove_perm

VIEW, EDIT, MANAGE = "view", "edit", "manage"

#: Lowest first. Each level includes the ones before it.
LEVELS = (VIEW, EDIT, MANAGE)

LEVEL_LABELS = {
    VIEW: _("Can view"),
    EDIT: _("Can edit"),
    MANAGE: _("Can manage"),
}

#: The stored permission that marks each level, as a prefix to the record type's name.
LEVEL_ACTIONS = {VIEW: "view", EDIT: "change", MANAGE: "delete"}


def record_type(record):
    """Return the core model a record belongs to, whatever registered type it is."""
    return getattr(record, "type_of", None) or type(record)


def stored(record):
    """Return the instance record-level permissions are stored against."""
    if type(record) is not record_type(record):
        return get_non_polymorphic_instance(record)
    return record


def level_from(codenames, record):
    """Return the highest level a set of permission codenames amounts to, or None."""
    name = record_type(record)._meta.model_name
    held = None
    for level in LEVELS:
        if f"{LEVEL_ACTIONS[level]}_{name}" in codenames:
            held = level
    return held


def own_level(person, record):
    """Return the level a person holds from being listed on the record itself, or None."""
    return level_from(set(get_user_perms(person, stored(record))), record)


def set_level(person, record, level):
    """Give a person exactly ``level`` on the record, or nothing when ``level`` is None."""
    name = record_type(record)._meta.model_name
    wanted = LEVELS[: LEVELS.index(level) + 1] if level else ()
    for each in LEVELS:
        codename = f"{LEVEL_ACTIONS[each]}_{name}"
        if each in wanted:
            assign_perm(codename, person, record)
        else:
            remove_perm(codename, person, record)


def records_above(record):
    """Return the records a record takes rights from, nearest first."""
    above = []
    parent = getattr(record, "dataset", None) or getattr(record, "project", None)
    while parent is not None:
        above.append(parent)
        parent = getattr(parent, "project", None)
    return above


def level_from_above(person, record):
    """Return the highest level a person holds from a record above, and that record."""
    best, source = None, None
    for parent in records_above(record):
        level = own_level(person, parent)
        if level and (best is None or LEVELS.index(level) > LEVELS.index(best)):
            best, source = level, parent
    return best, source


def higher(first, second):
    """Return the higher of two levels, either of which may be None."""
    ranked = [level for level in (first, second) if level]
    return max(ranked, key=LEVELS.index) if ranked else None


def has_account(person):
    """Say whether a person can sign in and act."""
    signed_in_before = person.is_claimed or person.has_usable_password()
    return bool(person.is_active and person.email and signed_in_before)


def people_above(record):
    """Return ``(person, level, source)`` for everyone holding a level from a record above."""
    found = {}
    for parent in records_above(record):
        holders = get_users_with_perms(
            stored(parent),
            attach_perms=True,
            with_superusers=False,
            with_group_users=False,
        )
        for person, codenames in holders.items():
            level = level_from(set(codenames), parent)
            if not level:
                continue
            known = found.get(person.pk)
            if known is None or LEVELS.index(level) > LEVELS.index(known[1]):
                found[person.pk] = (person, level, parent)
    return sorted(found.values(), key=lambda entry: str(entry[0]))


def managers(record):
    """Return the ids of the people who count as able to manage a record.

    A person counts when they can sign in and hold the manage level on the record or on a record
    above it. Holders of portal roles do not count.
    """
    ids = set()
    for each in [record, *records_above(record)]:
        holders = get_users_with_perms(
            stored(each),
            attach_perms=True,
            with_superusers=False,
            with_group_users=False,
        )
        for person, codenames in holders.items():
            if level_from(set(codenames), each) == MANAGE and has_account(person):
                ids.add(person.pk)
    return ids


def can_manage(user, record):
    """Say whether a user may change a record's contributors."""
    if not user.is_authenticated or not user.is_active:
        return False
    model = record_type(record)._meta
    if user.is_superuser or user.has_perm(
        f"{model.app_label}.delete_{model.model_name}"
    ):
        return True
    return higher(own_level(user, record), level_from_above(user, record)[0]) == MANAGE
