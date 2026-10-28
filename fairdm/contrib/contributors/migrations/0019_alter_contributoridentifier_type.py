import controlled_vocabularies.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributors', '0018_claiming_audit_log'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contributoridentifier',
            name='type',
            field=controlled_vocabularies.fields.ConceptField(collection='https://w3id.org/fairdm/vocabularies/identifier-types/contributor', help_text='The kind of identifier, from the contributor identifier types.', related_name='+', verbose_name='type', vocabulary=('https://w3id.org/fairdm/vocabularies/identifier-types',)),
        ),
    ]
