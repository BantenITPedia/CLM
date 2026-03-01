# Celery Beat Configuration Example

This file shows how to configure Celery Beat for automated email reminders.

**Location:** Typically in `legal_clm/celery.py` or Django `settings.py`

---

## Option 1: Configure in settings.py

Add to your Django settings file:

```python
# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Celery Beat Schedule - Automated Reminders
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Existing tasks
    'check_contract_expiry': {
        'task': 'contracts.tasks.check_contract_expiry',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
        'options': {'queue': 'default'}
    },
    'send_renewal_reminders': {
        'task': 'contracts.tasks.send_renewal_reminders',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
        'options': {'queue': 'default'}
    },
    'create_renewal_contract': {
        'task': 'contracts.tasks.create_renewal_contract',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {'queue': 'default'}
    },
    
    # NEW: Automated Reminder Tasks
    'schedule_reminders': {
        'task': 'contracts.tasks.schedule_reminders',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
        'options': {'queue': 'default'}
    },
    'send_reminders_morning': {
        'task': 'contracts.tasks.send_reminders',
        'schedule': crontab(hour=6, minute=5),  # 6:05 AM
        'options': {'queue': 'email'}
    },
    'send_reminders_noon': {
        'task': 'contracts.tasks.send_reminders',
        'schedule': crontab(hour=12, minute=5),  # 12:05 PM
        'options': {'queue': 'email'}
    },
    'send_reminders_evening': {
        'task': 'contracts.tasks.send_reminders',
        'schedule': crontab(hour=18, minute=5),  # 6:05 PM
        'options': {'queue': 'email'}
    },
    
    # OPTIONAL: Specific reminder type checks
    'check_expiry_reminders': {
        'task': 'contracts.tasks.check_expiry_reminders',
        'schedule': crontab(hour=6, minute=30),  # 6:30 AM
        'options': {'queue': 'default'}
    },
    'check_signature_pending_reminders': {
        'task': 'contracts.tasks.check_signature_pending_reminders',
        'schedule': crontab(hour=9, minute=0),  # 9 AM
        'options': {'queue': 'default'}
    },
    'check_renewal_reminders': {
        'task': 'contracts.tasks.check_renewal_reminders',
        'schedule': crontab(hour=15, minute=0),  # 3 PM
        'options': {'queue': 'default'}
    },
}
```

---

## Option 2: Configure in legal_clm/celery.py

Alternatively, configure directly in the Celery app file:

```python
# legal_clm/celery.py

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')

app = Celery('legal_clm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configure Beat Schedule
app.conf.beat_schedule = {
    # Reminder Tasks (New)
    'schedule_reminders': {
        'task': 'contracts.tasks.schedule_reminders',
        'schedule': crontab(hour=6, minute=0),  # Daily 6 AM
    },
    'send_reminders': {
        'task': 'contracts.tasks.send_reminders',
        'schedule': crontab(hour='6,12,18', minute=5),  # 3x daily
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

---

## Schedule Explanation

### Daily Schedule

| Task | Time | Purpose |
|------|------|---------|
| `check_contract_expiry` | 00:00 (Midnight) | Check expiry statuses |
| `send_renewal_reminders` | 01:00 (1 AM) | Send legacy renewal reminders |
| `create_renewal_contract` | 02:00 (2 AM) | Auto-create renewals |
| `schedule_reminders` | 06:00 (6 AM) | **Identify due reminders** |
| `send_reminders` | 06:05 (6:05 AM) | **Send scheduled reminders** |
| `check_expiry_reminders` | 06:30 (6:30 AM) | Check expiry type (optional) |
| `send_reminders` | 12:05 (12:05 PM) | **Send afternoon batch** |
| `check_signature_pending_reminders` | 09:00 (9 AM) | Check signature type (optional) |
| `send_reminders` | 18:05 (6:05 PM) | **Send evening batch** |
| `check_renewal_reminders` | 15:00 (3 PM) | Check renewal type (optional) |

### Rationale

1. **Midnight (00:00):** Lightweight status checks, non-email tasks
2. **6 AM (06:00):** Main reminder identification (light query workload)
3. **6:05 AM (06:05):** First email send batch
4. **Noon (12:05):** Second batch (ensures delivery if first queue is slow)
5. **6 PM (18:05):** Third batch (end-of-day follow-up)

**Benefits:**
- Spreads load across day
- Multiple attempts improve delivery
- Off-peak for most organizations
- Allows throttling to prevent duplicates

---

## Alternative: Continuous Sending

If you prefer continuous sending rather than batches:

```python
CELERY_BEAT_SCHEDULE = {
    'schedule_reminders': {
        'task': 'contracts.tasks.schedule_reminders',
        'schedule': 3600.0,  # Every hour
    },
    'send_reminders': {
        'task': 'contracts.tasks.send_reminders',
        'schedule': 300.0,   # Every 5 minutes
    },
}
```

This sends reminders continuously, reducing latency but increasing load.

---

## Monitoring Scheduled Tasks

### View Scheduled Tasks

```bash
# Check if Celery Beat is running
ps aux | grep celery

# View scheduled tasks
celery -A legal_clm inspect scheduled

# Output example:
# celery@worker1 -> {
#     'ok': 'Inspected 1 worker',
#     'count': 4,
#     'messages': [
#         {'name': 'contracts.tasks.schedule_reminders',
#          'schedule': '0 6 * * ?',
#          'next_run_time': '2026-01-31T06:00:00+00:00'}
#     ]
# }
```

### Monitor Task Execution

```bash
# Watch celery worker in real-time
celery -A legal_clm events

# View recent tasks
celery -A legal_clm inspect active

# View task stats
celery -A legal_clm inspect stats
```

### Check Logs

```bash
# Tail Celery worker logs
tail -f logs/celery.log

# Search for specific task
tail -f logs/celery.log | grep "schedule_reminders"

# View failures
tail -f logs/celery.log | grep "ERROR"
```

---

## Docker Deployment

If using Docker, add services for Beat and Worker:

```yaml
# docker-compose.yml

services:
  celery:
    build: .
    command: celery -A legal_clm worker --loglevel=info
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

  celery-beat:
    build: .
    command: celery -A legal_clm beat --loglevel=info
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

## Kubernetes Deployment

For Kubernetes, use CronJobs:

```yaml
# kubernetes/reminder-jobs.yaml

apiVersion: batch/v1
kind: CronJob
metadata:
  name: schedule-reminders
spec:
  schedule: "0 6 * * *"  # 6 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: django
            image: your-registry/django-app:latest
            command: 
            - python
            - manage.py
            - shell
            - -c
            - "from contracts.tasks import schedule_reminders; schedule_reminders()"
          restartPolicy: OnFailure

---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: send-reminders
spec:
  schedule: "5 6,12,18 * * *"  # 6:05 AM, 12:05 PM, 6:05 PM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: django
            image: your-registry/django-app:latest
            command:
            - python
            - manage.py
            - shell
            - -c
            - "from contracts.tasks import send_reminders; send_reminders()"
          restartPolicy: OnFailure
```

---

## Development Testing

### Simulate Tasks Manually

```bash
# Enter Django shell
python manage.py shell

# Import tasks
from contracts.tasks import schedule_reminders, send_reminders

# Schedule (no-op if no due reminders)
result = schedule_reminders()
print(result)

# Send (processes scheduled logs)
result = send_reminders()
print(result)
```

### Dry Run

```python
# Schedule reminders (preview, don't create logs)
from contracts.services import ReminderService
result = ReminderService.schedule_reminders(dry_run=True)
print(f"Would schedule: {result['scheduled']} reminders")
```

### Create Test Reminder

```python
from contracts.models import ReminderConfiguration, Contract
from django.utils import timezone
from datetime import timedelta

# Get a contract
contract = Contract.objects.first()

# Create test reminder (expires tomorrow)
config = ReminderConfiguration.objects.create(
    reminder_type='EXPIRY',
    scope='CONTRACT',
    contract=contract,
    enabled=True,
    days_before_trigger=0,  # Trigger immediately
    frequency='ONCE'
)

# Update contract end date
contract.end_date = timezone.now().date()
contract.save()

# Check due reminders
from contracts.services import ReminderService
due = ReminderService.get_due_reminders()
print(f"Due: {len(due)}")

# Schedule
from contracts.tasks import schedule_reminders
schedule_reminders()

# Check logs
from contracts.models import ReminderLog
logs = ReminderLog.objects.filter(contract=contract)
print(f"Logs: {logs.count()}")
```

---

## Troubleshooting

### Task Not Running

```bash
# 1. Check if beat is running
ps aux | grep celery.*beat

# 2. Check if worker is running
ps aux | grep celery.*worker

# 3. Check scheduled tasks
celery -A legal_clm inspect scheduled

# 4. Check logs for errors
tail -f logs/celery.log
```

### Task Running but Not Sending Email

```bash
# Check if send_reminders is finding scheduled logs
python manage.py shell
>>> from contracts.models import ReminderLog
>>> ReminderLog.objects.filter(status='SCHEDULED').count()

# Check for failures
>>> ReminderLog.objects.filter(status='FAILED').first().error_message
```

### High Latency

Reduce batch size or increase frequency:

```python
# More frequent, smaller batches
'send_reminders': {
    'task': 'contracts.tasks.send_reminders',
    'schedule': crontab(minute='*/5'),  # Every 5 minutes
    # With default batch_size=100
}

# Or manually tune batch size in task
def send_reminders():
    return ReminderService.send_reminder_batch(batch_size=10)  # Smaller batch
```

---

## Production Checklist

```
☐ Redis/broker configured and running
☐ Celery worker deployed and running
☐ Celery Beat deployed and running
☐ Schedule configured in settings
☐ Logs being collected (check celery.log)
☐ Default reminders created (checked in admin)
☐ Manual test of schedule_reminders()
☐ Manual test of send_reminders()
☐ Verified emails received
☐ Monitoring/alerting configured
☐ Retention/cleanup policy defined
```

---

## References

- [Celery Documentation](https://docs.celeryproject.io/)
- [Celery Beat](https://docs.celeryproject.io/en/stable/userguide/periodic-tasks.html)
- [Crontab Schedules](https://docs.celeryproject.io/en/stable/userguide/periodic-tasks.html#crontab-schedules)
- [Django Celery Integration](https://docs.celeryproject.io/en/stable/django/)
