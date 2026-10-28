# The branch's schema changes for the sample record, squashed into one file (Article IX).
# The status data migration stays standalone, which the same article exempts.

import controlled_vocabularies.fields
import shortuuid.django_fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sample', '0006_alter_sample_local_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sample',
            name='status',
            field=controlled_vocabularies.fields.ConceptField(default='https://w3id.org/fairdm/vocabularies/sample-status/unknown', help_text='The current custody status of the physical specimen.', related_name='+', verbose_name='status', vocabulary=('https://w3id.org/fairdm/vocabularies/sample-status',)),
        ),
        migrations.AlterField(
            model_name='sample',
            name='uuid',
            field=shortuuid.django_fields.ShortUUIDField(alphabet=None, editable=False, help_text='A unique identifier generated automatically when the sample is created. It cannot be edited.', length=22, max_length=23, prefix='s', unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='sampleidentifier',
            name='type',
            field=controlled_vocabularies.fields.ConceptField(collection='https://w3id.org/fairdm/vocabularies/identifier-types/sample', help_text='The kind of identifier, from the sample identifier types.', related_name='+', verbose_name='type', vocabulary=('https://w3id.org/fairdm/vocabularies/identifier-types',)),
        ),
    ]
