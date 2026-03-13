#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from contracts.models import ContractTypeDefinition, ContractType, ContractField

# Create GT type definition
gt_type, created = ContractTypeDefinition.objects.update_or_create(
    code=ContractType.GENERAL_TRADE,
    defaults={
        'name': 'General Trade Agreement - Regular',
        'description': 'Standard general trade agreement for regular customers',
        'is_template_based': True,
        'active': True
    }
)

print(f"GT Type Definition: {gt_type.code} (created={created})")

# Create 21 fields
fields_data = [
    ('party_b_name', 'Buyer Name', 'text', True, 1),
    ('party_b_address', 'Buyer Address', 'text', True, 3),
    ('delivery_address', 'Delivery Address', 'text', False, 4),
    ('business_form', 'Business Form', 'select', True, 5),
    ('contract_start_date', 'Contract Start Date', 'date', True, 6),
    ('contract_end_date', 'Contract End Date', 'date', True, 7),
    ('cvcode_number', 'CV Code Number', 'text', False, 8),
    ('quarter_1_period', 'Q1 Period', 'text', False, 9),
    ('quarter_2_period', 'Q2 Period', 'text', False, 10),
    ('quarter_3_period', 'Q3 Period', 'text', False, 11),
    ('quarter_4_period', 'Q4 Period', 'text', False, 12),
    ('sales_target_q1', 'Q1 Sales Target', 'number', False, 13),
    ('sales_target_q2', 'Q2 Sales Target', 'number', False, 14),
    ('sales_target_q3', 'Q3 Sales Target', 'number', False, 15),
    ('sales_target_q4', 'Q4 Sales Target', 'number', False, 16),
    ('total_purchase_target', 'Total Purchase Target', 'number', False, 17),
    ('party_b_representative', 'Representative Name', 'text', True, 18),
    ('party_b_representative_title', 'Representative Title', 'text', True, 19),
]

for field_key, label, field_type, required, position in fields_data:
    if field_key == 'business_form':
        options = ['CV', 'Usaha Perseorangan', 'Badan Hukum Perseroan Terbatas']
    else:
        options = None
    
    field, created = ContractField.objects.update_or_create(
        contract_type=gt_type,
        field_key=field_key,
        defaults={
            'label': label,
            'field_type': field_type,
            'required': required,
            'options': options,
            'position': position
        }
    )
    print(f"  {field_key}: {label} ({'created' if created else 'updated'})")

print(f"Total GT fields: {gt_type.fields.count()}")
