import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from django.contrib.auth.models import User, Group
from contracts.models import Contract, ContractParticipant

# Check Raditya
raditya = User.objects.filter(username__icontains='raditya').first()
print(f'Raditya: {raditya.username if raditya else "Not found"}')
if raditya:
    print(f'Groups: {list(raditya.groups.values_list("name", flat=True))}')

# Check Legal Team group
legal_group = Group.objects.filter(name__icontains='legal').first()
print(f'\nLegal Group: {legal_group.name if legal_group else "Not found"}')
if legal_group:
    print(f'Members: {list(legal_group.user_set.values_list("username", flat=True))}')

# Check contract
contract = Contract.objects.filter(status='LEGAL_REVIEW').first()
if contract:
    print(f'\nContract: {contract.title} (Status: {contract.status})')
    participants = ContractParticipant.objects.filter(contract=contract)
    print(f'Participants ({participants.count()}):')
    for p in participants:
        print(f'  - {p.user.username} ({p.role})')
else:
    print('\nNo LEGAL_REVIEW contracts')

# Add Raditya as participant if missing
if raditya and contract:
    participant, created = ContractParticipant.objects.get_or_create(
        contract=contract,
        user=raditya,
        defaults={'role': 'LEGAL'}
    )
    if created:
        print(f'\n✓ Added {raditya.username} as LEGAL participant')
    else:
        print(f'\n✓ {raditya.username} already a participant')
