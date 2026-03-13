from django.db import migrations


REGULAR_TYPE_CODE = 'GENERAL_TRADE'
PREMIUM_TYPE_CODE = 'GENERAL_TRADE_PREMIUM'

REGULAR_TYPE_NAME = 'General Trade Agreement - Regular'
PREMIUM_TYPE_NAME = 'General Trade Agreement - Premium'

REGULAR_TEMPLATE_NAME = 'GT Regular Agreement Template'
PREMIUM_TEMPLATE_NAME = 'GT Premium Agreement Template'


def standardize_gt_names(apps, schema_editor):
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    ContractTemplate = apps.get_model('contracts', 'ContractTemplate')

    regular_type = ContractTypeDefinition.objects.filter(code=REGULAR_TYPE_CODE).first()
    if regular_type:
        regular_type.name = REGULAR_TYPE_NAME
        regular_type.description = 'Standard general trade agreement for regular customers'
        regular_type.save(update_fields=['name', 'description'])

    premium_type = ContractTypeDefinition.objects.filter(code=PREMIUM_TYPE_CODE).first()
    if premium_type:
        premium_type.name = PREMIUM_TYPE_NAME
        premium_type.description = 'Premium general trade agreement with enhanced terms and benefits'
        premium_type.save(update_fields=['name', 'description'])

    ContractTemplate.objects.filter(contract_type__code=REGULAR_TYPE_CODE).update(name=REGULAR_TEMPLATE_NAME)
    ContractTemplate.objects.filter(contract_type__code=PREMIUM_TYPE_CODE).update(name=PREMIUM_TEMPLATE_NAME)


def reverse_standardize_gt_names(apps, schema_editor):
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    ContractTemplate = apps.get_model('contracts', 'ContractTemplate')

    regular_type = ContractTypeDefinition.objects.filter(code=REGULAR_TYPE_CODE).first()
    if regular_type:
        regular_type.name = 'General Trade Agreement'
        regular_type.description = 'General Trade Agreement Template'
        regular_type.save(update_fields=['name', 'description'])

    premium_type = ContractTypeDefinition.objects.filter(code=PREMIUM_TYPE_CODE).first()
    if premium_type:
        premium_type.name = PREMIUM_TYPE_NAME
        premium_type.description = 'Premium general trade agreement with enhanced terms and benefits'
        premium_type.save(update_fields=['name', 'description'])

    ContractTemplate.objects.filter(contract_type__code=REGULAR_TYPE_CODE).update(
        name='General Trade Agreement - Supporting Legal System'
    )
    ContractTemplate.objects.filter(contract_type__code=PREMIUM_TYPE_CODE).update(name=PREMIUM_TEMPLATE_NAME)


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0032_remove_manual_contract_number_fields'),
    ]

    operations = [
        migrations.RunPython(standardize_gt_names, reverse_standardize_gt_names),
    ]
