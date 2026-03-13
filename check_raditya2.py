import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from django.contrib.auth.models import User, Group
from contracts.models import Contract, ContractParticipant

output = []

# Check Raditya
raditya = User.objects.filter(username__icontains='raditya').first()
output.append(f'Raditya: {raditya.username if raditya else "Not found"}')
if raditya:
    groups = list(raditya.groups.values_list("name", flat=True))
    output.append(f'Groups: {groups}')

# Check Legal Team group
legal_group = Group.objects.filter(name__icontains='legal').first()
output.append(f'Legal Group: {legal_group.name if legal_group else "Not found"}')
if legal_group:
    members = list(legal_group.user_set.values_list("username", flat=True))
    output.append(f'Members: {members}')

# Check contract
contract = Contract.objects.filter(status='LEGAL_REVIEW').first()
if contract:
    output.append(f'Contract: {contract.title} (Status: {contract.status})')
    participants = ContractParticipant.objects.filter(contract=contract)
    output.append(f'Participants ({participants.count()}):')
    for p in participants:
        output.append(f'  - {p.user.username} ({p.role})')
        
    # Add Raditya if missing
    if raditya:
        participant, created = ContractParticipant.objects.get_or_create(
            contract=contract,
            user=raditya,
            defaults={'role': 'LEGAL'}
        )
        if created:
            output.append(f'✓ Added {raditya.username} as LEGAL participant')
        else:
            output.append(f'✓ {raditya.username} already a participant')
else:
    output.append('No LEGAL_REVIEW contracts')

# Print and save
for line in output:
    print(line)

# Also write to file
with open('/tmp/check_raditya.log', 'w') as f:
    f.write('\n'.join(output))
