from django.db import migrations, models


def seed_role_permissions(apps, schema_editor):
    ContractRolePermission = apps.get_model('contracts', 'ContractRolePermission')

    roles = ['OWNER', 'SALES', 'LEGAL', 'CUSTOMER', 'SIGNATORY', 'APPROVER']
    permissions = [
        'view_contract',
        'edit_contract',
        'delete_contract',
        'update_status',
        'manage_participants',
        'add_document',
        'add_comment',
        'edit_structured_data',
        'regenerate_draft',
    ]

    default_map = {
        'view_contract': {'OWNER', 'SALES', 'LEGAL', 'CUSTOMER', 'APPROVER', 'SIGNATORY'},
        'edit_contract': {'OWNER', 'SALES'},
        'delete_contract': {'OWNER'},
        'update_status': {'OWNER', 'LEGAL', 'APPROVER'},
        'manage_participants': {'OWNER', 'LEGAL'},
        'add_document': {'OWNER', 'SALES', 'LEGAL'},
        'add_comment': {'OWNER', 'SALES', 'LEGAL', 'CUSTOMER', 'APPROVER'},
        'edit_structured_data': {'OWNER', 'SALES', 'LEGAL'},
        'regenerate_draft': {'LEGAL'},
    }

    for permission in permissions:
        allowed_roles = default_map.get(permission, set())
        for role in roles:
            ContractRolePermission.objects.update_or_create(
                role=role,
                permission=permission,
                defaults={'allowed': role in allowed_roles}
            )


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0013_increase_contract_value_max'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContractRolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('OWNER', 'Contract Owner'), ('SALES', 'Sales Representative'), ('LEGAL', 'Legal Reviewer'), ('CUSTOMER', 'Customer'), ('SIGNATORY', 'Signatory'), ('APPROVER', 'Approver')], max_length=20)),
                ('permission', models.CharField(choices=[('view_contract', 'View contract'), ('edit_contract', 'Edit contract'), ('delete_contract', 'Delete contract'), ('update_status', 'Update status'), ('manage_participants', 'Manage participants'), ('add_document', 'Add documents'), ('add_comment', 'Add comments'), ('edit_structured_data', 'Edit structured data'), ('regenerate_draft', 'Regenerate drafts')], max_length=32)),
                ('allowed', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'indexes': [models.Index(fields=['role', 'permission'], name='contracts_c_role_pe_6f5f66_idx')],
                'unique_together': {('role', 'permission')},
            },
        ),
        migrations.RunPython(seed_role_permissions, migrations.RunPython.noop),
    ]
