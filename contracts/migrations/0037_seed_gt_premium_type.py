# Generated migration for seeding GT Premium type and related data

from django.db import migrations


def seed_gt_premium_type(apps, schema_editor):
    """Seed GT PREMIUM contract type and all related data"""
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    ContractField = apps.get_model('contracts', 'ContractField')
    ContractTemplate = apps.get_model('contracts', 'ContractTemplate')
    
    # Create GT PREMIUM type definition if it doesn't exist
    gt_premium, created = ContractTypeDefinition.objects.get_or_create(
        code='GENERAL_TRADE_PREMIUM',
        defaults={
            'name': 'General Trade Agreement - Premium',
            'description': 'Premium General Trade Agreement with advanced performance metrics, escrow conditions, and penalty clauses',
            'active': True,
            'is_template_based': True,
        }
    )
    
    # Create GT PREMIUM template
    template, _ = ContractTemplate.objects.get_or_create(
        contract_type=gt_premium,
        defaults={
            'name': 'GT Premium - Advanced Template',
            'content': '''<html><body><h1>PREMIUM GENERAL TRADE AGREEMENT</h1>
<p><b>Buyer:</b> {{ party_b_name }}</p>
<p><b>Address:</b> {{ party_b_address }}</p>
<p><b>Contract Period:</b> {{ contract_start_date }} to {{ contract_end_date }}</p>
<p><b>Payment Terms:</b> {{ payment_terms }}</p>
<p><b>Escrow:</b> {{ escrow_required }} ({{ escrow_percentage }}%)</p>
<p><b>Performance Bonus:</b> {{ performance_bonus }}%</p>
<p><b>Penalty Clause:</b> {{ penalty_clause }} IDR</p>
</body></html>''',
            'active': True,
            'version': 1,
        }
    )
    
    # Define GT PREMIUM fields
    gt_premium_fields = [
        ('party_b_name', 'Buyer Name', 'text', True, 1),
        ('party_b_company_id', 'Buyer Company ID', 'text', False, 2),
        ('party_b_address', 'Buyer Address', 'textarea', True, 3),
        ('delivery_address', 'Delivery Address', 'textarea', False, 4),
        ('business_form', 'Business Form', 'select', True, 5),
        ('contract_start_date', 'Contract Start Date', 'date', True, 6),
        ('contract_end_date', 'Contract End Date', 'date', True, 7),
        ('cvcode_number', 'CV Code Number', 'text', False, 8),
        ('quarter_1_period', 'Q1 Period', 'text', False, 9),
        ('quarter_2_period', 'Q2 Period', 'text', False, 10),
        ('quarter_3_period', 'Q3 Period', 'text', False, 11),
        ('quarter_4_period', 'Q4 Period', 'text', False, 12),
        ('sales_target_q1', 'Q1 Sales Target (IDR)', 'number', False, 13),
        ('sales_target_q2', 'Q2 Sales Target (IDR)', 'number', False, 14),
        ('sales_target_q3', 'Q3 Sales Target (IDR)', 'number', False, 15),
        ('sales_target_q4', 'Q4 Sales Target (IDR)', 'number', False, 16),
        ('total_purchase_target', 'Total Purchase Target (IDR)', 'number', True, 17),
        ('payment_terms', 'Payment Terms', 'select', True, 18),
        ('escrow_required', 'Escrow Required', 'select', False, 19),
        ('escrow_percentage', 'Escrow Percentage (%)', 'number', False, 20),
        ('penalty_clause', 'Penalty Clause (IDR)', 'number', False, 21),
        ('performance_bonus', 'Performance Bonus (%)', 'number', False, 22),
        ('special_conditions', 'Special Conditions', 'textarea', False, 23),
        ('insurance_required', 'Insurance Required', 'select', False, 24),
    ]
    
    # Create or update fields
    for field_key, label, field_type, required, position in gt_premium_fields:
        field_obj, _ = ContractField.objects.get_or_create(
            contract_type=gt_premium,
            field_key=field_key,
            defaults={
                'label': label,
                'field_type': field_type,
                'required': required,
                'position': position,
            }
        )
        
        # Add options for select fields
        if field_key == 'business_form':
            field_obj.options = ['CV', 'Usaha Perseorangan', 'Badan Hukum Perseroan Terbatas', 'Koperasi']
            field_obj.save()
        elif field_key == 'payment_terms':
            field_obj.options = ['Net 30', 'Net 60', 'Net 90', 'Net 120', 'Upon Delivery', 'Milestone-based']
            field_obj.save()
        elif field_key in ['escrow_required', 'insurance_required']:
            field_obj.options = ['Yes', 'No']
            field_obj.save()


def unseed_gt_premium_type(apps, schema_editor):
    """Remove GT PREMIUM type (reverse operation)"""
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    ContractTypeDefinition.objects.filter(code='GENERAL_TRADE_PREMIUM').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0036_alter_contract_contract_type_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_gt_premium_type, unseed_gt_premium_type),
    ]
