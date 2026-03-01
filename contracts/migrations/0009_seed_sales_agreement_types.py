from django.db import migrations


def seed_sales_agreement_types(apps, schema_editor):
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')

    sales_types = [
        ('GENERAL_TRADE', 'General Trade Agreement'),
        ('MODERN_TRADE', 'Modern Trade Agreement'),
        ('DISTRIBUTOR', 'Distributor Agreement'),
    ]

    for code, name in sales_types:
        ContractTypeDefinition.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'active': True,
                'is_template_based': True,
                'description': f'{name} (template-based sales agreement)',
            }
        )


def unseed_sales_agreement_types(apps, schema_editor):
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    ContractTypeDefinition.objects.filter(
        code__in=['GENERAL_TRADE', 'MODERN_TRADE', 'DISTRIBUTOR']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0008_sales_agreement_targets'),
    ]

    operations = [
        migrations.RunPython(seed_sales_agreement_types, unseed_sales_agreement_types),
    ]
