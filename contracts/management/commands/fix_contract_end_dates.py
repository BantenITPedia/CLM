from django.core.management.base import BaseCommand
from datetime import timedelta
from contracts.models import Contract, AuditLog


class Command(BaseCommand):
    help = 'Fix contract end dates to follow business rule: End Date = Start Date + 1 year - 1 day'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually changing it'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find contracts where end_date is exactly 1 year from start_date
        contracts = Contract.objects.filter(
            start_date__isnull=False,
            end_date__isnull=False
        )
        
        updated_count = 0
        skipped_count = 0
        
        for contract in contracts:
            # Calculate what the end date should be (start + 1 year - 1 day)
            expected_end_date = contract.start_date.replace(year=contract.start_date.year + 1) - timedelta(days=1)
            
            # Check if current end date is exactly 1 year from start (needs fixing)
            anniversary_date = contract.start_date.replace(year=contract.start_date.year + 1)
            
            if contract.end_date == anniversary_date:
                # This contract has end date on anniversary - needs updating
                old_end_date = contract.end_date
                new_end_date = expected_end_date
                
                if dry_run:
                    self.stdout.write(
                        f'Would update Contract #{contract.id}: {contract.title}\n'
                        f'  Start: {contract.start_date}\n'
                        f'  End: {old_end_date} → {new_end_date}\n'
                        f'  Duration: 366 days → 365 days\n'
                    )
                else:
                    contract.end_date = new_end_date
                    contract.save(update_fields=['end_date'])
                    
                    # Log the change
                    AuditLog.objects.create(
                        contract=contract,
                        action='END_DATE_ADJUSTED',
                        details=f'End date adjusted to business rule (Start + 1 year - 1 day): {old_end_date} → {new_end_date}',
                        old_value=str(old_end_date),
                        new_value=str(new_end_date)
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Updated Contract #{contract.id}: {contract.title} - End date: {old_end_date} → {new_end_date}'
                        )
                    )
                
                updated_count += 1
            else:
                skipped_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Would update {updated_count} contracts, {skipped_count} already correct or custom duration'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Updated {updated_count} contracts to follow business rule\n'
                    f'✓ Skipped {skipped_count} contracts (already correct or custom duration)'
                )
            )
