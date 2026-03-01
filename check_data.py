#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from contracts.models import ContractData
from contracts.templatetags.contract_filters import format_number

print("=" * 80)
print("CHECKING STRUCTURED DATA IN ALL CONTRACTS")
print("=" * 80)

for cd in ContractData.objects.all():
    print(f"\nContract ID {cd.contract.id} - Data Version {cd.version}:")
    for k, v in cd.data.items():
        formatted = format_number(v)
        if formatted != str(v):
            print(f"  {k}: {v:20} -> {formatted}")
        else:
            print(f"  {k}: {v} (no change)")
