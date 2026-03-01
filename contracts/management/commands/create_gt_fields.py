"""
Management command to create contract fields for GT (General Trade Agreement) template.
"""
from django.core.management.base import BaseCommand
from contracts.models import ContractTypeDefinition, ContractField


class Command(BaseCommand):
    help = 'Create contract fields for General Trade Agreement template'

    def handle(self, *args, **options):
        try:
            # Get the General Trade contract type
            contract_type = ContractTypeDefinition.objects.get(code='GENERAL_TRADE')
            
            # Define fields for GT Agreement
            fields_data = [
                {
                    'field_key': 'party_b_name',
                    'label': 'Party B - Company Name',
                    'field_type': 'text',
                    'required': True,
                    'position': 1,
                },
                {
                    'field_key': 'party_b_address',
                    'label': 'Party B - Legal Address',
                    'field_type': 'text',
                    'required': True,
                    'position': 3,
                },
                {
                    'field_key': 'delivery_address',
                    'label': 'Delivery Address',
                    'field_type': 'text',
                    'required': True,
                    'position': 4,
                },
                {
                    'field_key': 'business_form',
                    'label': 'Business Form (Bentuk Usaha)',
                    'field_type': 'select',
                    'required': True,
                    'position': 5,
                    'options': ['CV', 'Usaha Perseorangan', 'Badan Hukum Perseroan Terbatas'],
                },
                {
                    'field_key': 'party_b_representative',
                    'label': 'Party B - Representative Name',
                    'field_type': 'text',
                    'required': True,
                    'position': 6,
                },
                {
                    'field_key': 'party_b_representative_title',
                    'label': 'Party B - Representative Title',
                    'field_type': 'text',
                    'required': True,
                    'position': 7,
                },
                {
                    'field_key': 'contract_start_date',
                    'label': 'Contract Start Date',
                    'field_type': 'date',
                    'required': True,
                    'position': 8,
                },
                {
                    'field_key': 'contract_end_date',
                    'label': 'Contract End Date',
                    'field_type': 'date',
                    'required': True,
                    'position': 9,
                },
                {
                    'field_key': 'quarter_1_period',
                    'label': 'Quarter I Period (Months)',
                    'field_type': 'text',
                    'required': True,
                    'position': 10,
                },
                {
                    'field_key': 'sales_target_q1',
                    'label': 'Sales Target Q1 (in Rp)',
                    'field_type': 'number',
                    'required': True,
                    'position': 11,
                },
                {
                    'field_key': 'quarter_2_period',
                    'label': 'Quarter II Period (Months)',
                    'field_type': 'text',
                    'required': True,
                    'position': 12,
                },
                {
                    'field_key': 'sales_target_q2',
                    'label': 'Sales Target Q2 (in Rp)',
                    'field_type': 'number',
                    'required': True,
                    'position': 13,
                },
                {
                    'field_key': 'quarter_3_period',
                    'label': 'Quarter III Period (Months)',
                    'field_type': 'text',
                    'required': True,
                    'position': 14,
                },
                {
                    'field_key': 'sales_target_q3',
                    'label': 'Sales Target Q3 (in Rp)',
                    'field_type': 'number',
                    'required': True,
                    'position': 15,
                },
                {
                    'field_key': 'quarter_4_period',
                    'label': 'Quarter IV Period (Months)',
                    'field_type': 'text',
                    'required': True,
                    'position': 16,
                },
                {
                    'field_key': 'sales_target_q4',
                    'label': 'Sales Target Q4 (in Rp)',
                    'field_type': 'number',
                    'required': True,
                    'position': 17,
                },
                {
                    'field_key': 'total_purchase_target',
                    'label': 'Total Annual Purchase Target (in Rp)',
                    'field_type': 'number',
                    'required': True,
                    'position': 18,
                },
                {
                    'field_key': 'incentive_percentage',
                    'label': 'Incentive Percentage (%)',
                    'field_type': 'number',
                    'required': False,
                    'position': 19,
                },
                {
                    'field_key': 'product_types',
                    'label': 'Product Types',
                    'field_type': 'text',
                    'required': False,
                    'position': 20,
                },
                {
                    'field_key': 'cvcode_number',
                    'label': 'CVCODE Number',
                    'field_type': 'text',
                    'required': False,
                    'position': 21,
                },
            ]
            
            created_count = 0
            skipped_count = 0
            
            # Create or update fields
            for field_data in fields_data:
                field, created = ContractField.objects.update_or_create(
                    contract_type=contract_type,
                    field_key=field_data['field_key'],
                    defaults={
                        'label': field_data['label'],
                        'field_type': field_data['field_type'],
                        'required': field_data['required'],
                        'position': field_data['position'],
                        'options': field_data.get('options'),
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✓ Created: {field_data["label"]}')
                else:
                    skipped_count += 1
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully created {created_count} contract fields!'))
            if skipped_count > 0:
                self.stdout.write(self.style.WARNING(f'  ({skipped_count} fields already existed)'))
            
            self.stdout.write('')
            self.stdout.write('Fields are now available in the form:')
            self.stdout.write('  1. Go to: http://localhost/contracts/create/')
            self.stdout.write('  2. Select "General Trade Agreement" as contract type')
            self.stdout.write('  3. Fill in all fields')
            self.stdout.write('  4. Submit to generate draft from template!')
            
        except ContractTypeDefinition.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Error: General Trade Agreement contract type not found!')
            )
            self.stdout.write('Run: python manage.py upload_gt_template')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
