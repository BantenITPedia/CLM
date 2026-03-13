# Migration to remove legacy manual contract number fields from ContractField
# Created on 2026-03-09

from django.db import migrations


def remove_manual_number_fields(apps, schema_editor):
    """Remove legacy manual contract number fields (no_contract, contract_number)"""
    ContractField = apps.get_model('contracts', 'ContractField')
    
    # Store deleted fields for potential rollback
    deleted = ContractField.objects.filter(
        field_key__in=['no_contract', 'contract_number']
    )
    
    # Delete the legacy manual number fields
    deleted.delete()


def restore_manual_number_fields(apps, schema_editor):
    """Restore legacy manual contract number fields for rollback"""
    ContractField = apps.get_model('contracts', 'ContractField')
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    
    # Restore no_contract field for GENERAL_TRADE if it exists
    gt_type = ContractTypeDefinition.objects.filter(code='GENERAL_TRADE').first()
    if gt_type:
        ContractField.objects.get_or_create(
            contract_type=gt_type,
            field_key='no_contract',
            defaults={
                'label': 'Nomor Contract',
                'field_type': 'text',
                'required': True,
                'position': 0,
            }
        )
    
    # Restore for GENERAL_TRADE_PREMIUM if needed
    gt_premium_type = ContractTypeDefinition.objects.filter(code='GENERAL_TRADE_PREMIUM').first()
    if gt_premium_type:
        ContractField.objects.get_or_create(
            contract_type=gt_premium_type,
            field_key='no_contract',
            defaults={
                'label': 'Nomor Contract',
                'field_type': 'text',
                'required': True,
                'position': 0,
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0031_contract_contract_number_and_more'),
    ]

    operations = [
        migrations.RunPython(remove_manual_number_fields, restore_manual_number_fields),
    ]
