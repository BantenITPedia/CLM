from django.db import migrations


def seed_global_rbac_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    contracts_permissions = Permission.objects.filter(content_type__app_label='contracts')

    clm_admin_group, _ = Group.objects.get_or_create(name='CLM Admin')
    clm_legal_group, _ = Group.objects.get_or_create(name='CLM Legal')
    clm_sales_group, _ = Group.objects.get_or_create(name='CLM Sales')
    clm_viewer_group, _ = Group.objects.get_or_create(name='CLM Viewer')

    # Full access to all contracts app permissions.
    clm_admin_group.permissions.set(contracts_permissions)

    legal_codenames = {
        'view_contract',
        'change_contract',
        'view_contractparticipant',
        'change_contractparticipant',
        'view_contractdocument',
        'add_contractdocument',
        'change_contractdocument',
        'delete_contractdocument',
        'view_comment',
        'add_comment',
        'change_comment',
        'view_businessentitydocument',
        'change_businessentitydocument',
        'view_finalapproveddocument',
        'add_finalapproveddocument',
        'change_finalapproveddocument',
        'view_contractrolepermission',
        'change_companyprofile',
    }
    clm_legal_group.permissions.set(contracts_permissions.filter(codename__in=legal_codenames))

    sales_codenames = {
        'view_contract',
        'add_contract',
        'change_contract',
        'view_contractparticipant',
        'add_contractparticipant',
        'change_contractparticipant',
        'view_contractdocument',
        'add_contractdocument',
        'change_contractdocument',
        'view_comment',
        'add_comment',
        'change_comment',
        'view_contractdata',
        'change_contractdata',
    }
    clm_sales_group.permissions.set(contracts_permissions.filter(codename__in=sales_codenames))

    viewer_codenames = {
        'view_contract',
        'view_contractparticipant',
        'view_contractdocument',
        'view_comment',
        'view_contractdata',
        'view_contracttemplate',
    }
    clm_viewer_group.permissions.set(contracts_permissions.filter(codename__in=viewer_codenames))


def unseed_global_rbac_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['CLM Admin', 'CLM Legal', 'CLM Sales', 'CLM Viewer']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0040_seed_comment_added_notification_template'),
    ]

    operations = [
        migrations.RunPython(seed_global_rbac_groups, unseed_global_rbac_groups),
    ]
