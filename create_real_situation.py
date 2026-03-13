#!/usr/bin/env python
"""
Script to create realistic test contracts demonstrating the workflow
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from django.contrib.auth.models import User
from contracts.models import (
    Contract, ContractStatus, ContractType, ParticipantRole,
    ContractParticipant
)

def create_test_user(username, email, role=None):
    """Create or get a test user"""
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': username.split('_')[0].capitalize(),
            'last_name': username.split('_')[1].capitalize() if '_' in username else 'User',
            'is_staff': role == 'admin',
            'is_active': True
        }
    )
    return user

def create_test_contract(title, status, days_offset=0, user=None, contract_type=None):
    """Create a test contract"""
    if user is None:
        user = User.objects.first()
    
    if contract_type is None:
        contract_type = ContractType.GENERAL_TRADE
    
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=365 + days_offset)
    
    contract = Contract.objects.create(
        title=title,
        description=f"Test contract in {status} status",
        contract_type=contract_type,
        status=status,
        owner=user,
        party_a="PT. Perfect Companion Indonesia",
        party_b=f"Test Partner {title}",
        start_date=start_date,
        end_date=end_date,
        contract_value=Decimal('100000000.00'),
        auto_renew=False,
        business_entity_type="PT"
    )
    
    # Add participants
    ContractParticipant.objects.get_or_create(
        contract=contract,
        user=user,
        defaults={'role': ParticipantRole.OWNER}
    )
    
    print(f"✓ Created contract: {title} ({status})")
    return contract


def main():
    print("\n" + "="*60)
    print("Creating Real Situation Test Data")
    print("="*60 + "\n")
    
    # Create test users
    print("Creating test users...")
    owner = create_test_user('john_owner', 'john@company.com')
    legal = create_test_user('legal_review', 'legal@company.com')
    sales = create_test_user('sales_man', 'sales@company.com')
    
    # Create test contracts at different stages
    print("\nCreating test contracts at different workflow stages...\n")
    
    # 1. DRAFT - Just created, not submitted
    draft1 = create_test_contract(
        "General Trade Agreement - Alpha Corp",
        ContractStatus.DRAFT,
        days_offset=0,
        user=owner
    )
    
    # 2. DRAFT - Another draft
    draft2 = create_test_contract(
        "Service Agreement - Beta Ltd",
        ContractStatus.DRAFT,
        days_offset=0,
        user=sales
    )
    
    # 3. SUBMITTED - Awaiting legal review
    submitted = create_test_contract(
        "Vendor Agreement - Gamma Inc",
        ContractStatus.SUBMITTED,
        days_offset=30,
        user=owner
    )
    
    # 4. LEGAL_REVIEW - Being reviewed by legal
    under_review = create_test_contract(
        "Distributor Agreement - Delta Corp",
        ContractStatus.LEGAL_REVIEW,
        days_offset=60,
        user=legal
    )
    
    # 5. APPROVED - Legal approved, waiting for director signature
    approved = create_test_contract(
        "NDA - Epsilon Ltd",
        ContractStatus.APPROVED,
        days_offset=90,
        user=legal
    )
    
    # 6. ACTIVE - Signed and active
    active1 = create_test_contract(
        "Modern Trade Agreement - Zeta Corp",
        ContractStatus.ACTIVE,
        days_offset=120,
        user=owner
    )
    
    active2 = create_test_contract(
        "Service Agreement - Theta Inc",
        ContractStatus.ACTIVE,
        days_offset=200,
        user=sales
    )
    
    # 7. EXPIRING_SOON - Active but expiring in 20 days
    expiring = Contract.objects.create(
        title="Expiring Lease Agreement - Iota Ltd",
        description="Test contract expiring soon",
        contract_type=ContractType.LEASE,
        status=ContractStatus.EXPIRING_SOON,
        owner=owner,
        party_a="PT. Perfect Companion Indonesia",
        party_b="Iota Ltd",
        start_date=datetime.now().date() - timedelta(days=345),
        end_date=datetime.now().date() + timedelta(days=20),
        contract_value=Decimal('50000000.00'),
        auto_renew=False,
        business_entity_type="PT"
    )
    ContractParticipant.objects.get_or_create(
        contract=expiring,
        user=owner,
        defaults={'role': ParticipantRole.OWNER}
    )
    print(f"✓ Created contract: {expiring.title} (EXPIRING_SOON)")
    
    # 8. TERMINATED - Contract ended
    terminated = Contract.objects.create(
        title="Old Purchase Agreement - Kappa Corp",
        description="Test terminated contract",
        contract_type=ContractType.PURCHASE,
        status=ContractStatus.TERMINATED,
        owner=owner,
        party_a="PT. Perfect Companion Indonesia",
        party_b="Kappa Corp",
        start_date=datetime.now().date() - timedelta(days=730),
        end_date=datetime.now().date() - timedelta(days=30),
        contract_value=Decimal('25000000.00'),
        auto_renew=False,
        business_entity_type="PT"
    )
    ContractParticipant.objects.get_or_create(
        contract=terminated,
        user=owner,
        defaults={'role': ParticipantRole.OWNER}
    )
    print(f"✓ Created contract: {terminated.title} (TERMINATED)")
    
    print("\n" + "="*60)
    print("Summary of Test Data")
    print("="*60)
    print(f"""
Test Users Created:
  • {owner.username} (Owner/Admin)
  • {legal.username} (Legal Team)
  • {sales.username} (Sales)

Test Contracts Created: 8
  ✓ DRAFT: 2 contracts (not submitted yet)
  ✓ SUBMITTED: 1 contract (awaiting legal review)
  ✓ LEGAL_REVIEW: 1 contract (in progress)
  ✓ APPROVED: 1 contract (waiting for signature)
  ✓ ACTIVE: 2 contracts (signed and active)
  ✓ EXPIRING_SOON: 1 contract (expires in 20 days)
  ✓ TERMINATED: 1 contract (ended)

Workflow Demonstration:
1. Start by viewing DRAFT contracts - notice "Submit" button is available
2. Move to SUBMITTED - legal team can now review
3. LEGAL_REVIEW - legal team evaluates and approves
4. APPROVED - awaiting final signature  
5. Upload signed document to auto-activate → ACTIVE
6. EXPIRING_SOON shows contracts nearing end date
7. TERMINATED shows ended contracts

Dashboard shows:
  - Total Contracts: 8
  - Active Contracts: 2
  - Legal Review: 1
  - Draft: 2
  
You can now test the complete workflow!
    """)
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
