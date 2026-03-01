from django.db import migrations, models
import django.db.models.deletion


def seed_contract_type_definitions(apps, schema_editor):
    ContractTypeDefinition = apps.get_model('contracts', 'ContractTypeDefinition')
    for code, label in [
        ('NDA', 'Non-Disclosure Agreement'),
        ('VENDOR', 'Vendor Agreement'),
        ('SERVICE', 'Service Agreement'),
        ('EMPLOYMENT', 'Employment Contract'),
        ('LEASE', 'Lease Agreement'),
        ('PURCHASE', 'Purchase Agreement'),
        ('OTHER', 'Other'),
    ]:
        ContractTypeDefinition.objects.get_or_create(code=code, defaults={'name': label, 'description': label})


def default_contract_status_choices():
    return [
        ('DRAFT', 'Draft'),
        ('DATA_COMPLETED', 'Data Completed'),
        ('PENDING_REVIEW', 'Pending Review'),
        ('LEGAL_REVIEW', 'Legal Review'),
        ('APPROVED', 'Approved'),
        ('PENDING_SIGNATURE', 'Pending Signature'),
        ('SIGNED', 'Signed'),
        ('ACTIVE', 'Active'),
        ('EXPIRING_SOON', 'Expiring Soon'),
        ('EXPIRED', 'Expired'),
        ('RENEWED', 'Renewed'),
        ('TERMINATED', 'Terminated'),
    ]


def default_audit_action_choices():
    return [
        ('CREATE', 'Contract Created'),
        ('UPDATE', 'Contract Updated'),
        ('STATUS_CHANGE', 'Status Changed'),
        ('DOCUMENT_UPLOAD', 'Document Uploaded'),
        ('PARTICIPANT_ADDED', 'Participant Added'),
        ('PARTICIPANT_REMOVED', 'Participant Removed'),
        ('SIGNATURE_ADDED', 'Signature Added'),
        ('EMAIL_SENT', 'Email Sent'),
        ('RENEWAL_REMINDER', 'Renewal Reminder Sent'),
        ('EXPIRY_CHECK', 'Expiry Check Performed'),
        ('AUTO_RENEWAL', 'Auto Renewal Created'),
        ('COMMENT_ADDED', 'Comment Added'),
        ('APPROVAL_REQUESTED', 'Approval Requested'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('DATA_SUBMITTED', 'Structured Data Submitted'),
        ('DRAFT_GENERATED', 'Draft Generated'),
        ('DRAFT_UPDATED', 'Draft Updated'),
    ]


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContractTypeDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(choices=[('NDA', 'Non-Disclosure Agreement'), ('VENDOR', 'Vendor Agreement'), ('SERVICE', 'Service Agreement'), ('EMPLOYMENT', 'Employment Contract'), ('LEASE', 'Lease Agreement'), ('PURCHASE', 'Purchase Agreement'), ('OTHER', 'Other')], help_text='Internal contract type code (matches Contract.contract_type)', max_length=20, unique=True)),
                ('name', models.CharField(help_text='Display name for admin use', max_length=255)),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='ContractTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('content', models.TextField(help_text='Use Django template variables like {{ party_name }}')),
                ('active', models.BooleanField(default=True)),
                ('version', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('contract_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='templates', to='contracts.contracttypedefinition')),
            ],
            options={'ordering': ['contract_type', '-active', '-version', 'name']},
        ),
        migrations.CreateModel(
            name='ContractField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_key', models.CharField(help_text='Template variable name', max_length=100)),
                ('label', models.CharField(max_length=255)),
                ('field_type', models.CharField(choices=[('text', 'Text'), ('number', 'Number'), ('date', 'Date'), ('select', 'Select')], max_length=20)),
                ('required', models.BooleanField(default=False)),
                ('options', models.JSONField(blank=True, help_text='Options for select fields', null=True)),
                ('position', models.PositiveIntegerField(default=0)),
                ('contract_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='contracts.contracttypedefinition')),
            ],
            options={'ordering': ['contract_type', 'position', 'label']},
        ),
        migrations.CreateModel(
            name='ContractDraft',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveIntegerField(default=1)),
                ('file', models.FileField(upload_to='contract_drafts/%Y/%m/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='ContractData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.JSONField(blank=True, default=dict)),
                ('submitted_at', models.DateTimeField(auto_now=True)),
                ('contract', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='structured_data', to='contracts.contract')),
            ],
        ),
        migrations.AlterField(
            model_name='contract',
            name='status',
            field=models.CharField(choices=default_contract_status_choices(), default='DRAFT', max_length=20),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(choices=default_audit_action_choices(), max_length=50),
        ),
        migrations.AddField(
            model_name='contractdraft',
            name='contract',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drafts', to='contracts.contract'),
        ),
        migrations.AddField(
            model_name='contractdraft',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='drafts', to='contracts.contracttemplate'),
        ),
        migrations.AddConstraint(
            model_name='contractfield',
            constraint=models.UniqueConstraint(fields=('contract_type', 'field_key'), name='contracts_contractfield_unique_field'),
        ),
        migrations.AddConstraint(
            model_name='contractdraft',
            constraint=models.UniqueConstraint(fields=('contract', 'version'), name='contracts_draft_unique_version'),
        ),
        migrations.RunPython(seed_contract_type_definitions, reverse_code=migrations.RunPython.noop),
    ]
