from django.db import migrations, models


def seed_notification_templates(apps, schema_editor):
    NotificationEmailTemplate = apps.get_model('contracts', 'NotificationEmailTemplate')

    events = [
        ('contract_created', 'Contract Created Email'),
        ('customer_invitation', 'Customer Invitation Email'),
        ('legal_review', 'Legal Review Email'),
        ('contract_approved', 'Contract Approved Email'),
        ('signature_request', 'Signature Request Email'),
        ('contract_signed', 'Contract Signed Email'),
        ('contract_activated', 'Contract Activated Email'),
        ('expiry_reminder', 'Expiry Reminder Email'),
        ('contract_expired', 'Contract Expired Email'),
        ('renewal_created', 'Renewal Created Email'),
        ('data_submitted', 'Data Submitted Email'),
        ('draft_generated', 'Draft Generated Email'),
        ('signature_request_participant', 'Participant Signature Request Email'),
        ('approval_request_participant', 'Participant Approval Request Email'),
    ]

    for event_key, name in events:
        NotificationEmailTemplate.objects.get_or_create(
            event_key=event_key,
            defaults={
                'name': name,
                'enabled': True,
                'description': 'Generated from migration. Edit in admin to customize subject/body.',
            },
        )


def unseed_notification_templates(apps, schema_editor):
    NotificationEmailTemplate = apps.get_model('contracts', 'NotificationEmailTemplate')
    NotificationEmailTemplate.objects.filter(
        event_key__in=[
            'contract_created',
            'customer_invitation',
            'legal_review',
            'contract_approved',
            'signature_request',
            'contract_signed',
            'contract_activated',
            'expiry_reminder',
            'contract_expired',
            'renewal_created',
            'data_submitted',
            'draft_generated',
            'signature_request_participant',
            'approval_request_participant',
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0037_seed_gt_premium_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationEmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_key', models.CharField(help_text='Email event key (for example: contract_created, legal_review, expiry_reminder)', max_length=100, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('enabled', models.BooleanField(default=True, help_text='Disable to skip this notification type')),
                ('subject_template', models.CharField(blank=True, help_text='Optional Django-template subject override', max_length=255)),
                ('use_custom_html', models.BooleanField(default=False, help_text='Use custom HTML body below instead of templates/emails/*.html')),
                ('html_template', models.TextField(blank=True, help_text='Custom HTML body using Django template syntax')),
                ('text_template', models.TextField(blank=True, help_text='Optional plain-text body using Django template syntax')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['event_key'],
            },
        ),
        migrations.RunPython(seed_notification_templates, unseed_notification_templates),
    ]
