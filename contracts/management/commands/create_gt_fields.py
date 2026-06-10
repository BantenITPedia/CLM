"""Management command to seed template fields for selected contract types."""
from django.core.management.base import BaseCommand

from contracts.models import ContractField, ContractType, ContractTypeDefinition


class Command(BaseCommand):
    help = 'Create contract fields for selected contract type (default: GENERAL_TRADE)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contract-type',
            default=ContractType.GENERAL_TRADE,
            choices=[ContractType.GENERAL_TRADE, ContractType.DISTRIBUTOR],
            help='Contract type code to seed fields for'
        )

    def _gt_fields(self):
        return [
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

    def _distributor_fields(self):
        return [
            {
                'field_key': 'target_schema',
                'label': 'Target Schema',
                'field_type': 'select',
                'required': True,
                'position': 1,
                'options': ['yearly_only', 'quarterly', 'custom_period'],
            },
            {
                'field_key': 'party_b_name',
                'label': 'Pihak Kedua - Nama Perusahaan',
                'field_type': 'text',
                'required': True,
                'position': 2,
            },
            {
                'field_key': 'party_b_registered_address',
                'label': 'Pihak Kedua - Alamat Terdaftar',
                'field_type': 'text',
                'required': True,
                'position': 3,
            },
            {
                'field_key': 'party_b_representative_name',
                'label': 'Pihak Kedua - Nama Perwakilan',
                'field_type': 'text',
                'required': True,
                'position': 4,
            },
            {
                'field_key': 'party_b_representative_title',
                'label': 'Pihak Kedua - Jabatan Perwakilan',
                'field_type': 'text',
                'required': True,
                'position': 5,
            },
            {
                'field_key': 'second_party_place_name',
                'label': 'Lampiran A - Nama Tempat Pihak Kedua',
                'field_type': 'text',
                'required': True,
                'position': 6,
            },
            {
                'field_key': 'second_party_place_address',
                'label': 'Lampiran A - Alamat Tempat Pihak Kedua',
                'field_type': 'text',
                'required': False,
                'position': 7,
            },
            {
                'field_key': 'delivery_address',
                'label': 'Lampiran A - Alamat Pengiriman / Delivery Address',
                'field_type': 'text',
                'required': True,
                'position': 7.5,
                'help_text': 'Alamat pengiriman produk ke tempat Pihak Kedua',
            },
            {
                'field_key': 'cvcode_number',
                'label': 'Lampiran A - Nomor CVCODE',
                'field_type': 'text',
                'required': False,
                'position': 8,
            },
            {
                'field_key': 'second_party_criteria',
                'label': 'Lampiran A - Kriteria Pihak Kedua (Entity Type)',
                'field_type': 'select',
                'required': False,
                'position': 9,
                'options': ['PT', 'CV', 'PERORANGAN'],
            },
            {
                'field_key': 'percentage_benefit',
                'label': 'Lampiran A - Persentase Benefit / Kriteria',
                'field_type': 'text',
                'required': True,
                'position': 9.5,
                'help_text': 'Isikan dengan kesepakatan antara PCI & distributor',
            },
            {
                'field_key': 'product_scope_text_distributor',
                'label': 'Lampiran A - Jenis Produk',
                'field_type': 'text',
                'required': False,
                'position': 10,
            },
            {
                'field_key': 'wilayah_operasional',
                'label': 'Pasal 2 - Wilayah Operasional',
                'field_type': 'text',
                'required': True,
                'position': 11,
            },
            {
                'field_key': 'total_purchase_target',
                'label': 'Lampiran B - Total Target Pembelian (Rp)',
                'field_type': 'number',
                'required': True,
                'position': 12,
            },
            {
                'field_key': 'total_target_qtr',
                'label': 'Lampiran B - Total Target Quarterly',
                'field_type': 'number',
                'required': False,
                'position': 13,
            },
            {
                'field_key': 'quarter_1_period',
                'label': 'Lampiran B - Periode Q1',
                'field_type': 'text',
                'required': False,
                'position': 14,
            },
            {
                'field_key': 'sales_target_q1',
                'label': 'Lampiran B - Target Q1 (Rp)',
                'field_type': 'number',
                'required': False,
                'position': 15,
            },
            {
                'field_key': 'quarter_2_period',
                'label': 'Lampiran B - Periode Q2',
                'field_type': 'text',
                'required': False,
                'position': 16,
            },
            {
                'field_key': 'sales_target_q2',
                'label': 'Lampiran B - Target Q2 (Rp)',
                'field_type': 'number',
                'required': False,
                'position': 17,
            },
            {
                'field_key': 'quarter_3_period',
                'label': 'Lampiran B - Periode Q3',
                'field_type': 'text',
                'required': False,
                'position': 18,
            },
            {
                'field_key': 'sales_target_q3',
                'label': 'Lampiran B - Target Q3 (Rp)',
                'field_type': 'number',
                'required': False,
                'position': 19,
            },
            {
                'field_key': 'quarter_4_period',
                'label': 'Lampiran B - Periode Q4',
                'field_type': 'text',
                'required': False,
                'position': 20,
            },
            {
                'field_key': 'sales_target_q4',
                'label': 'Lampiran B - Target Q4 (Rp)',
                'field_type': 'number',
                'required': False,
                'position': 21,
            },
            {
                'field_key': 'non_prd_list',
                'label': 'Lampiran B - Non Product List',
                'field_type': 'text',
                'required': False,
                'position': 22,
            },
            {
                'field_key': 'inc_prd_list',
                'label': 'Lampiran B - Included Product List',
                'field_type': 'text',
                'required': False,
                'position': 23,
            },
            {
                'field_key': 'bank_grt',
                'label': 'Lampiran B - Bank Guarantee Minimum',
                'field_type': 'number',
                'required': False,
                'position': 24,
            },
            {
                'field_key': 'custom_period_target_notes',
                'label': 'Lampiran B - Catatan Target Periode Khusus',
                'field_type': 'text',
                'required': False,
                'position': 25,
            },
            {
                'field_key': 'incentive_scheme_text_distributor',
                'label': 'Lampiran C - Skema Insentif',
                'field_type': 'text',
                'required': False,
                'position': 26,
            },
            {
                'field_key': 'incentive_scheme_notes',
                'label': 'Lampiran C - Catatan Skema Insentif',
                'field_type': 'text',
                'required': False,
                'position': 27,
            },
        ]

    def handle(self, *args, **options):
        try:
            selected_type = options['contract_type']
            contract_type = ContractTypeDefinition.objects.get(code=selected_type)
            fields_data = self._distributor_fields() if selected_type == ContractType.DISTRIBUTOR else self._gt_fields()
            
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
            self.stdout.write(f'Fields are now available for contract type: {selected_type}')
            
        except ContractTypeDefinition.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Error: contract type {options["contract_type"]} not found!')
            )
            self.stdout.write('Run: python manage.py upload_gt_template')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
