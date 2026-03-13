#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
sys.path.insert(0, '/app')
django.setup()

from contracts.models import Contract, ContractStatus
from contracts.services import EmailService

# Find and update contract
contracts = Contract.objects.all()
print(f"Total contracts: {contracts.count()}")

for c in contracts:
    print(f"- ID {c.id}: {c.title} (Status: {c.status})")
    if c.status == 'SUBMITTED':
        print(f"  Updating {c.title} to LEGAL_REVIEW...")
        c.status = ContractStatus.LEGAL_REVIEW
        c.save()
        EmailService.send_legal_review_email(c)
        print(f"  ✓ Updated and email sent")
