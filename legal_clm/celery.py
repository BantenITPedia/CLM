import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')

app = Celery('legal_clm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'check-contract-expiry-daily': {
        'task': 'contracts.tasks.check_contract_expiry',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9 AM
    },
    'send-renewal-reminders': {
        'task': 'contracts.tasks.send_renewal_reminders',
        'schedule': crontab(hour=10, minute=0),  # Run daily at 10 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
