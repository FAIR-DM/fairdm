from django.db import migrations
from django.db.models import Max

VIEW, EDIT, MANAGE = 1, 2, 3

CORE = {
    "project": ("project", "Project"),
    "dataset": ("dataset", "Dataset"),
    "sample": ("sample", "Sample"),
    "measurement": ("measurement", "Measurement"),
}
POLYMORPHIC = ("sample", "measurement")
GENERIC = {
    "import_data": EDIT,
    "modify_metadata": EDIT,
    "add_contributor": MANAGE,
    "modify_contributor": MANAGE,
    "can_publish": MANAGE,
}
ACTIONS = {"view": VIEW, "add": EDIT, "change": EDIT, "delete": MANAGE}
ANONYMOUS = "AnonymousUser"


def level_for(codename):
    if codename in GENERIC:
        return GENERIC[codename]
    if codename.endswith("_settings"):
        return MANAGE
    if codename.endswith("_metadata"):
        return EDIT
    return ACTIONS.get(codename.split("_", 1)[0])


def convert_stored_permissions(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    UserObjectPermission = apps.get_model("guardian", "UserObjectPermission")
    GroupObjectPermission = apps.get_model("guardian", "GroupObjectPermission")
    Person = apps.get_model("contributors", "Person")
    Contribution = apps.get_model("contributors", "Contribution")
    models = {kind: apps.get_model(*label) for kind, label in CORE.items()}

    kind_of = {}
    base_of = {}
    for kind, (app_label, model) in CORE.items():
        content_type = ContentType.objects.filter(
            app_label=app_label, model=model.lower()
        ).first()
        if content_type is not None:
            kind_of[content_type.pk] = kind
            base_of[kind] = content_type.pk
    for kind in POLYMORPHIC:
        for content_type_id in (
            models[kind]
            .objects.order_by()
            .values_list("polymorphic_ctype_id", flat=True)
            .distinct()
        ):
            kind_of[content_type_id] = kind

    best = {}

    def note(person_id, kind, object_pk, level):
        key = (person_id, kind, str(object_pk))
        best[key] = max(best.get(key, 0), level)

    members = {}
    user_rows = UserObjectPermission.objects.filter(content_type_id__in=kind_of)
    for row in user_rows.select_related("permission"):
        level = level_for(row.permission.codename)
        if level is not None:
            note(row.user_id, kind_of[row.content_type_id], row.object_pk, level)
    group_rows = GroupObjectPermission.objects.filter(content_type_id__in=kind_of)
    for row in group_rows.select_related("permission"):
        level = level_for(row.permission.codename)
        if level is None:
            continue
        if row.group_id not in members:
            members[row.group_id] = list(
                Person.groups.through.objects.filter(group_id=row.group_id).values_list(
                    "person_id", flat=True
                )
            )
        for person_id in members[row.group_id]:
            note(person_id, kind_of[row.content_type_id], row.object_pk, level)

    people = {
        person.pk: person
        for person in Person.objects.filter(
            pk__in={person_id for person_id, _kind, _pk in best}
        ).exclude(email=ANONYMOUS)
    }

    own_type = {}
    for kind in CORE:
        wanted = {pk for _person, found, pk in best if found == kind}
        if kind in POLYMORPHIC:
            found = (
                models[kind]
                .objects.filter(pk__in=wanted)
                .values_list("pk", "polymorphic_ctype_id")
            )
            own_type.update({(kind, str(pk)): ctype for pk, ctype in found})
        else:
            existing = (
                models[kind].objects.filter(pk__in=wanted).values_list("pk", flat=True)
            )
            own_type.update({(kind, str(pk)): base_of[kind] for pk in existing})

    held = {}
    for contribution in Contribution.objects.filter(content_type_id__in=kind_of):
        kind = kind_of[contribution.content_type_id]
        held[(contribution.contributor_id, kind, contribution.object_id)] = contribution
    top = Contribution.objects.aggregate(top=Max("order"))["top"]
    next_order = 0 if top is None else top + 1

    def credit_on(contributor_id, kind, object_id, content_type_id, level):
        nonlocal next_order
        credit = Contribution.objects.create(
            contributor_id=contributor_id,
            content_type_id=content_type_id,
            object_id=object_id,
            level=level,
            order=next_order,
        )
        next_order += 1
        held[(contributor_id, kind, object_id)] = credit
        return credit

    for (person_id, kind, object_pk), level in best.items():
        person = people.get(person_id)
        content_type_id = own_type.get((kind, object_pk))
        if person is None or content_type_id is None or person.is_superuser:
            continue
        existing = held.get((person_id, kind, object_pk))
        if existing is None:
            credit_on(person_id, kind, object_pk, content_type_id, level)
        elif (existing.level or 0) < level:
            existing.level = level
            existing.save(update_fields=["level"])

    person_ids = set(Person.objects.values_list("pk", flat=True))
    for (contributor_id, kind, object_id), contribution in list(held.items()):
        if contributor_id in person_ids and contribution.level is None:
            contribution.level = VIEW
            contribution.save(update_fields=["level"])
        if contributor_id in person_ids and contribution.affiliation_id is not None:
            key = (contribution.affiliation_id, kind, object_id)
            if key not in held:
                credit_on(
                    contribution.affiliation_id,
                    kind,
                    object_id,
                    contribution.content_type_id,
                    None,
                )

    user_rows.delete()
    group_rows.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("contributors", "0023_credited_from_set_null"),
        (
            "guardian",
            "0003_remove_groupobjectpermission_guardian_gr_content_ae6aec_idx_and_more",
        ),
        ("contenttypes", "0002_remove_content_type_name"),
        ("project", "0010_alter_projectdescription_value"),
        ("dataset", "0014_alter_datasetdescription_value"),
        ("sample", "0010_alter_sampledescription_value"),
        ("measurement", "0013_alter_measurementdescription_value"),
    ]

    operations = [
        migrations.RunPython(convert_stored_permissions, migrations.RunPython.noop),
    ]
