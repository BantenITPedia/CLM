from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0009_seed_sales_agreement_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='contractdocument',
            name='version',
            field=models.PositiveIntegerField(default=1, help_text='Document version number for this contract'),
        ),
        migrations.AddField(
            model_name='contractdocument',
            name='is_current',
            field=models.BooleanField(default=True, help_text='Whether this is the latest document version'),
        ),
    ]
