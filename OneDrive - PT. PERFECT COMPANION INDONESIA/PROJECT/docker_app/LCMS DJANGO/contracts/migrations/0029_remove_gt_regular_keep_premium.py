# Migration to remove GENERAL_TRADE_REGULAR type

from django.db import migrations
from contracts.models import ContractType


def remove_gt_regular(apps, schema_editor):
    """Remove GENERAL_TRADE_REGULAR type"""
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    ContractTypeDefinition.objects.filter(code='GENERAL_TRADE_REGULAR').delete()


def add_gt_regular(apps, schema_editor):
    """Re-add GENERAL_TRADE_REGULAR type for reverse"""
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    ContractTypeDefinition.objects.update_or_create(
        code='GENERAL_TRADE_REGULAR',
        defaults={
            'name': 'General Trade Agreement - Regular',
            'description': 'Standard general trade agreement for regular customers',
            'is_template_based': True,
            'active': True,
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0027_add_gt_regular_premium_types'),
    ]

    operations = [
        migrations.RunPython(remove_gt_regular, add_gt_regular),
    ]
