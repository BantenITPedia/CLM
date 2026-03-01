from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from contracts.models import ContractRolePermission, ContractPermission, ParticipantRole


class Command(BaseCommand):
    help = 'Set up Document Administration group with final document upload permission'

    def handle(self, *args, **options):
        # Create Document Administration group if it doesn't exist
        doc_admin_group, created = Group.objects.get_or_create(name='Document Administration')
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created "Document Administration" group'))
        else:
            self.stdout.write(self.style.WARNING('⚠ "Document Administration" group already exists'))
        
        # Set up permission mappings for Document Administration
        # They should have upload_final_document permission
        permissions_to_grant = [
            ContractPermission.UPLOAD_FINAL_DOCUMENT,
            ContractPermission.VIEW_CONTRACT,
            ContractPermission.ADD_DOCUMENT,
        ]
        
        for permission in permissions_to_grant:
            # For each legal role (LEGAL, OWNER), grant this permission to Document Admin users
            for role in [ParticipantRole.OWNER, ParticipantRole.LEGAL]:
                perm_entry, created = ContractRolePermission.objects.get_or_create(
                    permission=permission,
                    role=role,
                    defaults={'allowed': True}
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Granted {permission} to {role} role')
                    )
        
        self.stdout.write(self.style.SUCCESS('✓ Document Administration setup complete!'))
        self.stdout.write(self.style.WARNING(
            'Note: Add users to the "Document Administration" group in Django admin to enable final document uploads'
        ))
