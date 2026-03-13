import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from django.contrib.auth.models import Group, User
from contracts.models import ContractParticipant, Contract

# Check if Legal group exists
legal_groups = Group.objects.filter(name__icontains='legal')
print("Legal Groups:", [g.name for g in legal_groups])

# Check if Raditya exists and his groups
raditya = User.objects.filter(first_name__icontains='raditya').first()
if raditya:
    print(f"\nRaditya: {raditya.username}")
    print(f"Groups: {[g.name for g in raditya.groups.all()]}")
else:
    print("\nRaditya not found, checking by username...")
    raditya = User.objects.filter(username__icontains='raditya').first()
    if raditya:
        print(f"Raditya: {raditya.username}")
        print(f"Groups: {[g.name for g in raditya.groups.all()]}")

# Check the contract just created
contract = Contract.objects.filter(status='SUBMITTED').first()
if contract:
    print(f"\nContract: {contract.title} (ID: {contract.id})")
    print(f"Status: {contract.status}")
    participants = ContractParticipant.objects.filter(contract=contract)
    print(f"Participants ({participants.count()}):")
    for p in participants:
        print(f"  - {p.user.username} ({p.role})")
else:
    print("\nNo SUBMITTED contracts found")
