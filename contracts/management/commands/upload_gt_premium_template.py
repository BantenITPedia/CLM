from pathlib import Path

import mammoth
from django.core.management.base import BaseCommand

from contracts.models import ContractTemplate, ContractType, ContractTypeDefinition


class Command(BaseCommand):
    help = 'Upload General Trade Premium template from the legacy Premium DOCX file'

    def handle(self, *args, **options):
        contract_type, created = ContractTypeDefinition.objects.get_or_create(
            code=ContractType.GENERAL_TRADE_PREMIUM,
            defaults={
                'name': 'General Trade Agreement - Premium',
                'description': 'Premium General Trade Agreement template',
                'is_template_based': True,
                'active': True,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created contract type: {contract_type.name}'))
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
                self.stdout.write(self.style.SUCCESS(f'Updated contract type: {contract_type.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Using existing contract type: {contract_type.name}'))

        template_path = (
            Path(__file__).parent.parent.parent.parent
            / 'contract agreement'
            / 'Template Agreement GT_RestrictedFinal - Premium Comodity.docx'
        )

        if not template_path.exists():
            self.stdout.write(self.style.ERROR(f'Template file not found: {template_path}'))
            return

        with template_path.open('rb') as docx_file:
            result = mammoth.convert_to_html(docx_file)

        template_content = result.value or ''
        if not template_content.strip():
            self.stdout.write(self.style.ERROR('Converted Premium template is empty'))
            return

        template, created = ContractTemplate.objects.update_or_create(
            contract_type=contract_type,
            name='General Trade Agreement Premium - Legacy Import',
            defaults={
                'content': template_content,
                'active': True,
            },
        )

        ContractTemplate.objects.filter(contract_type=contract_type).exclude(id=template.id).update(active=False)

        self.stdout.write(self.style.SUCCESS('✓ Premium template uploaded and activated successfully!'))
        self.stdout.write(f'  Contract Type: {contract_type.name}')
        self.stdout.write(f'  Template Name: {template.name}')
        self.stdout.write(f'  Template ID: {template.id}')
        self.stdout.write(f'  Content Length: {len(template_content)} characters')
        if result.messages:
            self.stdout.write('  Conversion warnings:')
            for message in result.messages:
                self.stdout.write(f'   - {message}')