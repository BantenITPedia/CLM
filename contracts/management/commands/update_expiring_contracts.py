from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from contracts.models import Contract, ContractStatus, AuditLog


class Command(BaseCommand):
    help = 'Mark ACTIVE contracts as EXPIRING_SOON if within 90 days of expiration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to consider as expiring soon (default: 90)'
        )

    def handle(self, *args, **options):
        days_threshold = options['days']
        today = timezone.now().date()
        expiration_date = today + timedelta(days=days_threshold)
        
        # Find ACTIVE contracts expiring within threshold
        expiring_contracts = Contract.objects.filter(
            status=ContractStatus.ACTIVE,
            end_date__gte=today,
            end_date__lte=expiration_date
        ).exclude(status=ContractStatus.EXPIRING_SOON)
        
        updated_count = 0
        for contract in expiring_contracts:
            contract.status = ContractStatus.EXPIRING_SOON
            contract.save(update_fields=['status'])
            
            # Log the status change
            AuditLog.objects.create(
                contract=contract,
                action='STATUS_CHANGE',
                details=f"Status automatically changed to EXPIRING_SOON (expires in {(contract.end_date - today).days} days)",
                old_value=ContractStatus.ACTIVE,
                new_value=ContractStatus.EXPIRING_SOON
            )
            updated_count += 1
        
        # Revert contracts that are no longer expiring soon (beyond threshold)
        reverted_contracts = Contract.objects.filter(
            status=ContractStatus.EXPIRING_SOON,
            end_date__gt=expiration_date
        )
        
        reverted_count = 0
        for contract in reverted_contracts:
            contract.status = ContractStatus.ACTIVE
            contract.save(update_fields=['status'])
            
            AuditLog.objects.create(
                contract=contract,
                action='STATUS_CHANGE',
                details=f"Status reverted from EXPIRING_SOON to ACTIVE (expiration extended)",
                old_value=ContractStatus.EXPIRING_SOON,
                new_value=ContractStatus.ACTIVE
            )
            reverted_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Updated {updated_count} contracts to EXPIRING_SOON\n'
                f'✓ Reverted {reverted_count} contracts back to ACTIVE'
            )
        )
