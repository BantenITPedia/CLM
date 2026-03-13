from django.db import migrations


DUPLICATE_KEY = 'party_b_representative_name'
GT_CODES = ['GENERAL_TRADE', 'GENERAL_TRADE_PREMIUM']


def remove_duplicate_gt_representative_name_field(apps, schema_editor):
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    ContractField = apps.get_model('contracts', 'ContractField')

    type_ids = list(
        ContractTypeDefinition.objects.filter(code__in=GT_CODES).values_list('id', flat=True)
    )
    if not type_ids:
        return

    ContractField.objects.filter(
        contract_type_id__in=type_ids,
        field_key=DUPLICATE_KEY,
    ).delete()


def restore_duplicate_gt_representative_name_field(apps, schema_editor):
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    ContractField = apps.get_model('contracts', 'ContractField')

    for contract_type in ContractTypeDefinition.objects.filter(code__in=GT_CODES):
        ContractField.objects.get_or_create(
            contract_type=contract_type,
            field_key=DUPLICATE_KEY,
            defaults={
                'label': 'Representative Name',
                'field_type': 'text',
                'required': True,
                'position': 18,
                'options': None,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0033_standardize_gt_regular_premium_names'),
    ]

    operations = [
        migrations.RunPython(
            remove_duplicate_gt_representative_name_field,
            restore_duplicate_gt_representative_name_field,
        ),
    ]
