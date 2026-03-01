from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Contract, ContractStatus, AuditLog, ContractParticipant
from .services import EmailService, ReminderService


@shared_task
def update_expiring_contracts():
    """
    Daily task to mark ACTIVE contracts as EXPIRING_SOON if within 90 days of expiration
    """
    today = timezone.now().date()
    days_threshold = 90
    expiration_date = today + timedelta(days=days_threshold)
    
    # Mark ACTIVE contracts as EXPIRING_SOON if within threshold
    expiring_contracts = Contract.objects.filter(
        status=ContractStatus.ACTIVE,
        end_date__gte=today,
        end_date__lte=expiration_date
    )
    
    updated_count = 0
    for contract in expiring_contracts:
        if contract.status != ContractStatus.EXPIRING_SOON:
            contract.status = ContractStatus.EXPIRING_SOON
            contract.save(update_fields=['status'])
            
            AuditLog.objects.create(
                contract=contract,
                action='STATUS_CHANGE',
                details=f"Automatically marked as EXPIRING_SOON - {(contract.end_date - today).days} days until expiration",
                old_value=ContractStatus.ACTIVE,
                new_value=ContractStatus.EXPIRING_SOON
            )
            updated_count += 1
    
    # Revert contracts beyond threshold back to ACTIVE
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
            details='Reverted from EXPIRING_SOON to ACTIVE - expiration date extended',
            old_value=ContractStatus.EXPIRING_SOON,
            new_value=ContractStatus.ACTIVE
        )
        reverted_count += 1
    
    return {
        'updated_to_expiring_soon': updated_count,
        'reverted_to_active': reverted_count,
        'checked_at': str(timezone.now())
    }


@shared_task
def check_contract_expiry():
    """
    Daily task to check contract expiry and send notifications
    Uses ReminderService for configurable expiry reminders
    """
    today = timezone.now().date()
    reminders_sent = 0
    
    # Find contracts that are expiring soon
    expiring_contracts = Contract.objects.filter(
        status=ContractStatus.EXPIRING_SOON,
        end_date__isnull=False
    )
    
    for contract in expiring_contracts:
        if contract.end_date:
            days_until_expiry = (contract.end_date - today).days
            
            # Send reminder if within reminder period
            if 0 <= days_until_expiry <= contract.renewal_reminder_days:
                # Check if we already sent a reminder today
                recent_reminder = AuditLog.objects.filter(
                    contract=contract,
                    action='RENEWAL_REMINDER',
                    timestamp__date=today
                ).exists()
                
                if not recent_reminder:
                    EmailService.send_expiry_reminder_email(contract)
                    reminders_sent += 1
                    
                    AuditLog.objects.create(
                        contract=contract,
                        action='RENEWAL_REMINDER',
                        details=f'Expiry reminder sent - {days_until_expiry} days until expiration'
                    )
    
    return {
        'reminders_sent': reminders_sent,
        'checked_at': str(timezone.now())
    }


@shared_task
def create_renewal_contract(contract_id):
    """
    Create a renewal contract for an expiring contract
    """
    try:
        parent_contract = Contract.objects.get(id=contract_id)
        
        # Check if renewal already exists
        existing_renewal = Contract.objects.filter(
            parent_contract=parent_contract,
            status__in=[
                ContractStatus.DRAFT,
                ContractStatus.PENDING_REVIEW,
                ContractStatus.LEGAL_REVIEW
            ]
        ).exists()
        
        if existing_renewal:
            return {'status': 'skipped', 'reason': 'Renewal already exists'}
        
        # Calculate new dates
        if parent_contract.end_date:
            new_start_date = parent_contract.end_date + timedelta(days=1)
            new_end_date = new_start_date + timedelta(days=parent_contract.renewal_period_months * 30)
        else:
            new_start_date = timezone.now().date()
            new_end_date = new_start_date + timedelta(days=parent_contract.renewal_period_months * 30)
        
        # Create renewal contract
        renewal_contract = Contract.objects.create(
            title=f"{parent_contract.title} (Renewal)",
            contract_type=parent_contract.contract_type,
            description=f"Auto-renewal of contract #{parent_contract.id}",
            party_a=parent_contract.party_a,
            party_b=parent_contract.party_b,
            contract_value=parent_contract.contract_value,
            start_date=new_start_date,
            end_date=new_end_date,
            renewal_reminder_days=parent_contract.renewal_reminder_days,
            auto_renew=parent_contract.auto_renew,
            renewal_period_months=parent_contract.renewal_period_months,
            parent_contract=parent_contract,
            status=ContractStatus.DRAFT,
            owner=parent_contract.owner,
            created_by=parent_contract.owner
        )
        
        # Copy participants from parent contract
        for participant in parent_contract.participants.filter(is_active=True):
            ContractParticipant.objects.create(
                contract=renewal_contract,
                user=participant.user,
                role=participant.role
            )
        
        # Log the auto-renewal
        AuditLog.objects.create(
            contract=renewal_contract,
            action='AUTO_RENEWAL',
            details=f"Auto-renewal created from contract #{parent_contract.id}"
        )
        
        AuditLog.objects.create(
            contract=parent_contract,
            action='AUTO_RENEWAL',
            details=f"Renewal contract #{renewal_contract.id} created"
        )
        
        # Send notification
        EmailService.send_renewal_created_email(renewal_contract, parent_contract)
        
        return {
            'status': 'success',
            'renewal_contract_id': renewal_contract.id,
            'parent_contract_id': parent_contract.id
        }
    
    except Contract.DoesNotExist:
        return {'status': 'error', 'reason': 'Contract not found'}
    except Exception as e:
        return {'status': 'error', 'reason': str(e)}


@shared_task
def test_email_task():
    """Test task to verify Celery is working"""
    print("Celery is working! Task executed successfully.")
    return "Test task completed"

@shared_task
def schedule_reminders():
    """
    Daily task to identify and schedule due reminders
    
    Per core_clm_spec.md, this implements configurable reminder schedules for:
    - Contract expiration
    - Signature pending
    - Renewal notification
    
    This task:
    1. Identifies contracts with due reminders based on ReminderConfiguration
    2. Respects throttling (don't send duplicate reminders)
    3. Respects max occurrences limits
    4. Creates ReminderLog entries for tracking
    
    Called by Celery Beat scheduler (typically daily)
    """
    return ReminderService.schedule_reminders(dry_run=False)


@shared_task
def send_reminders():
    """
    Send all scheduled reminders
    
    This task processes ReminderLog entries that are in SCHEDULED status and sends
    the corresponding emails. Updates log entries with send status and timestamps.
    
    Separated from schedule_reminders to allow flexibility in scheduling.
    Can be run multiple times per day to ensure delivery.
    
    Returns:
        dict with summary of sent/failed reminders
    """
    return ReminderService.send_reminder_batch(batch_size=100)


@shared_task
def check_signature_pending_reminders():
    """
    Task to identify contracts awaiting signatures and send reminders
    
    Checks for contracts in PENDING_SIGNATURE status that are past their
    reminder trigger date per ReminderConfiguration.SIGNATURE_PENDING settings.
    
    Uses ReminderService to determine which reminders are due and throttle duplicates.
    """
    from django.utils import timezone
    from .models import ReminderType
    
    due_reminders = ReminderService.get_due_reminders(
        reminder_type=ReminderType.SIGNATURE_PENDING
    )
    
    processed = 0
    for contract, config, trigger_date in due_reminders:
        # Schedule the reminder
        from .models import ReminderLog
        recipients_list = ReminderService._get_recipient_emails(contract, config)
        
        ReminderLog.objects.create(
            reminder_config=config,
            contract=contract,
            reminder_type=ReminderType.SIGNATURE_PENDING,
            scheduled_date=timezone.now(),
            recipients=','.join(recipients_list),
            status='SCHEDULED'
        )
        processed += 1
    
    return {
        'signature_pending_reminders_scheduled': processed,
        'checked_at': str(timezone.now())
    }


@shared_task
def check_expiry_reminders():
    """
    Task to identify contracts approaching expiry and send reminders
    
    Uses ReminderConfiguration.EXPIRY settings to determine reminder timing.
    Respects configurable schedules and throttling to prevent duplicate reminders.
    
    Per core_clm_spec.md, contract period drives reminder schedule.
    """
    from django.utils import timezone
    from .models import ReminderType
    
    due_reminders = ReminderService.get_due_reminders(
        reminder_type=ReminderType.EXPIRY
    )
    
    processed = 0
    for contract, config, trigger_date in due_reminders:
        from .models import ReminderLog
        recipients_list = ReminderService._get_recipient_emails(contract, config)
        
        ReminderLog.objects.create(
            reminder_config=config,
            contract=contract,
            reminder_type=ReminderType.EXPIRY,
            scheduled_date=timezone.now(),
            recipients=','.join(recipients_list),
            status='SCHEDULED'
        )
        processed += 1
    
    return {
        'expiry_reminders_scheduled': processed,
        'checked_at': str(timezone.now())
    }


@shared_task
def check_renewal_reminders():
    """
    Task to identify contracts due for renewal and send reminders
    
    Uses ReminderConfiguration.RENEWAL settings to determine when renewal reminders
    should be sent (typically N days before contract end date).
    
    Supports auto-renewal workflows per core_clm_spec.md section 7.
    """
    from django.utils import timezone
    from .models import ReminderType
    
    due_reminders = ReminderService.get_due_reminders(
        reminder_type=ReminderType.RENEWAL
    )
    
    processed = 0
    for contract, config, trigger_date in due_reminders:
        from .models import ReminderLog
        recipients_list = ReminderService._get_recipient_emails(contract, config)
        
        ReminderLog.objects.create(
            reminder_config=config,
            contract=contract,
            reminder_type=ReminderType.RENEWAL,
            scheduled_date=timezone.now(),
            recipients=','.join(recipients_list),
            status='SCHEDULED'
        )
        processed += 1
    
    return {
        'renewal_reminders_scheduled': processed,
        'checked_at': str(timezone.now())
    }