from django.db import migrations, models


def seed_contract_type_configuration(apps, schema_editor):
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')

    gt_regular_product = (
        'Quarter (Triwulan) and Yearly (Tahunan): MEO, LUV CARE, NOVA dan produk-produk yang akan dirilis selanjutnya.\n\n'
        'Yearly only (Tahunan saja): CAT CHOIZE, DOG CHOIZE, CHEF CHOIZE, CUTIEZ, SANTAP, LEZATO, A-PRO, '
        'pasir kucing merek CAT COMFY dan produk-produk yang akan dirilis selanjutnya.'
    )
    gt_premium_product = (
        'Quarter (Triwulan) and Yearly (Tahunan): SmartHeart, Smart Heart Gold, Me-O Gold.'
    )

    gt_regular_incentive = (
        'D1 (9,750), D2 (4,875), D3 (1,950) with yearly, quarterly, and commodity-only sections.'
    )
    gt_premium_incentive = (
        'D1 (4,000), D2 (2,000), D3 (1,000) with yearly and quarterly non-commodity sections.'
    )

    regular = ContractTypeDefinition.objects.filter(code='GENERAL_TRADE').first()
    if regular:
        regular.number_prefix = '01'
        regular.number_company_code = regular.number_company_code or 'PCI'
        regular.number_department_code = regular.number_department_code or 'SALES'
        regular.product_scope_text = regular.product_scope_text or gt_regular_product
        regular.incentive_scheme_text = regular.incentive_scheme_text or gt_regular_incentive
        regular.save(update_fields=[
            'number_prefix',
            'number_company_code',
            'number_department_code',
            'product_scope_text',
            'incentive_scheme_text',
        ])

    premium = ContractTypeDefinition.objects.filter(code='GENERAL_TRADE_PREMIUM').first()
    if premium:
        premium.number_prefix = '02'
        premium.number_company_code = premium.number_company_code or 'PCI'
        premium.number_department_code = premium.number_department_code or 'SALES'
        premium.product_scope_text = premium.product_scope_text or gt_premium_product
        premium.incentive_scheme_text = premium.incentive_scheme_text or gt_premium_incentive
        premium.save(update_fields=[
            'number_prefix',
            'number_company_code',
            'number_department_code',
            'product_scope_text',
            'incentive_scheme_text',
        ])


def unseed_contract_type_configuration(apps, schema_editor):
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    ContractTypeDefinition.objects.filter(code='GENERAL_TRADE').update(number_prefix='')
    ContractTypeDefinition.objects.filter(code='GENERAL_TRADE_PREMIUM').update(number_prefix='')


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0042_seed_activity_notification_templates'),
    ]

    operations = [
        migrations.AddField(
            model_name='contracttypedefinition',
            name='incentive_scheme_text',
            field=models.TextField(blank=True, default='', help_text='Configurable incentive scheme text for templates (available as {{ incentive_scheme_text }}).'),
        ),
        migrations.AddField(
            model_name='contracttypedefinition',
            name='number_company_code',
            field=models.CharField(blank=True, default='PCI', help_text='Company segment in contract number format. Example: PCI', max_length=20),
        ),
        migrations.AddField(
            model_name='contracttypedefinition',
            name='number_department_code',
            field=models.CharField(blank=True, default='SALES', help_text='Department segment in contract number format. Example: SALES', max_length=20),
        ),
        migrations.AddField(
            model_name='contracttypedefinition',
            name='number_prefix',
            field=models.CharField(blank=True, default='', help_text='Contract number prefix for this type (e.g. 01, 02, 03). Leave blank to disable auto-numbering.', max_length=10),
        ),
        migrations.AddField(
            model_name='contracttypedefinition',
            name='product_scope_text',
            field=models.TextField(blank=True, default='', help_text='Configurable product scope text for templates (available as {{ product_scope_text }}).'),
        ),
        migrations.CreateModel(
            name='ContractNumberSequence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField()),
                ('month', models.PositiveSmallIntegerField()),
                ('last_number', models.PositiveIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contract_type', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='number_sequences', to='contracts.contracttypedefinition')),
            ],
            options={
                'indexes': [models.Index(fields=['contract_type', 'year', 'month'], name='contracts_co_contrac_8e2ec3_idx')],
                'unique_together': {('contract_type', 'year', 'month')},
            },
        ),
        migrations.RunPython(seed_contract_type_configuration, unseed_contract_type_configuration),
    ]
