"""
Management command to initialize default role-permission mappings
Usage: python manage.py setup_permissions
"""
from django.core.management.base import BaseCommand
from contracts.models import ContractRolePermission, ParticipantRole, ContractPermission
from contracts.permissions import PERMISSION_ROLE_MAP


class Command(BaseCommand):
    help = 'Initialize default role-permission mappings from PERMISSION_ROLE_MAP'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing permissions and recreate from defaults',
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)

        if reset:
            self.stdout.write(self.style.WARNING('Resetting all permissions...'))
            deleted_count = ContractRolePermission.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing permissions'))

        self.stdout.write('Setting up role-permission mappings...')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        # Iterate through the permission map
        for permission, allowed_roles in PERMISSION_ROLE_MAP.items():
            for role in ParticipantRole:
                is_allowed = role in allowed_roles

                # Try to get existing permission
                perm, created = ContractRolePermission.objects.get_or_create(
                    role=role,
                    permission=permission,
                    defaults={'allowed': is_allowed}
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Created: {role.label} → {permission.label} = {is_allowed}'
                        )
                    )
                else:
                    # Update if different
                    if perm.allowed != is_allowed and not reset:
                        # Don't auto-update if not in reset mode (preserve manual changes)
                        skipped_count += 1
                        self.stdout.write(
                            self.style.NOTICE(
                                f'○ Exists: {role.label} → {permission.label} (keeping existing: {perm.allowed})'
                            )
                        )
                    elif perm.allowed != is_allowed:
                        # Update in reset mode
                        perm.allowed = is_allowed
                        perm.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'↻ Updated: {role.label} → {permission.label} = {is_allowed}'
                            )
                        )
                    else:
                        skipped_count += 1

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Created: {created_count}'))
        if updated_count > 0:
            self.stdout.write(self.style.WARNING(f'↻ Updated: {updated_count}'))
        self.stdout.write(self.style.NOTICE(f'○ Unchanged: {skipped_count}'))
        self.stdout.write('='*60)
        
        if not reset and skipped_count > 0:
            self.stdout.write(
                self.style.NOTICE(
                    '\nℹ Some permissions already exist with different values.'
                )
            )
            self.stdout.write(
                self.style.NOTICE(
                    '  Use --reset flag to overwrite with defaults.'
                )
            )

        self.stdout.write(self.style.SUCCESS('\n✓ Permission setup complete!'))
