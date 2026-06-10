from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0043_contract_type_numbering_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='contract_number',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
    ]
