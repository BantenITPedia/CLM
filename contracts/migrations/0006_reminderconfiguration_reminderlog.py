# Generated migration for ReminderConfiguration and ReminderLog models
# Implements automated email reminders as per core_clm_spec.md

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0005_alter_contractparticipant_unique_together_and_more'),
    ]

    operations = [
        # Add ReminderType choices via model
        migrations.CreateModel(
            name='ReminderConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder_type', models.CharField(
                    choices=[
                        ('EXPIRY', 'Contract Expiration'),
                        ('SIGNATURE_PENDING', 'Signature Pending'),
                        ('RENEWAL', 'Renewal Notification')
                    ],
                    help_text='Type of reminder: expiry, signature pending, or renewal',
                    max_length=20
                )),
                ('scope', models.CharField(
                    choices=[
                        ('GLOBAL', 'Apply to all contracts'),
                        ('TYPE', 'Apply to specific contract type'),
                        ('CONTRACT', 'Apply to specific contract only')
                    ],
                    default='GLOBAL',
                    help_text='Scope of this reminder configuration',
                    max_length=20
                )),
                ('enabled', models.BooleanField(
                    default=True,
                    help_text='Enable/disable this reminder'
                )),
                ('days_before_trigger', models.IntegerField(
                    default=30,
                    help_text='Days before contract date to trigger reminder (e.g., 30 days before expiry)'
                )),
                ('frequency', models.CharField(
                    choices=[
                        ('ONCE', 'Send once'),
                        ('DAILY', 'Send daily'),
                        ('WEEKLY', 'Send weekly')
                    ],
                    default='ONCE',
                    help_text='How often to send reminder once trigger date is reached',
                    max_length=20
                )),
                ('max_occurrences', models.IntegerField(
                    default=1,
                    help_text='Maximum number of times to send this reminder (0=unlimited)'
                )),
                ('recipient_roles', models.CharField(
                    blank=True,
                    help_text='Comma-separated roles to notify (e.g., OWNER,SIGNATORY). Empty=all',
                    max_length=255
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('description', models.TextField(
                    blank=True,
                    help_text='Admin notes about this configuration'
                )),
                ('contract', models.ForeignKey(
                    blank=True,
                    help_text='Specific contract this applies to (if scope=CONTRACT)',
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reminder_configurations',
                    to='contracts.contract'
                )),
                ('contract_type', models.ForeignKey(
                    blank=True,
                    help_text='Contract type this applies to (if scope=TYPE)',
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reminder_configurations',
                    to='contracts.contracttypedefinition'
                )),
            ],
            options={
                'ordering': ['reminder_type', 'scope', '-enabled'],
            },
        ),
        
        migrations.CreateModel(
            name='ReminderLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder_type', models.CharField(
                    choices=[
                        ('EXPIRY', 'Contract Expiration'),
                        ('SIGNATURE_PENDING', 'Signature Pending'),
                        ('RENEWAL', 'Renewal Notification')
                    ],
                    help_text='Type of reminder sent',
                    max_length=20
                )),
                ('scheduled_date', models.DateTimeField(
                    help_text='When this reminder was scheduled/due'
                )),
                ('sent_date', models.DateTimeField(
                    blank=True,
                    help_text='When the reminder was actually sent',
                    null=True
                )),
                ('recipients', models.TextField(
                    help_text='Comma-separated email addresses that received this'
                )),
                ('status', models.CharField(
                    choices=[
                        ('SCHEDULED', 'Scheduled'),
                        ('SENT', 'Sent'),
                        ('FAILED', 'Failed'),
                        ('SKIPPED', 'Skipped (throttled)')
                    ],
                    default='SCHEDULED',
                    max_length=20
                )),
                ('error_message', models.TextField(
                    blank=True,
                    help_text='Error details if status=FAILED'
                )),
                ('email_subject', models.CharField(
                    blank=True,
                    help_text='Email subject line sent',
                    max_length=255
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contract', models.ForeignKey(
                    help_text='Contract this reminder is about',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reminder_logs',
                    to='contracts.contract'
                )),
                ('reminder_config', models.ForeignKey(
                    help_text='Reminder configuration that triggered this',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='logs',
                    to='contracts.reminderconfiguration'
                )),
            ],
            options={
                'ordering': ['-scheduled_date'],
            },
        ),
        
        # Add indexes for performance
        migrations.AddIndex(
            model_name='reminderconfiguration',
            index=models.Index(
                fields=['reminder_type', 'scope', 'enabled'],
                name='reminder_type_scope_enabled_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='reminderconfiguration',
            index=models.Index(
                fields=['contract_type', 'enabled'],
                name='reminder_contract_type_enabled_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='reminderconfiguration',
            index=models.Index(
                fields=['contract', 'enabled'],
                name='reminder_contract_enabled_idx'
            ),
        ),
        
        migrations.AddIndex(
            model_name='reminderlog',
            index=models.Index(
                fields=['contract', '-scheduled_date'],
                name='log_contract_scheduled_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='reminderlog',
            index=models.Index(
                fields=['reminder_type', 'status'],
                name='log_type_status_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='reminderlog',
            index=models.Index(
                fields=['sent_date'],
                name='log_sent_date_idx'
            ),
        ),
        
        # Add unique constraint for global reminders
        migrations.AddConstraint(
            model_name='reminderconfiguration',
            constraint=models.UniqueConstraint(
                condition=models.Q(('contract_type__isnull', True), ('contract__isnull', True)),
                fields=['reminder_type', 'scope'],
                name='unique_global_reminder'
            ),
        ),
    ]
