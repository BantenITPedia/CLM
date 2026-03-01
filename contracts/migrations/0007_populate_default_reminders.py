# Data migration - populate default reminder configurations
# Creates standard reminders for contract expiry, signature pending, and renewal

from django.db import migrations


def create_default_reminders(apps, schema_editor):
    """
    Create default global reminder configurations as per core_clm_spec.md
    
    Defaults:
    - Expiry: 30 days before end_date, once per contract
    - Signature Pending: 3 days after entering pending_signature, once per contract
    - Renewal: 60 days before end_date, once per contract
    """
    ReminderConfiguration = apps.get_model('contracts', 'ReminderConfiguration')
    
    # Only create if they don't already exist
    if ReminderConfiguration.objects.count() == 0:
        # Contract Expiry Reminder - 30 days before
        ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='GLOBAL',
            enabled=True,
            days_before_trigger=30,
            frequency='ONCE',
            max_occurrences=1,
            description='Global reminder: Send email 30 days before contract expiry'
        )
        
        # Signature Pending Reminder - 3 days after pending
        ReminderConfiguration.objects.create(
            reminder_type='SIGNATURE_PENDING',
            scope='GLOBAL',
            enabled=True,
            days_before_trigger=3,
            frequency='DAILY',
            max_occurrences=0,  # Unlimited daily reminders
            recipient_roles='SIGNATORY,OWNER',
            description='Global reminder: Send email 3 days after signature requested (daily)'
        )
        
        # Renewal Notification - 60 days before
        ReminderConfiguration.objects.create(
            reminder_type='RENEWAL',
            scope='GLOBAL',
            enabled=True,
            days_before_trigger=60,
            frequency='ONCE',
            max_occurrences=1,
            description='Global reminder: Send email 60 days before contract renewal is needed'
        )


def remove_default_reminders(apps, schema_editor):
    """
    Remove default reminders on rollback
    (but only if they look like defaults - preserve custom configs)
    """
    ReminderConfiguration = apps.get_model('contracts', 'ReminderConfiguration')
    
    # Only remove if they match exactly what we created
    ReminderConfiguration.objects.filter(
        scope='GLOBAL',
        contract_type__isnull=True,
        contract__isnull=True,
        reminder_type__in=['EXPIRY', 'SIGNATURE_PENDING', 'RENEWAL']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0006_reminderconfiguration_reminderlog'),
    ]

    operations = [
        migrations.RunPython(create_default_reminders, remove_default_reminders),
    ]
