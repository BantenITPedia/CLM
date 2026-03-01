# Reminder System - Quick API Reference

**Status:** Ready for use  
**Location:** `contracts/services.py` (ReminderService), `contracts/tasks.py` (Celery tasks), `contracts/admin.py` (Admin)

---

## ReminderService API

### Core Methods

#### `get_due_reminders(reminder_type=None, contract_type=None)`

Get all reminders due to be sent.

```python
from contracts.services import ReminderService

# All due reminders
all_due = ReminderService.get_due_reminders()

# Specific type
expiry_due = ReminderService.get_due_reminders(reminder_type='EXPIRY')

# Returns:
# [(contract_obj, config_obj, trigger_date), ...]
```

#### `schedule_reminders(dry_run=False)`

Find due reminders and create ReminderLog entries.

```python
# Schedule reminders
result = ReminderService.schedule_reminders(dry_run=False)
# {'scheduled': 5, 'dry_run': False, 'timestamp': '...'}

# Dry run (don't create logs)
result = ReminderService.schedule_reminders(dry_run=True)
```

#### `send_reminder_batch(batch_size=100)`

Send all scheduled reminders.

```python
# Send up to 100 reminders
result = ReminderService.send_reminder_batch(batch_size=100)
# {'sent': 4, 'failed': 1, 'total': 5, 'timestamp': '...'}
```

---

## Celery Tasks

### Recommended Schedule

```python
# Celery Beat config (in Django settings)
CELERY_BEAT_SCHEDULE = {
    'schedule_reminders': {
        'task': 'contracts.tasks.schedule_reminders',
        'schedule': crontab(hour=6, minute=0),  # Daily 6 AM
    },
    'send_reminders': {
        'task': 'contracts.tasks.send_reminders',
        'schedule': crontab(hour='6,12,18', minute=5),  # 3x daily
    },
}
```

### Available Tasks

**`schedule_reminders()`** - Identify due reminders  
**`send_reminders()`** - Send scheduled reminders  
**`check_expiry_reminders()`** - Check expiry type  
**`check_signature_pending_reminders()`** - Check signature type  
**`check_renewal_reminders()`** - Check renewal type  

### Manual Execution

```python
from contracts.tasks import schedule_reminders, send_reminders

# Schedule
result1 = schedule_reminders.delay()  # Async
result1 = schedule_reminders()         # Sync

# Send
result2 = send_reminders.delay()      # Async
result2 = send_reminders()             # Sync

print(result1.get(), result2.get())
```

---

## Admin Interface

### Access

Navigate to: `Django Admin → Contracts → Reminder Configurations`

### Create Global Reminder

```
1. Click "Add Reminder Configuration"
2. Reminder Type: [EXPIRY | SIGNATURE_PENDING | RENEWAL]
3. Scope: GLOBAL
4. Days Before Trigger: 30 (for expiry)
5. Frequency: ONCE
6. Max Occurrences: 1
7. Save
```

### Create Type-Specific Reminder

```
1. Click "Add Reminder Configuration"
2. Reminder Type: EXPIRY
3. Scope: TYPE
4. Contract Type: DISTRIBUTOR Agreement
5. Days Before Trigger: 14
6. Frequency: ONCE
7. Save
```

### Create Per-Contract Override

```
1. Click "Add Reminder Configuration"
2. Reminder Type: SIGNATURE_PENDING
3. Scope: CONTRACT
4. Contract: [Select specific contract]
5. Days Before Trigger: 0
6. Frequency: DAILY
7. Max Occurrences: 0 (unlimited)
8. Save
```

### View & Troubleshoot Logs

Navigate to: `Django Admin → Contracts → Reminder Logs`

**Filter by:**
- Status (SENT, FAILED, SCHEDULED, SKIPPED)
- Reminder type
- Date range

**Troubleshoot failures:**
1. Click failed log entry
2. View "Error Information" section
3. Check error_message for issue details

---

## EmailService Extensions

### New Methods

```python
from contracts.services import EmailService

# Send expiry reminder
EmailService.send_expiry_reminder_email(
    contract=contract_obj,
    recipients=['user@example.com']  # Optional
)

# Send signature pending reminder
EmailService.send_signature_pending_reminder(
    contract=contract_obj,
    recipients=['signatory@example.com']  # Optional
)

# Send renewal reminder
EmailService.send_renewal_reminder(
    contract=contract_obj,
    recipients=['owner@example.com']  # Optional
)
```

---

## Models

### ReminderConfiguration

**Choices:**
```python
REMINDER_TYPES = [
    ('EXPIRY', 'Contract Expiration'),
    ('SIGNATURE_PENDING', 'Signature Pending'),
    ('RENEWAL', 'Renewal Notification'),
]

SCOPES = [
    ('GLOBAL', 'Apply to all contracts'),
    ('TYPE', 'Apply to specific contract type'),
    ('CONTRACT', 'Apply to specific contract only'),
]

FREQUENCIES = [
    ('ONCE', 'Send once'),
    ('DAILY', 'Send daily'),
    ('WEEKLY', 'Send weekly'),
]
```

**Query Examples:**
```python
from contracts.models import ReminderConfiguration

# Get all active configs
configs = ReminderConfiguration.objects.filter(enabled=True)

# Get expiry reminders
expiry = ReminderConfiguration.objects.filter(reminder_type='EXPIRY')

# Get per-contract overrides
overrides = ReminderConfiguration.objects.filter(scope='CONTRACT')

# Get type-specific
by_type = ReminderConfiguration.objects.filter(
    scope='TYPE',
    contract_type__code='DISTRIBUTOR'
)
```

### ReminderLog

**Fields:**
- `reminder_config` - ForeignKey to configuration
- `contract` - Contract this reminder is about
- `reminder_type` - Type of reminder (EXPIRY, SIGNATURE_PENDING, RENEWAL)
- `scheduled_date` - When it was due
- `sent_date` - When it was sent
- `recipients` - Comma-separated emails
- `status` - SCHEDULED, SENT, FAILED, SKIPPED
- `error_message` - Error details if failed
- `email_subject` - Subject line that was sent

**Query Examples:**
```python
from contracts.models import ReminderLog

# Find failed reminders
failed = ReminderLog.objects.filter(status='FAILED')

# Find reminders for a contract
logs = ReminderLog.objects.filter(contract=contract_obj)

# Find reminders sent today
from django.utils import timezone
today = timezone.now().date()
today_sent = ReminderLog.objects.filter(
    status='SENT',
    sent_date__date=today
)

# Count by type
from django.db.models import Count
by_type = ReminderLog.objects.values('reminder_type').annotate(
    count=Count('id')
)
```

---

## Configuration Constants

### Default Global Reminders

Automatically created on migration:

```python
# Contract Expiration - 30 days before
ReminderConfiguration(
    reminder_type='EXPIRY',
    scope='GLOBAL',
    enabled=True,
    days_before_trigger=30,
    frequency='ONCE',
    max_occurrences=1,
)

# Signature Pending - 3 days after
ReminderConfiguration(
    reminder_type='SIGNATURE_PENDING',
    scope='GLOBAL',
    enabled=True,
    days_before_trigger=3,
    frequency='DAILY',
    max_occurrences=0,
    recipient_roles='SIGNATORY,OWNER',
)

# Renewal - 60 days before
ReminderConfiguration(
    reminder_type='RENEWAL',
    scope='GLOBAL',
    enabled=True,
    days_before_trigger=60,
    frequency='ONCE',
    max_occurrences=1,
)
```

---

## Debugging

### Check Active Configurations

```python
from contracts.models import ReminderConfiguration

configs = ReminderConfiguration.objects.filter(enabled=True)
for c in configs:
    print(f"{c.reminder_type} ({c.scope}): {c.days_before_trigger} days")
```

### Check Due Reminders

```python
from contracts.services import ReminderService

due = ReminderService.get_due_reminders()
print(f"Due reminders: {len(due)}")

for contract, config, trigger_date in due:
    print(f"  {contract.title}: {config.reminder_type} on {trigger_date}")
```

### Check Recent Logs

```python
from contracts.models import ReminderLog
from django.utils import timezone
from datetime import timedelta

yesterday = timezone.now().date() - timedelta(days=1)
logs = ReminderLog.objects.filter(
    created_at__date__gte=yesterday
)

for log in logs:
    print(f"{log.contract.title}: {log.status}")
```

### Simulate Reminder Sending

```python
# Dry run - see what would be scheduled
from contracts.services import ReminderService
result = ReminderService.schedule_reminders(dry_run=True)
print(result)

# Actual scheduling
result = ReminderService.schedule_reminders(dry_run=False)
print(result)
```

---

## Throttling Examples

### Prevent Duplicate Daily Reminders

```python
config = ReminderConfiguration.objects.create(
    reminder_type='SIGNATURE_PENDING',
    scope='GLOBAL',
    days_before_trigger=0,
    frequency='DAILY',      # Won't send twice same day
    max_occurrences=0,      # Send every day until signed
)
```

### Limit Total Reminders

```python
config = ReminderConfiguration.objects.create(
    reminder_type='EXPIRY',
    scope='GLOBAL',
    days_before_trigger=30,
    frequency='ONCE',
    max_occurrences=3,      # Send max 3 times per contract
)
```

### One-Time Only

```python
config = ReminderConfiguration.objects.create(
    reminder_type='RENEWAL',
    scope='GLOBAL',
    days_before_trigger=60,
    frequency='ONCE',
    max_occurrences=1,      # Send exactly once
)
```

---

## Deployment Checklist

```
☐ Run migrations: python manage.py migrate
☐ Verify default reminders created (Admin UI)
☐ Configure Celery Beat schedule
☐ Start Celery Beat: celery -A legal_clm beat
☐ Start Celery Worker: celery -A legal_clm worker
☐ Test scheduling: python manage.py shell
☐ Test sending: python manage.py shell
☐ Monitor logs: tail -f logs/celery.log
☐ Check admin: http://localhost:8000/admin/contracts/reminderconfiguration/
```

---

## Common Tasks

**Disable all reminders temporarily:**
```python
from contracts.models import ReminderConfiguration
ReminderConfiguration.objects.all().update(enabled=False)
```

**Re-enable after maintenance:**
```python
ReminderConfiguration.objects.all().update(enabled=True)
```

**Find stuck/failed reminders:**
```python
from contracts.models import ReminderLog
failed = ReminderLog.objects.filter(status='FAILED')
for log in failed:
    print(f"{log.contract}: {log.error_message}")
```

**Retry failed reminders:**
```python
# Manual retry - recreate as SCHEDULED
for log in failed:
    log.status = 'SCHEDULED'
    log.sent_date = None
    log.error_message = ''
    log.save()

# Then run send_reminders() to retry
from contracts.tasks import send_reminders
send_reminders()
```

---

For detailed documentation, see: [REMINDER_SYSTEM_GUIDE.md](REMINDER_SYSTEM_GUIDE.md)
