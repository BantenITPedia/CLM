import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from contracts.models import Contract

contracts = Contract.objects.all().order_by('id')
print(f"Total contracts: {contracts.count()}")
print("Contract IDs and titles:")
for c in contracts[:30]:
    print(f"  ID {c.id}: {c.title}")
