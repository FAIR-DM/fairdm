from django.db import migrations


def cleanup_duplicate_types(apps, schema_editor):
    ContributorIdentifier = apps.get_model("contributors", "ContributorIdentifier")
    db_alias = schema_editor.connection.alias

    total_deleted = 0

    from django.db.models import Count
    duplicates = (
        ContributorIdentifier.objects.using(db_alias)
        .values("related", "type")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )

    for dup in duplicates:
        instances = ContributorIdentifier.objects.using(db_alias).filter(
            related_id=dup["related"],
            type=dup["type"],
        ).order_by("-modified")
        
        instances_to_delete = instances[1:]
        count = instances_to_delete.count()
        if count > 0:
            instances_to_delete.delete()
            total_deleted += count
            print(
                f"  Deleted {count} duplicate ContributorIdentifier "
                f"(related_id={dup['related']}, type={dup['type']})"
            )
    
    if total_deleted > 0:
        print(f"Total duplicates removed: {total_deleted}")
    else:
        print("No duplicates found - database is clean!")


class Migration(migrations.Migration):

    dependencies = [
        ("contributors", "0005_alter_contributor_profile"),
    ]

    operations = [
        migrations.RunPython(cleanup_duplicate_types, migrations.RunPython.noop),
    ]
