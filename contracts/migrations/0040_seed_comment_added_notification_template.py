from django.db import migrations


def seed_comment_added_event(apps, schema_editor):
    NotificationEmailTemplate = apps.get_model('contracts', 'NotificationEmailTemplate')
    NotificationEmailTemplate.objects.get_or_create(
        event_key='comment_added',
        defaults={
            'name': 'Comment Added Email',
            'enabled': True,
            'description': 'Notify participants when a new comment is added on a contract.',
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0039_emailsettings'),
    ]

    operations = [
        migrations.RunPython(seed_comment_added_event, migrations.RunPython.noop),
    ]
