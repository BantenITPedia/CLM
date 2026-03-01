"""
Management command to upload GT (General Trade) template to the system.
"""
from django.core.management.base import BaseCommand
from pathlib import Path
from contracts.models import ContractTypeDefinition, ContractTemplate


class Command(BaseCommand):
    help = 'Upload General Trade Agreement template from HTML file'

    def handle(self, *args, **options):
        try:
            # Get or create the General Trade contract type definition
            contract_type, created = ContractTypeDefinition.objects.get_or_create(
                code='GENERAL_TRADE',
                defaults={
                    'name': 'General Trade Agreement',
                    'description': 'General Trade Agreement Template',
                    'is_template_based': True,
                    'active': True,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created contract type: {contract_type.name}')
                )
            else:
                updates = {}
                if not contract_type.is_template_based:
                    updates['is_template_based'] = True
                if not contract_type.active:
                    updates['active'] = True
                if updates:
                    for key, value in updates.items():
                        setattr(contract_type, key, value)
                    contract_type.save(update_fields=list(updates.keys()))
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated contract type: {contract_type.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Using existing contract type: {contract_type.name}')
                    )
            
            # Read the HTML template file
            template_path = Path(__file__).parent.parent.parent.parent / 'contract agreement' / 'Template Agreement GT_ Supporting Legal System.htm'
            
            if not template_path.exists():
                self.stdout.write(
                    self.style.ERROR(f'Template file not found: {template_path}')
                )
                return
            
            with open(template_path, 'r', encoding='windows-1252') as f:
                template_content = f.read()
            
            # Create or update the template
            template, created = ContractTemplate.objects.update_or_create(
                contract_type=contract_type,
                name='General Trade Agreement - Supporting Legal System',
                defaults={
                    'content': template_content,
                    'active': True,
                }
            )
            
            ContractTemplate.objects.filter(
                contract_type=contract_type
            ).exclude(id=template.id).update(active=False)

            self.stdout.write(
                self.style.SUCCESS('✓ Template uploaded and activated successfully!')
            )
            self.stdout.write(f'  Contract Type: {contract_type.name}')
            self.stdout.write(f'  Template Name: {template.name}')
            self.stdout.write(f'  Version: {template.version}')
            self.stdout.write(f'  Template ID: {template.id}')
            self.stdout.write(f'  Content Length: {len(template_content)} characters')
            self.stdout.write('')
            self.stdout.write('Next steps:')
            self.stdout.write('  1. Go to Admin: http://localhost/admin')
            self.stdout.write('  2. Navigate to: Contracts > Contract Fields')
            self.stdout.write('  3. Add/update fields for this contract type')
            self.stdout.write('  4. Then create contracts and generate drafts!')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error uploading template: {str(e)}')
            )
