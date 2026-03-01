from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0007_populate_default_reminders'),
    ]

    operations = [
        migrations.AddField(
            model_name='contracttypedefinition',
            name='is_template_based',
            field=models.BooleanField(default=False, help_text='Whether this contract type uses template-based generation'),
        ),
        migrations.AddField(
            model_name='contract',
            name='is_draft_generated',
            field=models.BooleanField(default=False, help_text='Whether a draft has been generated from a template'),
        ),
        migrations.AddField(
            model_name='contract',
            name='draft_generated_at',
            field=models.DateTimeField(blank=True, help_text='Last time a draft was generated', null=True),
        ),
        migrations.CreateModel(
            name='ContractTarget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annual_target', models.DecimalField(decimal_places=2, help_text='Annual sales target value', max_digits=14)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contract', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='target', to='contracts.contract')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ContractQuarter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quarter_number', models.PositiveSmallIntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('target_amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quarters', to='contracts.contract')),
            ],
            options={
                'ordering': ['contract', 'quarter_number'],
                'unique_together': {('contract', 'quarter_number')},
            },
        ),
        migrations.AddIndex(
            model_name='contractquarter',
            index=models.Index(fields=['contract', 'quarter_number'], name='contract_quarter_idx'),
        ),
    ]
