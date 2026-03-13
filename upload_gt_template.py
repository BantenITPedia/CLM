#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from contracts.models import ContractTypeDefinition, ContractTemplate, ContractType
from pathlib import Path

# Read GT template HTML
template_path = Path('contract agreement/Template Agreement GT_ Supporting Legal System - 2.htm')
if not template_path.exists():
    print(f"ERROR: Template file not found at {template_path}")
    exit(1)

with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Template size: {len(content)} bytes")

# Get or create GT type
gt_type = ContractTypeDefinition.objects.get(code=ContractType.GENERAL_TRADE)

# Create/update template
template, created = ContractTemplate.objects.update_or_create(
    contract_type=gt_type,
    name='Supporting Legal System',
    defaults={
        'content': content,
        'active': True,
        'version': 1
    }
)

print(f"Template: {template.name} v{template.version} (created={created})")
print(f"Active: {template.active}")
print(f"Content length: {len(template.content)} bytes")
