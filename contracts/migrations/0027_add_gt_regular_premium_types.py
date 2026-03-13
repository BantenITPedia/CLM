# Generated migration for GT Regular and Premium contract types

from django.db import migrations
from contracts.models import ContractType


def seed_gt_variants(apps, schema_editor):
    """Create ContractTypeDefinition entries for GT Regular and Premium variants"""
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    
    # GT Regular
    ContractTypeDefinition.objects.update_or_create(
        code=ContractType.GENERAL_TRADE_REGULAR,
        defaults={
            'name': 'General Trade Agreement - Regular',
            'description': 'Standard general trade agreement for regular customers',
            'is_template_based': True,
            'active': True,
        }
    )
    
    # GT Premium
    ContractTypeDefinition.objects.update_or_create(
        code=ContractType.GENERAL_TRADE_PREMIUM,
        defaults={
            'name': 'General Trade Agreement - Premium',
            'description': 'Premium general trade agreement with enhanced terms and benefits',
            'is_template_based': True,
            'active': True,
        }
    )


def reverse_gt_variants(apps, schema_editor):
    """Remove GT Regular and Premium variants"""
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    ContractTypeDefinition.objects.filter(
        code__in=[ContractType.GENERAL_TRADE_REGULAR, ContractType.GENERAL_TRADE_PREMIUM]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0028_alter_contract_contract_type_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_gt_variants, reverse_gt_variants),
    ]
