from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from contracts.models import (
    Contract, ContractTypeDefinition, ContractField, ContractTemplate,
    ContractData, ContractDataFile, ContractDraft, ContractParticipant,
    ContractSignature, ContractDocument, AuditLog, Comment
)
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = 'Populate all admin models with comprehensive reference data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting admin data setup...'))
        
        # Get or create admin user
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@lcms.local', 'is_staff': True, 'is_superuser': True}
        )
        
        # Create test users
        legal_user, _ = User.objects.get_or_create(
            username='legal_reviewer',
            defaults={'email': 'legal@lcms.local', 'is_staff': True}
        )
        
        sales_user, _ = User.objects.get_or_create(
            username='sales_rep',
            defaults={'email': 'sales@lcms.local', 'is_staff': False}
        )
        
        self.stdout.write('✓ Users created')
        
        # Setup Contract Type Definitions with Fields
        self._setup_contract_types(admin_user)
        self.stdout.write('✓ Contract types and fields configured')
        
        # Setup Contract Templates
        self._setup_templates()
        self.stdout.write('✓ Templates created')
        
        # Setup Sample Contracts with all related data
        self._setup_sample_contracts(admin_user, legal_user, sales_user)
        self.stdout.write('✓ Sample contracts created')
        
        self.stdout.write(self.style.SUCCESS('\n=== Setup Complete! ===\n'))
        self.stdout.write('Admin data is ready to use. Visit http://localhost/admin/')

    def _setup_contract_types(self, user):
        """Setup all contract types with dynamic fields"""
        
        # Clear existing fields
        ContractField.objects.all().delete()
        
        # NDA Configuration
        nda_type = ContractTypeDefinition.objects.get(code='NDA')
        nda_fields = [
            {'field_key': 'disclosing_party', 'label': 'Disclosing Party Name', 'field_type': 'text', 'position': 1, 'required': True},
            {'field_key': 'receiving_party', 'label': 'Receiving Party Name', 'field_type': 'text', 'position': 2, 'required': True},
            {'field_key': 'confidentiality_period', 'label': 'Confidentiality Period (months)', 'field_type': 'number', 'position': 3, 'required': True},
            {'field_key': 'effective_date', 'label': 'Effective Date', 'field_type': 'date', 'position': 4, 'required': True},
            {'field_key': 'nda_type', 'label': 'NDA Type', 'field_type': 'select', 'position': 5, 'required': True, 'options': ['Unilateral', 'Bilateral', 'Multilateral']},
        ]
        for field_data in nda_fields:
            ContractField.objects.create(contract_type=nda_type, **field_data)
        
        # Vendor Agreement Configuration
        vendor_type = ContractTypeDefinition.objects.get(code='VENDOR')
        vendor_fields = [
            {'field_key': 'vendor_name', 'label': 'Vendor Company Name', 'field_type': 'text', 'position': 1, 'required': True},
            {'field_key': 'vendor_contact', 'label': 'Primary Contact', 'field_type': 'text', 'position': 2, 'required': True},
            {'field_key': 'service_description', 'label': 'Services/Products Description', 'field_type': 'text', 'position': 3, 'required': True},
            {'field_key': 'contract_value', 'label': 'Total Contract Value (IDR)', 'field_type': 'number', 'position': 4, 'required': True},
            {'field_key': 'payment_terms', 'label': 'Payment Terms', 'field_type': 'select', 'position': 5, 'required': True, 'options': ['Net 30', 'Net 60', 'Net 90', 'Upon Delivery']},
            {'field_key': 'start_date', 'label': 'Service Start Date', 'field_type': 'date', 'position': 6, 'required': True},
            {'field_key': 'end_date', 'label': 'Service End Date', 'field_type': 'date', 'position': 7, 'required': True},
            {'field_key': 'insurance_required', 'label': 'Insurance Required', 'field_type': 'select', 'position': 8, 'required': False, 'options': ['Yes', 'No']},
            {'field_key': 'sow_document', 'label': 'Statement of Work (Upload)', 'field_type': 'file', 'position': 9, 'required': False},
        ]
        for field_data in vendor_fields:
            ContractField.objects.create(contract_type=vendor_type, **field_data)
        
        # Employment Contract Configuration
        emp_type = ContractTypeDefinition.objects.get(code='EMPLOYMENT')
        emp_fields = [
            {'field_key': 'employee_name', 'label': 'Employee Full Name', 'field_type': 'text', 'position': 1, 'required': True},
            {'field_key': 'position_title', 'label': 'Position Title', 'field_type': 'text', 'position': 2, 'required': True},
            {'field_key': 'annual_salary', 'label': 'Annual Salary (IDR)', 'field_type': 'number', 'position': 3, 'required': True},
            {'field_key': 'start_date', 'label': 'Employment Start Date', 'field_type': 'date', 'position': 4, 'required': True},
            {'field_key': 'employment_type', 'label': 'Employment Type', 'field_type': 'select', 'position': 5, 'required': True, 'options': ['Full-time', 'Part-time', 'Contract', 'Temporary']},
            {'field_key': 'reporting_to', 'label': 'Reports To', 'field_type': 'text', 'position': 6, 'required': True},
        ]
        for field_data in emp_fields:
            ContractField.objects.create(contract_type=emp_type, **field_data)
        
        # Service Agreement Configuration
        service_type = ContractTypeDefinition.objects.get(code='SERVICE')
        service_fields = [
            {'field_key': 'service_provider', 'label': 'Service Provider Name', 'field_type': 'text', 'position': 1, 'required': True},
            {'field_key': 'service_recipient', 'label': 'Service Recipient Name', 'field_type': 'text', 'position': 2, 'required': True},
            {'field_key': 'service_scope', 'label': 'Scope of Services', 'field_type': 'text', 'position': 3, 'required': True},
            {'field_key': 'service_fee', 'label': 'Service Fee (IDR)', 'field_type': 'number', 'position': 4, 'required': True},
            {'field_key': 'term_length', 'label': 'Contract Term (months)', 'field_type': 'number', 'position': 5, 'required': True},
            {'field_key': 'service_sla', 'label': 'Service Level Agreement', 'field_type': 'select', 'position': 6, 'required': False, 'options': ['99.5% Uptime', '99.9% Uptime', '99.99% Uptime', 'Best Effort']},
        ]
        for field_data in service_fields:
            ContractField.objects.create(contract_type=service_type, **field_data)

    def _setup_templates(self):
        """Create templates for each contract type"""
        
        templates_config = [
            {
                'code': 'NDA',
                'name': 'Standard NDA Template',
                'content': '''<html><head><style>body{font-family:Arial;margin:40px;}</style></head><body>
<h1>NON-DISCLOSURE AGREEMENT</h1>
<p>This Agreement is entered into as of {{ effective_date }} by and between:</p>
<p><b>Disclosing Party:</b> {{ disclosing_party }}</p>
<p><b>Receiving Party:</b> {{ receiving_party }}</p>
<p><b>Type:</b> {{ nda_type }}</p>
<p><b>Confidentiality Period:</b> {{ confidentiality_period }} months from the effective date.</p>
<p>The Receiving Party agrees to maintain the confidentiality of all proprietary information disclosed by the Disclosing Party.</p>
</body></html>'''
            },
            {
                'code': 'VENDOR',
                'name': 'Standard Vendor Agreement Template',
                'content': '''<html><head><style>body{font-family:Arial;margin:40px;}</style></head><body>
<h1>VENDOR SERVICE AGREEMENT</h1>
<p><b>Vendor:</b> {{ vendor_name }}</p>
<p><b>Contact:</b> {{ vendor_contact }}</p>
<p><b>Services:</b> {{ service_description }}</p>
<p><b>Contract Value:</b> Rp {{ contract_value }}</p>
<p><b>Payment Terms:</b> {{ payment_terms }}</p>
<p><b>Service Period:</b> {{ start_date }} to {{ end_date }}</p>
<p><b>Insurance Required:</b> {{ insurance_required }}</p>
<p>This agreement outlines the terms and conditions for the provision of services.</p>
</body></html>'''
            },
            {
                'code': 'EMPLOYMENT',
                'name': 'Employment Contract Template',
                'content': '''<html><head><style>body{font-family:Arial;margin:40px;}</style></head><body>
<h1>EMPLOYMENT AGREEMENT</h1>
<p><b>Employee:</b> {{ employee_name }}</p>
<p><b>Position:</b> {{ position_title }}</p>
<p><b>Employment Type:</b> {{ employment_type }}</p>
<p><b>Annual Salary:</b> Rp {{ annual_salary }}</p>
<p><b>Start Date:</b> {{ start_date }}</p>
<p><b>Reports To:</b> {{ reporting_to }}</p>
<p>Employment is on an at-will basis, subject to company policies.</p>
</body></html>'''
            },
            {
                'code': 'SERVICE',
                'name': 'Service Agreement Template',
                'content': '''<html><head><style>body{font-family:Arial;margin:40px;}</style></head><body>
<h1>SERVICE AGREEMENT</h1>
<p><b>Service Provider:</b> {{ service_provider }}</p>
<p><b>Service Recipient:</b> {{ service_recipient }}</p>
<p><b>Scope:</b> {{ service_scope }}</p>
<p><b>Service Fee:</b> Rp {{ service_fee }}</p>
<p><b>Term:</b> {{ term_length }} months</p>
<p><b>SLA:</b> {{ service_sla }}</p>
</body></html>'''
            }
        ]
        
        for config in templates_config:
            type_def = ContractTypeDefinition.objects.get(code=config['code'])
            ContractTemplate.objects.filter(contract_type=type_def).delete()
            ContractTemplate.objects.create(
                contract_type=type_def,
                name=config['name'],
                content=config['content'],
                active=True,
                version=1
            )

    def _setup_sample_contracts(self, admin_user, legal_user, sales_user):
        """Create sample contracts with full workflow data"""
        
        # Clear existing sample data to avoid duplicates
        Contract.objects.filter(title__in=[
            'Acme Software Services Agreement',
            'Sarah Johnson - Senior Developer Position',
            'TechCorp NDA - Q1 2026 Partnership Discussion'
        ]).delete()
        
        # Vendor Agreement Sample
        vendor_contract = Contract.objects.create(
            title='Acme Software Services Agreement',
            contract_type='VENDOR',
            status='ACTIVE',
            owner=sales_user,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=365)).date(),
            party_a='Our Company Inc',
            party_b='Acme Software Inc',
            contract_value=50000.00,
            description='Cloud hosting and technical support services for internal infrastructure'
        )
        
        # Add structured data
        vendor_data = ContractData.objects.create(
            contract=vendor_contract,
            version=1,
            submitted_by=sales_user,
            data={
                'vendor_name': 'Acme Software Inc',
                'vendor_contact': 'John Smith, john@acmesoftware.com',
                'service_description': 'Cloud Hosting, 24/7 Support, Infrastructure Management',
                'contract_value': 50000,
                'payment_terms': 'Net 60',
                'start_date': '2026-01-01',
                'end_date': '2027-01-01',
                'insurance_required': 'Yes'
            }
        )
        
        # Generate draft
        vendor_template = ContractTemplate.objects.filter(contract_type__code='VENDOR').first()
        draft_content = '<h1>Vendor Service Agreement</h1><p>Acme Software Inc - $50,000/year</p>'
        ContractDraft.objects.create(
            contract=vendor_contract,
            template=vendor_template,
            version=1,
            file=ContentFile(draft_content.encode(), name='draft_vendor_v1.html')
        )
        
        # Add document
        ContractDocument.objects.create(
            contract=vendor_contract,
            title='Signed Agreement - Acme',
            document=ContentFile(b'Sample PDF content', name='acme_signed.pdf'),
            uploaded_by=legal_user,
            description='Final signed agreement from Acme Software'
        )
        
        # Add participants
        ContractParticipant.objects.filter(contract=vendor_contract).delete()
        ContractParticipant.objects.create(
            contract=vendor_contract,
            user=sales_user,
            role='OWNER'
        )
        ContractParticipant.objects.create(
            contract=vendor_contract,
            user=legal_user,
            role='LEGAL'
        )
        
        # Add signature
        ContractSignature.objects.filter(contract=vendor_contract).delete()
        ContractSignature.objects.create(
            contract=vendor_contract,
            user=legal_user
        )
        
        # Add audit log
        AuditLog.objects.create(
            contract=vendor_contract,
            user=sales_user,
            action='CREATED',
            details='Contract created for Acme Software Services'
        )
        AuditLog.objects.create(
            contract=vendor_contract,
            user=admin_user,
            action='DATA_SUBMITTED',
            details='Structured data submitted and draft generated'
        )
        
        # Add comments
        Comment.objects.create(
            contract=vendor_contract,
            user=legal_user,
            text='Terms look good. Approved for signature.',
            is_internal=True
        )
        
        # Employment Contract Sample
        emp_contract = Contract.objects.create(
            title='Sarah Johnson - Senior Developer Position',
            contract_type='EMPLOYMENT',
            status='ACTIVE',
            owner=admin_user,
            start_date=(timezone.now() + timedelta(days=30)).date(),
            end_date=None,
            party_a='Our Company Inc',
            party_b='Sarah Johnson',
            contract_value=120000.00,
            description='Full-time Senior Developer position'
        )
        
        emp_data = ContractData.objects.create(
            contract=emp_contract,
            version=1,
            submitted_by=admin_user,
            data={
                'employee_name': 'Sarah Johnson',
                'position_title': 'Senior Developer',
                'annual_salary': 120000,
                'start_date': '2026-02-15',
                'employment_type': 'Full-time',
                'reporting_to': 'Engineering Manager'
            }
        )
        
        emp_template = ContractTemplate.objects.filter(contract_type__code='EMPLOYMENT').first()
        ContractDraft.objects.create(
            contract=emp_contract,
            template=emp_template,
            version=1,
            file=ContentFile(b'<h1>Employment Agreement - Sarah Johnson</h1>', name='draft_emp_v1.html')
        )
        
        ContractParticipant.objects.filter(contract=emp_contract).delete()
        ContractParticipant.objects.create(
            contract=emp_contract,
            user=admin_user,
            role='OWNER'
        )
        
        AuditLog.objects.create(
            contract=emp_contract,
            user=admin_user,
            action='CREATED',
            details='Employment contract created'
        )
        
        # NDA Sample
        nda_contract = Contract.objects.create(
            title='TechCorp NDA - Q1 2026 Partnership Discussion',
            contract_type='NDA',
            status='PENDING_SIGNATURE',
            owner=admin_user,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=180)).date(),
            party_a='Our Company Inc',
            party_b='TechCorp International',
            description='Confidentiality agreement for partnership discussions'
        )
        
        ContractParticipant.objects.filter(contract=nda_contract).delete()
        ContractParticipant.objects.create(
            contract=nda_contract,
            user=admin_user,
            role='OWNER'
        )
        ContractParticipant.objects.create(
            contract=nda_contract,
            user=legal_user,
            role='LEGAL'
        )
        
        AuditLog.objects.create(
            contract=nda_contract,
            user=admin_user,
            action='CREATED',
            details='NDA created for partnership discussion'
        )
        
        Comment.objects.create(
            contract=nda_contract,
            user=legal_user,
            text='Waiting for counterparty signature. Standard bilateral NDA terms.',
            is_internal=True
        )
