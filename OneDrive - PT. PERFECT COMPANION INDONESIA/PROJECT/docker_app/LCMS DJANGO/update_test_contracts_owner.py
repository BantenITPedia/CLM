#!/usr/bin/env python
"""
Update test contracts to be accessible to the current admin user
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from django.contrib.auth.models import User
from contracts.models import Contract, ContractParticipant, ParticipantRole

# Get the first superuser (admin)
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    print("No superuser found. Creating one...")
    admin_user = User.objects.create_superuser('admin', 'admin@company.com', 'admin')
    print(f"Created superuser: {admin_user.username}")

# Update all contracts to be owned by admin
contracts = Contract.objects.all()
count = 0
for contract in contracts:
    if contract.owner != admin_user:
        contract.owner = admin_user
        contract.save()
        count += 1
        
        # Ensure admin is a participant
        ContractParticipant.objects.get_or_create(
            contract=contract,
            user=admin_user,
            defaults={'role': ParticipantRole.OWNER}
        )

print(f"\n✓ Updated {count} contracts to be owned by {admin_user.username}")
print(f"\nAdmin User: {admin_user.username}")
print(f"Email: {admin_user.email}")
print(f"Total contracts: {contracts.count()}")

# Show expiring contracts
from datetime import datetime, timedelta
today = datetime.now().date()
expiring = Contract.objects.filter(
    end_date__gte=today,
    end_date__lte=today + timedelta(days=30),
    status='EXPIRING_SOON'
)
print(f"\nExpiring contracts accessible to {admin_user.username}:")
for contract in expiring:
    print(f"  ✓ {contract.title} (expires {contract.end_date})")
