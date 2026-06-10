"""
Management command to upload GT (General Trade) template to the system.
"""
import mammoth
import re
from django.core.management.base import BaseCommand
from pathlib import Path
from contracts.models import ContractTemplate, ContractType, ContractTypeDefinition


DISTRIBUTOR_TEMPLATE_CONTENT = """<!DOCTYPE html>
<html lang=\"id\">
<head>
    <meta charset=\"UTF-8\">
    <title>Perjanjian Kerja Sama Keagenan</title>
</head>
<body>
    <h2 style=\"text-align:center;\">PERJANJIAN KERJA SAMA KEAGENAN</h2>
    <p style=\"text-align:center;\">Nomor: {{ contract_number }}</p>

    <p>Perjanjian ini dibuat dan ditandatangani pada tanggal {{ contract_signing_date }} antara {{ party_a }} dan {{ party_b_name|default:party_b }}.</p>

    <h3>Lampiran A</h3>
    <p>Nama Tempat Pihak Kedua: {{ second_party_place_name|default:party_b_name|default:party_b }}</p>
    <p>Nomor CVCODE: {{ cvcode_number|default:'-' }}</p>
    <p>Alamat Tempat Pihak Kedua: {{ second_party_place_address|default:party_b_registered_address|default:'-' }}</p>
    <p>Kriteria Pihak Kedua: {{ second_party_criteria|default:'-' }}</p>
    <p>Jenis Produk: {{ product_scope_text_distributor|default:product_scope_text|default:'-' }}</p>

    <h3>Lampiran B</h3>
    {% if target_schema == 'quarterly' %}
    <table border=\"1\" cellspacing=\"0\" cellpadding=\"6\" width=\"100%\">
        <tr><th>Periode</th><th>Target (Rp)</th></tr>
        <tr><td>{{ quarter_1_period|default:q1_period|default:'Q1' }}</td><td>{{ sales_target_q1|default:q1_sales_target|default:'-' }}</td></tr>
        <tr><td>{{ quarter_2_period|default:q2_period|default:'Q2' }}</td><td>{{ sales_target_q2|default:q2_sales_target|default:'-' }}</td></tr>
        <tr><td>{{ quarter_3_period|default:q3_period|default:'Q3' }}</td><td>{{ sales_target_q3|default:q3_sales_target|default:'-' }}</td></tr>
        <tr><td>{{ quarter_4_period|default:q4_period|default:'Q4' }}</td><td>{{ sales_target_q4|default:q4_sales_target|default:'-' }}</td></tr>
        <tr><td><strong>Total</strong></td><td><strong>{{ total_purchase_target|default:total_annual_purchase_target|default:contract_value|default:'-' }}</strong></td></tr>
    </table>
    {% elif target_schema == 'custom_period' %}
    <p>{{ custom_period_target_notes|default:'Skema target periode khusus mengikuti ketentuan internal yang disepakati Para Pihak.' }}</p>
    <p>Total Target: {{ total_purchase_target|default:total_annual_purchase_target|default:contract_value|default:'-' }}</p>
    {% else %}
    <p>Total target pembelian Produk: <strong>{{ total_purchase_target_formatted|default:total_purchase_target|default:total_annual_purchase_target|default:contract_value|default:'-' }}</strong>.</p>
    {% endif %}

    <h3>Lampiran C</h3>
    <p>{{ incentive_scheme_text_distributor|default:incentive_scheme_text|default:'Skema insentif mengikuti ketentuan Pihak Pertama.' }}</p>
    {% if incentive_scheme_notes %}<p>Catatan: {{ incentive_scheme_notes }}</p>{% endif %}
</body>
</html>
"""


def _normalize_distributor_html(converted_html):
    """Add base styling and normalize known placeholder artifacts from DOCX conversion."""
    html = converted_html or ''

    replacements = {
        'tanggal contract': '',
    }
    for old, new in replacements.items():
        html = html.replace(old, new)

    html = re.sub(r'<em>\s*start_date\s*</em>', '{{ contract_start_date }}', html, flags=re.IGNORECASE)
    html = re.sub(r'<em>\s*end_date\s*</em>', '{{ contract_end_date }}', html, flags=re.IGNORECASE)
    html = re.sub(r'\bstart_date\b', '{{ contract_start_date }}', html, flags=re.IGNORECASE)
    html = re.sub(r'\bend_date\b', '{{ contract_end_date }}', html, flags=re.IGNORECASE)

    # Ensure key identity placeholders are dynamic in intro block.
    html = re.sub(r'Nomor\.\s*<em>.*?</em>', 'Nomor. <em>{{ contract_number }}</em>', html, flags=re.IGNORECASE)

    lampiran_a_block = """
<p><strong>Lampiran A</strong></p>
<p><strong>Syarat dan Ketentuan</strong></p>
<p><strong>Nomor. {{ contract_number }}</strong></p>
<table>
    <tr>
        <td><p>Nama Tempat Pihak Kedua</p><p><em>Second Party Place</em></p></td>
        <td><p><strong>{{ second_party_place_name|default:party_b_legal_name }}</strong></p></td>
    </tr>
    <tr>
        <td><p>Nomor CVCODE</p><p><em>CVCODE Number</em></p></td>
        <td><p><strong>{{ cvcode_number|default:'-' }}</strong></p></td>
    </tr>
    <tr>
        <td><p>Alamat Tempat</p><p><em>Addresses of Second Party Place</em></p></td>
        <td><p><strong>{{ second_party_place_address|default:party_b_registered_address|default:'-' }}</strong></p></td>
    </tr>
    <tr>
        <td><p>Kriteria Pihak Kedua</p><p><em>Second Party criteria</em></p></td>
        <td><p><strong>{{ second_party_criteria|default:'-' }}</strong></p></td>
    </tr>
    <tr>
        <td><p>Jenis Produk</p><p><em>Product</em></p></td>
        <td><p>{{ product_scope_text_distributor|default:product_scope_text|default:'-' }}</p></td>
    </tr>
</table>
"""

    lampiran_b_block = """
<p><strong>Lampiran B</strong></p>
<p><strong>Target Sales / <em>Sales Target</em></strong></p>
<p><strong>Nomor. {{ contract_number }}</strong></p>
{% if target_schema == 'quarterly' %}
<table>
    <tr><td>{{ quarter_1_period|default:q1_period|default:'Q1' }}</td><td><strong>{{ sales_target_q1|default:q1_sales_target|default:'-' }}</strong></td></tr>
    <tr><td>{{ quarter_2_period|default:q2_period|default:'Q2' }}</td><td><strong>{{ sales_target_q2|default:q2_sales_target|default:'-' }}</strong></td></tr>
    <tr><td>{{ quarter_3_period|default:q3_period|default:'Q3' }}</td><td><strong>{{ sales_target_q3|default:q3_sales_target|default:'-' }}</strong></td></tr>
    <tr><td>{{ quarter_4_period|default:q4_period|default:'Q4' }}</td><td><strong>{{ sales_target_q4|default:q4_sales_target|default:'-' }}</strong></td></tr>
    <tr><td><strong>Total Target Quarterly</strong></td><td><strong>{{ total_purchase_target|default:'-' }}</strong></td></tr>
    <tr><td><strong>Total Target Yearly</strong></td><td><strong>{{ total_annual_purchase_target|default:total_purchase_target|default:'-' }}</strong></td></tr>
</table>
{% elif target_schema == 'custom_period' %}
<p>{{ custom_period_target_notes|default:'Skema target periode khusus mengikuti kesepakatan para pihak.' }}</p>
<p><strong>Total Target:</strong> {{ total_purchase_target|default:total_annual_purchase_target|default:'-' }}</p>
{% else %}
<p><strong>Total Target Yearly:</strong> {{ total_annual_purchase_target|default:total_purchase_target|default:'-' }}</p>
{% endif %}
<table>
    <tr>
        <td>Bahwa untuk total target pembelian atas Produk yang wajib dilakukan oleh Pihak Kedua yaitu sebesar <strong>{{ total_purchase_target_formatted|default:total_purchase_target|default:'-' }}</strong>.</td>
        <td>Whereas the total purchase target for Products that must be carried out by the Second Party is <strong>{{ total_purchase_target|default:'-' }}</strong>.</td>
    </tr>
</table>
"""

    lampiran_c_block = """
<p><strong>Lampiran C</strong></p>
<p><strong>Skema Insentif / Incentive Scheme</strong></p>
<p><strong>Nomor. {{ contract_number }}</strong></p>
<p>{{ incentive_scheme_text_distributor|default:incentive_scheme_text|default:'-' }}</p>
{% if incentive_scheme_notes %}
<p>Keterangan / <em>Note</em>: {{ incentive_scheme_notes }}</p>
{% endif %}
"""

    html = re.sub(
        r'<p><strong>\s*Lampiran\s*A\s*</strong></p>.*?(?=<p><strong>\s*Lampiran\s*B\s*</strong></p>)',
        lampiran_a_block,
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html = re.sub(
        r'<p><strong>\s*Lampiran\s*B\s*</strong></p>.*?(?=<p><strong>\s*Lampiran\s*C\s*</strong></p>)',
        lampiran_b_block,
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html = re.sub(
        r'<p><strong>\s*Lampiran\s*C\s*</strong></p>.*$',
        lampiran_c_block,
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    style_block = """
<style>
        body {
            font-family: "Times New Roman", serif;
            font-size: 12pt;
            line-height: 1.6;
        }
        h1, h2, h3 {
            text-align: center;
            font-weight: bold;
        }
        .center { text-align: center; }
        .section-title {
            text-align: center;
            font-weight: bold;
            margin-top: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        table, th, td {
            border: 1px solid #000;
        }
        th, td {
            padding: 6px;
            vertical-align: top;
        }
        .signature {
            border-collapse: collapse;
            width: 100%;
            border: 1px solid #000;
        }
        .signature td {
            text-align: center;
            padding: 10px;
            vertical-align: top;
            border-top: none;
            border-bottom: none;
        }
        .signature td:first-child {
            border-right: none;
        }
        .signature td:last-child {
            border-left: none;
        }
        .signature-stamp {
            height: 50px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 9pt;
            color: #999;
        }
        .signature-label {
            font-weight: bold;
            font-size: 11pt;
            margin-bottom: 5px;
        }
        .signature-company {
            padding: 8px 12px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        .signature-space {
            height: 120px;
            margin-bottom: 15px;
        }
        .signature-name {
            font-weight: bold;
            margin-bottom: 2px;
            font-size: 13pt;
        }
        .signature-title {
            font-style: italic;
            font-size: 11pt;
            color: #333;
        }
        .page-break {
            page-break-before: always;
        }
        ol, ul {
            margin-top: 0;
            margin-bottom: 0;
        }
        p {
            margin: 0 0 8px 0;
            text-align: justify;
        }
        /* Force top heading block to match GT centered composition */
        body > p:nth-of-type(1),
        body > p:nth-of-type(2),
        body > p:nth-of-type(3),
        body > p:nth-of-type(4),
        body > p:nth-of-type(5),
        body > p:nth-of-type(6) {
            text-align: center;
            font-weight: bold;
        }
</style>
"""

    return f"<!DOCTYPE html><html lang=\"id\"><head><meta charset=\"UTF-8\">{style_block}</head><body>{html}</body></html>"


class Command(BaseCommand):
    help = 'Upload General Trade Agreement template from HTML file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contract-type',
            default=ContractType.GENERAL_TRADE,
            choices=[ContractType.GENERAL_TRADE, ContractType.DISTRIBUTOR],
            help='Contract type to upload template for'
        )

    def handle(self, *args, **options):
        try:
            selected_type = options['contract_type']

            defaults_map = {
                ContractType.GENERAL_TRADE: {
                    'name': 'General Trade Agreement',
                    'description': 'General Trade Agreement Template',
                    'number_prefix': '',
                    'number_company_code': '',
                    'number_department_code': '',
                },
                ContractType.DISTRIBUTOR: {
                    'name': 'Distributor Agreement',
                    'description': 'Distributor agreement template',
                    'number_prefix': '03',
                    'number_company_code': 'PCI',
                    'number_department_code': 'SALES',
                },
            }

            contract_type, created = ContractTypeDefinition.objects.get_or_create(
                code=selected_type,
                defaults={
                    'name': defaults_map[selected_type]['name'],
                    'description': defaults_map[selected_type]['description'],
                    'is_template_based': True,
                    'active': True,
                    'number_prefix': defaults_map[selected_type]['number_prefix'],
                    'number_company_code': defaults_map[selected_type]['number_company_code'],
                    'number_department_code': defaults_map[selected_type]['number_department_code'],
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
                desired_prefix = defaults_map[selected_type]['number_prefix']
                desired_company_code = defaults_map[selected_type]['number_company_code']
                desired_department_code = defaults_map[selected_type]['number_department_code']
                if desired_prefix and contract_type.number_prefix != desired_prefix:
                    updates['number_prefix'] = desired_prefix
                if desired_company_code and contract_type.number_company_code != desired_company_code:
                    updates['number_company_code'] = desired_company_code
                if desired_department_code and contract_type.number_department_code != desired_department_code:
                    updates['number_department_code'] = desired_department_code
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
            
            if selected_type == ContractType.GENERAL_TRADE:
                template_path = Path(__file__).parent.parent.parent.parent / 'contract agreement' / 'Template Agreement GT_ Supporting Legal System.htm'
                if not template_path.exists():
                    self.stdout.write(
                        self.style.ERROR(f'Template file not found: {template_path}')
                    )
                    return

                with open(template_path, 'r', encoding='windows-1252') as f:
                    template_content = f.read()
                template_name = 'General Trade Agreement - Supporting Legal System'
            else:
                distributor_docx_path = Path(__file__).parent.parent.parent.parent / 'contract agreement' / 'Distributor template.docx'
                if distributor_docx_path.exists():
                    with distributor_docx_path.open('rb') as docx_file:
                        result = mammoth.convert_to_html(docx_file)
                    template_content = _normalize_distributor_html(result.value or '')
                    if not template_content.strip():
                        self.stdout.write(self.style.ERROR('Converted Distributor template is empty'))
                        return
                    if result.messages:
                        self.stdout.write('  Conversion warnings:')
                        for message in result.messages:
                            self.stdout.write(f'   - {message}')
                else:
                    template_content = DISTRIBUTOR_TEMPLATE_CONTENT
                template_name = 'Distributor Agreement - Supporting Legal System'
            
            # Create or update the template
            template, created = ContractTemplate.objects.update_or_create(
                contract_type=contract_type,
                name=template_name,
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
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error uploading template: {str(e)}')
            )
