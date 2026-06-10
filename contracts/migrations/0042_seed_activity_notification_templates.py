from django.db import migrations


ACTIVITY_EVENTS = [
    ('activity_contract_submitted', 'Activity: Contract Submitted'),
    ('activity_structured_data_submitted', 'Activity: Structured Data Submitted'),
    ('activity_participant_added', 'Activity: Participant Added'),
    ('activity_contract_edited', 'Activity: Contract Edited'),
    ('activity_document_uploaded', 'Activity: Document Uploaded'),
    ('activity_final_document_uploaded', 'Activity: Final Document Uploaded'),
    ('activity_status_updated', 'Activity: Status Updated'),
    ('activity_contract_number_assigned', 'Activity: Contract Number Assigned'),
]


def seed_activity_notification_templates(apps, schema_editor):
    NotificationEmailTemplate = apps.get_model('contracts', 'NotificationEmailTemplate')

    for event_key, name in ACTIVITY_EVENTS:
        NotificationEmailTemplate.objects.get_or_create(
            event_key=event_key,
            defaults={
                'name': name,
                'enabled': True,
                'description': 'Operational activity notification toggle. Disable to suppress this specific action email.',
            },
        )


def unseed_activity_notification_templates(apps, schema_editor):
    NotificationEmailTemplate = apps.get_model('contracts', 'NotificationEmailTemplate')
    NotificationEmailTemplate.objects.filter(
        event_key__in=[event_key for event_key, _ in ACTIVITY_EVENTS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0041_seed_global_rbac_groups'),
    ]

    operations = [
        migrations.RunPython(seed_activity_notification_templates, unseed_activity_notification_templates),
    ]
