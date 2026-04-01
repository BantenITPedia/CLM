from django.db import migrations, models


def seed_default_email_settings(apps, schema_editor):
    EmailSettings = apps.get_model('contracts', 'EmailSettings')
    if not EmailSettings.objects.exists():
        EmailSettings.objects.create(
            name='Default SMTP',
            provider='SMTP',
            is_active=True,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0038_notificationemailtemplate'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Default Email Settings', max_length=100)),
                ('provider', models.CharField(choices=[('SMTP', 'SMTP'), ('RESEND', 'Resend API'), ('SENDGRID', 'SendGrid API')], default='SMTP', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('default_from_email', models.EmailField(blank=True, max_length=254)),
                ('host', models.CharField(blank=True, max_length=255)),
                ('port', models.IntegerField(default=587)),
                ('username', models.CharField(blank=True, max_length=255)),
                ('password', models.CharField(blank=True, max_length=255)),
                ('use_tls', models.BooleanField(default=True)),
                ('use_ssl', models.BooleanField(default=False)),
                ('api_key', models.CharField(blank=True, max_length=255)),
                ('api_endpoint', models.URLField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-is_active', '-updated_at']},
        ),
        migrations.RunPython(seed_default_email_settings, migrations.RunPython.noop),
    ]
