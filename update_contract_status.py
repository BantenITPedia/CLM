import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from contracts.models import Contract, ContractStatus
from contracts.services import EmailService

# Update existing contract from SUBMITTED to LEGAL_REVIEW
contract = Contract.objects.filter(status='SUBMITTED').first()
if contract:
    contract.status = ContractStatus.LEGAL_REVIEW
    contract.save()
    print(f"✓ Updated: {contract.title} → LEGAL_REVIEW")
    
    # Send legal review email
    EmailService.send_legal_review_email(contract)
    print(f"✓ Sent legal review email to legal team")
else:
    print("No SUBMITTED contracts found")
