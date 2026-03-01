#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from contracts.models import ContractTypeDefinition, ContractTemplate, ContractType
from pathlib import Path

# Read GT template HTML - use the newer version with UTF-8 encoding
template_path = Path('contract agreement/Template Agreement GT_ Supporting Legal System - 2.htm')
if not template_path.exists():
    print(f"ERROR: Template file not found at {template_path}")
    exit(1)

try:
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
except UnicodeDecodeError:
    with open(template_path, 'r', encoding='latin-1') as f:
        content = f.read()

print(f"Template size: {len(content)} bytes")

# Get GT type
gt_type = ContractTypeDefinition.objects.get(code=ContractType.GENERAL_TRADE)

# Delete old template first
old_templates = ContractTemplate.objects.filter(contract_type=gt_type)
print(f"Deleting {old_templates.count()} old template(s)...")
old_templates.delete()

# Create new template
template = ContractTemplate.objects.create(
    contract_type=gt_type,
    name='Supporting Legal System (v2)',
    content=content,
    active=True,
    version=1
)

print(f"✓ New template uploaded: {template.name} v{template.version}")
print(f"✓ Content length: {len(template.content)} bytes")
print(f"✓ Active: {template.active}")
