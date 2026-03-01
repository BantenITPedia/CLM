#!/usr/bin/env python
"""Setup test data for dynamic contract system"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lcms.settings')
django.setup()

from contracts.models import ContractTypeDefinition, ContractField, ContractTemplate

# Get VENDOR type
vendor_type = ContractTypeDefinition.objects.get(code='VENDOR')

# Clear existing fields for clean test
ContractField.objects.filter(contract_type=vendor_type).delete()

# Create fields for Vendor Agreement
fields_data = [
    {'field_key': 'vendor_name', 'label': 'Vendor Name', 'field_type': 'text', 'required': True, 'position': 1},
    {'field_key': 'service_description', 'label': 'Service Description', 'field_type': 'text', 'required': True, 'position': 2},
    {'field_key': 'contract_value', 'label': 'Contract Value (IDR)', 'field_type': 'number', 'required': True, 'position': 3},
    {'field_key': 'payment_terms', 'label': 'Payment Terms', 'field_type': 'select', 'required': True, 'position': 4, 'options': ['Net 30', 'Net 60', 'Net 90', 'Upon Delivery']},
    {'field_key': 'start_date', 'label': 'Service Start Date', 'field_type': 'date', 'required': True, 'position': 5},
    {'field_key': 'end_date', 'label': 'Service End Date', 'field_type': 'date', 'required': True, 'position': 6},
    {'field_key': 'supporting_document', 'label': 'Supporting Document', 'field_type': 'file', 'required': False, 'position': 7},
]

for field_data in fields_data:
    options = field_data.pop('options', None)
    field = ContractField.objects.create(contract_type=vendor_type, **field_data)
    if options:
        field.options = options
        field.save()

print(f'✓ Created {len(fields_data)} fields for Vendor Agreement')

# Create template
ContractTemplate.objects.filter(contract_type=vendor_type).delete()
template = ContractTemplate.objects.create(
    contract_type=vendor_type,
    name='Standard Vendor Agreement Template',
    content='<html><body><h1>VENDOR SERVICE AGREEMENT</h1><p><b>Vendor Name:</b> {{ vendor_name }}</p><p><b>Service:</b> {{ service_description }}</p><p><b>Value:</b> ${{ contract_value }}</p><p><b>Payment Terms:</b> {{ payment_terms }}</p><p><b>Period:</b> {{ start_date }} to {{ end_date }}</p></body></html>',
    active=True,
    version=1
)

print(f'✓ Created template: {template.name}')
print('\n=== Setup Complete! ===')
print('\nNext steps:')
print('1. Go to http://localhost/contracts/1/')
print('2. Click "Add Data" button')
print('3. Fill in the 7 fields that appear')
print('4. Click "Save Data"')
print('5. Draft will be generated automatically!')
