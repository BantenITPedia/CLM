import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')

app = Celery('legal_clm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Keep startup retry behavior explicit for Celery 6+ compatibility.
app.conf.broker_connection_retry_on_startup = True

# Celery Beat Schedule
app.conf.beat_schedule = {
    'update-expiring-contracts-daily': {
        'task': 'contracts.tasks.update_expiring_contracts',
        'schedule': crontab(hour=8, minute=0),  # Run daily at 8 AM
    },
    'schedule-reminders-daily': {
        'task': 'contracts.tasks.schedule_reminders',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9 AM
    },
    'send-reminders-hourly': {
        'task': 'contracts.tasks.send_reminders',
        'schedule': crontab(minute=0),  # Run every hour
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
