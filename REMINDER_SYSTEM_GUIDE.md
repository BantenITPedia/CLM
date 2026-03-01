# Automated Email Reminders - Implementation Guide

**Status:** ✅ Complete  
**Scope:** Configurable automated email reminders per core_clm_spec.md section 7  
**Framework:** Django + Celery (background jobs)  
**Date:** January 30, 2026

---

## Overview

Implements automated email reminders as defined in core_clm_spec.md:
- **Contract expiration** - notify before end date
- **Signature pending** - notify when awaiting signatures
- **Renewal notification** - notify when renewal is due

All reminders are:
- **Configurable** - admin can adjust schedules without code changes
- **Throttled** - prevent duplicate reminders via configurable frequency
- **Audited** - every reminder is logged for compliance and troubleshooting
- **Scoped** - can be global, per-contract-type, or per-contract

---

## Architecture

### Models

#### ReminderConfiguration
Stores configurable reminder schedules.

**Fields:**
- `reminder_type` (choices) - EXPIRY, SIGNATURE_PENDING, RENEWAL
- `scope` (choices) - GLOBAL, TYPE, CONTRACT
- `contract_type` - ForeignKey to ContractTypeDefinition (if scope=TYPE)
- `contract` - ForeignKey to Contract (if scope=CONTRACT)
- `enabled` (bool) - quick enable/disable without deleting
- `days_before_trigger` (int) - days before event to send reminder
- `frequency` (choices) - ONCE, DAILY, WEEKLY
- `max_occurrences` (int) - limit total sends (0=unlimited)
- `recipient_roles` (string) - comma-separated roles (e.g., "OWNER,SIGNATORY")
- `description` (text) - admin notes
- `created_at`, `updated_at` (timestamps)

**Indexes:**
- `(reminder_type, scope, enabled)` - primary query
- `(contract_type, enabled)` - type-specific queries
- `(contract, enabled)` - per-contract queries

**Unique Constraint:**
- One global reminder per type (scope=GLOBAL, contract_type=NULL, contract=NULL)

#### ReminderLog
Audit trail of all sent/scheduled reminders. Prevents duplicates and enables troubleshooting.

**Fields:**
- `reminder_config` - ForeignKey to ReminderConfiguration
- `contract` - ForeignKey to Contract
- `reminder_type` - Type of reminder sent (denormalized for query speed)
- `scheduled_date` - When reminder was due
- `sent_date` - When it was actually sent (NULL if not sent)
- `recipients` - Comma-separated email list
- `status` (choices) - SCHEDULED, SENT, FAILED, SKIPPED
- `error_message` (text) - if status=FAILED
- `email_subject` (string) - email subject sent
- `created_at`, `updated_at` (timestamps)

**Indexes:**
- `(contract, -scheduled_date)` - per-contract history
- `(reminder_type, status)` - find stuck reminders
- `(sent_date)` - historical analysis

**Read-Only in Admin:**
- ReminderLogs are never manually created/edited
- Generated only by background tasks
- Preserved for audit trail

---

## Service Layer

### ReminderService

**Location:** `contracts/services.py`

#### `get_due_reminders(reminder_type=None, contract_type=None)`

Identifies contracts with reminders that are due.

**Logic:**
1. Query active ReminderConfigurations matching type/scope
2. For each config, get target contracts (GLOBAL → all, TYPE → by type, CONTRACT → specific)
3. Calculate trigger date for each contract based on reminder type and days_before_trigger
4. Check if trigger date has passed
5. Check throttling (don't send if already sent per frequency)
6. Check max_occurrences (don't send if limit reached)
7. Return list of due (contract, config, trigger_date) tuples

**Usage:**
```python
due_reminders = ReminderService.get_due_reminders(reminder_type='EXPIRY')

for contract, config, trigger_date in due_reminders:
    # Process reminder
    pass
```

#### `_calculate_trigger_date(contract, reminder_type, days_before)`

Calculates when a reminder should trigger.

**Logic:**
- **EXPIRY**: contract.end_date - days_before_trigger
- **SIGNATURE_PENDING**: contract.updated_at.date() + days_before_trigger
- **RENEWAL**: contract.end_date - days_before_trigger (same as EXPIRY but different message)

#### `_should_send_reminder(contract, config)`

Implements throttling based on frequency.

**Logic:**
- **ONCE**: Never send if already sent
- **DAILY**: Send at most once per day
- **WEEKLY**: Send at most once per week

Checks ReminderLog history to enforce.

#### `schedule_reminders(dry_run=False)`

Main orchestration - find due reminders and create ReminderLog entries.

**Returns:**
```python
{
    'scheduled': 5,           # Reminders scheduled this run
    'dry_run': False,
    'timestamp': '2026-01-30T10:30:00Z'
}
```

#### `send_reminder_batch(batch_size=100)`

Send all SCHEDULED reminders. Updates ReminderLog status.

**Returns:**
```python
{
    'sent': 4,               # Successfully sent
    'failed': 1,             # Failed to send
    'total': 5,
    'timestamp': '2026-01-30T10:30:05Z'
}
```

#### Helper Methods

**`_send_reminder_email(contract, config, recipients_str)`**
- Dispatches to appropriate EmailService method based on reminder_type

**`_get_recipient_emails(contract, config)`**
- Gets participant emails filtered by config's recipient_roles
- Always includes contract owner

---

## Celery Tasks

**Location:** `contracts/tasks.py`

### Core Tasks (Daily Schedule)

#### `check_contract_expiry()`
Legacy task - updates contract statuses for expired/expiring_soon.
No changes to core logic, still sends EmailService.send_contract_expired_email() for backward compatibility.

#### `schedule_reminders()`
**Recommended timing:** Daily (early morning)

Identifies all due reminders and creates ReminderLog entries. Separates scheduling from sending to allow flexible timing.

**Code:**
```python
@shared_task
def schedule_reminders():
    """Daily task to identify and schedule due reminders"""
    return ReminderService.schedule_reminders(dry_run=False)
```

#### `send_reminders()`
**Recommended timing:** Multiple times per day (after schedule_reminders)

Sends all SCHEDULED ReminderLog entries via EmailService.

**Code:**
```python
@shared_task
def send_reminders():
    """Send all scheduled reminders"""
    return ReminderService.send_reminder_batch(batch_size=100)
```

### Specialized Tasks

#### `check_signature_pending_reminders()`
Identifies contracts in PENDING_SIGNATURE and sends reminders based on ReminderConfiguration.SIGNATURE_PENDING.

#### `check_expiry_reminders()`
Identifies contracts approaching end_date and sends reminders based on ReminderConfiguration.EXPIRY.

#### `check_renewal_reminders()`
Identifies contracts needing renewal and sends reminders based on ReminderConfiguration.RENEWAL.

---

## Email Service Extensions

**Location:** `contracts/services.py` (EmailService class)

### New Methods

#### `send_expiry_reminder_email(contract, recipients=None)`
Sends expiry reminder using template `emails/expiry_reminder.html`.

**Context:**
- `contract` - Contract instance
- `days_until_expiry` - Days remaining
- `site_url` - Site URL for links

#### `send_signature_pending_reminder(contract, recipients=None)`
Sends signature pending reminder, focuses on SIGNATORY role.

**Context:**
- `contract` - Contract instance
- `site_url` - Site URL for links

#### `send_renewal_reminder(contract, recipients=None)`
Sends renewal notification reminder.

**Context:**
- `contract` - Contract instance
- `end_date` - Contract end date
- `site_url` - Site URL for links

---

## Default Configurations

**Data Migration:** `0007_populate_default_reminders.py`

Auto-created on first run (production-safe):

| Type | Scope | Days | Frequency | Max | Recipients |
|------|-------|------|-----------|-----|------------|
| EXPIRY | GLOBAL | 30 | ONCE | 1 | All |
| SIGNATURE_PENDING | GLOBAL | 3 | DAILY | 0 | SIGNATORY, OWNER |
| RENEWAL | GLOBAL | 60 | ONCE | 1 | All |

**Customization:**
Admin can add type-specific or per-contract overrides via Django admin without deleting defaults.

---

## Django Admin Interface

**Location:** `contracts/admin.py`

### ReminderConfigurationAdmin

**Features:**
- List view with quick filter (type, scope, enabled, frequency)
- Fieldsets organized by functionality:
  - Reminder Type & Scope
  - Schedule Configuration
  - Recipients
  - Metadata
- Help text explaining each field
- Search across description, contract type, contract title

**Workflow:**
```
1. Admin → Django Admin → Reminder Configurations
2. View default GLOBAL configurations
3. Click "Add Reminder Configuration"
4. Select reminder_type, scope
5. Set schedule parameters
6. Save
```

### ReminderLogAdmin

**Features:**
- Read-only view (logs auto-generated by tasks)
- List view with status filter (SENT, FAILED, SCHEDULED, SKIPPED)
- Search by contract, recipients, email subject, error message
- Full details view including error messages for troubleshooting
- Preserved for audit trail (no delete permission)

**Workflow:**
```
1. Admin → Django Admin → Reminder Logs
2. Filter by status='FAILED'
3. Click log entry to view error_message
4. Diagnose and adjust ReminderConfiguration if needed
```

---

## Configuration Examples

### Example 1: Contract-Type-Specific Expiry Reminder

**Scenario:** For DISTRIBUTOR agreements, send reminder 14 days before (not 30).

**Steps:**
1. Admin → Reminder Configurations → Add
2. Reminder Type: EXPIRY
3. Scope: TYPE
4. Contract Type: DISTRIBUTOR Agreement
5. Days Before Trigger: 14
6. Frequency: ONCE
7. Max Occurrences: 1
8. Save

**Result:** DISTRIBUTOR contracts get 14-day reminders; others get 30-day (global).

### Example 2: Per-Contract Override

**Scenario:** Specific VIP contract needs daily reminders until signed.

**Steps:**
1. Admin → Reminder Configurations → Add
2. Reminder Type: SIGNATURE_PENDING
3. Scope: CONTRACT
4. Contract: Select specific VIP contract
5. Days Before Trigger: 0 (remind immediately and every day)
6. Frequency: DAILY
7. Max Occurrences: 0 (unlimited)
8. Recipient Roles: SIGNATORY
9. Save

**Result:** VIP contract gets daily signature reminders; others get 3-day default.

### Example 3: Disable Renewal Reminders

**Scenario:** Temporarily disable renewal reminders during system upgrade.

**Steps:**
1. Admin → Reminder Configurations
2. Find RENEWAL (global)
3. Edit → uncheck "Enabled"
4. Save

**Result:** No renewal reminders sent until re-enabled.

---

## Celery Beat Schedule

Add to Django settings or celery configuration:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Existing tasks
    'check_contract_expiry': {
        'task': 'contracts.tasks.check_contract_expiry',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    
    # New reminder tasks
    'schedule_reminders': {
        'task': 'contracts.tasks.schedule_reminders',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
    },
    'send_reminders': {
        'task': 'contracts.tasks.send_reminders',
        'schedule': crontab(hour='6,12,18', minute=5),  # 6:05 AM, 12:05 PM, 6:05 PM
    },
}
```

**Timing Rationale:**
- `schedule_reminders` runs once daily to identify due reminders (light query)
- `send_reminders` runs multiple times to ensure delivery and handle queues
- Separated to enable retry without re-identifying

---

## Implementation Checklist

✅ **Models**
- ReminderConfiguration model with scopes, frequency, throttling
- ReminderLog model for audit trail
- Indexes for performance
- Unique constraints for consistency

✅ **Service Layer**
- ReminderService with orchestration methods
- Trigger date calculation per reminder type
- Throttling logic based on frequency
- Helper methods for recipients and emails

✅ **Email Integration**
- Three new EmailService methods for each reminder type
- Template rendering
- Recipient filtering by role

✅ **Celery Tasks**
- `schedule_reminders()` - identify due reminders
- `send_reminders()` - send scheduled reminders
- Specialized tasks for each reminder type (optional)

✅ **Admin Interface**
- ReminderConfigurationAdmin for management
- ReminderLogAdmin for audit/troubleshooting
- Fieldsets and help text for usability

✅ **Database Migrations**
- Schema migration (0006) - create models and indexes
- Data migration (0007) - populate defaults

✅ **Documentation**
- This guide
- API reference
- Configuration examples

---

## Testing

### Manual Testing

**Test 1: Schedule Reminders**
```python
from contracts.tasks import schedule_reminders
result = schedule_reminders()
print(result)  # {'scheduled': N, ...}
```

**Test 2: Check Due Reminders**
```python
from contracts.services import ReminderService
due = ReminderService.get_due_reminders(reminder_type='EXPIRY')
print(f"Due reminders: {len(due)}")
```

**Test 3: Send Reminders**
```python
from contracts.tasks import send_reminders
result = send_reminders()
print(result)  # {'sent': N, 'failed': M, ...}
```

### Admin Testing

1. **Create Configuration:**
   - Admin → Reminder Configurations → Add
   - Set reminder_type, scope, schedule
   - Save

2. **View Logs:**
   - Admin → Reminder Logs
   - Filter by status
   - Check error_message for issues

3. **Disable/Enable:**
   - Edit configuration
   - Toggle "enabled" checkbox
   - Verify no logs created when disabled

---

## Troubleshooting

### Reminders Not Sending

**Check 1:** Configuration enabled?
```python
from contracts.models import ReminderConfiguration
configs = ReminderConfiguration.objects.filter(enabled=True)
print(configs)
```

**Check 2:** Due date passed?
```python
from contracts.services import ReminderService
due = ReminderService.get_due_reminders()
print(f"Due: {len(due)}")
```

**Check 3:** Throttled?
```python
from contracts.models import ReminderLog
logs = ReminderLog.objects.filter(status='SKIPPED')
print(logs)
```

**Check 4:** Failed to send?
```python
logs = ReminderLog.objects.filter(status='FAILED')
for log in logs:
    print(f"{log.contract}: {log.error_message}")
```

### Duplicate Reminders

**Cause:** Frequency set to ONCE but max_occurrences > 1.

**Solution:**
- Edit configuration
- Set max_occurrences = 1
- Or increase days_before_trigger to avoid overlap

### Missing Recipients

**Cause:** Recipient roles don't match participants.

**Solution:**
1. Check contract participants
2. Admin → Contracts → Participants
3. Verify roles match config recipient_roles
4. Adjust configuration or add participants

---

## Compliance & Audit

**What's Logged:**
- Every reminder scheduled (ReminderLog.status=SCHEDULED)
- Every email sent (ReminderLog.status=SENT, sent_date populated)
- Every failure (ReminderLog.status=FAILED, error_message populated)
- Email recipients and subject line

**Audit Trail:**
- All logs searchable by contract, reminder type, date range
- Immutable (no delete permission in admin)
- Preserved for compliance audits

**Throttling Compliance:**
- ReminderService enforces frequency limits
- ReminderLog.status=SKIPPED logs throttled reminders
- Admin can audit throttling behavior

---

## Performance Considerations

**Query Optimization:**
- Indexes on (reminder_type, scope, enabled)
- Indexes on (contract, -scheduled_date) for history
- Denormalized reminder_type in ReminderLog for direct queries

**Batch Size:**
- `send_reminders()` processes 100 reminders per task
- Adjust batch_size if needed for large deployments

**Email Rate Limiting:**
- Configure Django email backend for rate limiting
- Task failures logged in ReminderLog for retry

---

## Production Deployment

**Checklist:**
1. ✅ Run migrations: `python manage.py migrate`
2. ✅ Verify default reminders created: Admin → Reminder Configurations
3. ✅ Configure Celery Beat schedule (see above)
4. ✅ Start Celery Beat scheduler
5. ✅ Start Celery worker
6. ✅ Test scheduling: `python manage.py shell` → `schedule_reminders()`
7. ✅ Test sending: `python manage.py shell` → `send_reminders()`
8. ✅ Monitor ReminderLog for errors
9. ✅ Configure alerts for failed reminders

---

## Summary

Automated email reminders are now fully configurable without code changes. Admins can:
- Enable/disable reminder types globally
- Set custom schedules per contract type
- Override for specific contracts
- Monitor delivery and troubleshoot failures

The system is production-ready with proper audit logging, throttling, and error handling.
