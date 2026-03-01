from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from contracts.models import Contract, ContractType, ContractDocument
from contracts.services import DocumentVersionService


class DocumentVersioningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', email='user@example.com')
        self.contract = Contract.objects.create(
            title='Vendor Agreement',
            contract_type=ContractType.VENDOR,
            party_a='Company A',
            party_b='Vendor B'
        )

    def test_first_upload_sets_version_1(self):
        file_obj = SimpleUploadedFile('doc_v1.pdf', b'v1 content')
        doc = DocumentVersionService.create_versioned_document(
            contract=self.contract,
            uploaded_by=self.user,
            title='Agreement',
            file_obj=file_obj,
            description='Initial version'
        )

        self.assertEqual(doc.version, 1)
        self.assertTrue(doc.is_current)

    def test_second_upload_increments_version(self):
        file_obj1 = SimpleUploadedFile('doc_v1.pdf', b'v1 content')
        DocumentVersionService.create_versioned_document(
            contract=self.contract,
            uploaded_by=self.user,
            title='Agreement',
            file_obj=file_obj1,
            description='Initial version'
        )

        file_obj2 = SimpleUploadedFile('doc_v2.pdf', b'v2 content')
        doc2 = DocumentVersionService.create_versioned_document(
            contract=self.contract,
            uploaded_by=self.user,
            title='Agreement',
            file_obj=file_obj2,
            description='Revised version'
        )

        self.assertEqual(doc2.version, 2)
        self.assertTrue(doc2.is_current)

        previous_docs = ContractDocument.objects.filter(contract=self.contract, version=1)
        self.assertTrue(previous_docs.exists())
        self.assertFalse(previous_docs.first().is_current)

    def test_versions_increment_per_contract(self):
        file_obj1 = SimpleUploadedFile('doc_v1.pdf', b'v1 content')
        DocumentVersionService.create_versioned_document(
            contract=self.contract,
            uploaded_by=self.user,
            title='Agreement',
            file_obj=file_obj1
        )

        file_obj2 = SimpleUploadedFile('doc_v2.pdf', b'v2 content')
        doc2 = DocumentVersionService.create_versioned_document(
            contract=self.contract,
            uploaded_by=self.user,
            title='Agreement',
            file_obj=file_obj2
        )

        self.assertEqual(doc2.version, 2)

    def test_non_template_document_still_allowed(self):
        file_obj = SimpleUploadedFile('doc.pdf', b'content')
        doc = DocumentVersionService.create_versioned_document(
            contract=self.contract,
            uploaded_by=self.user,
            title='Agreement',
            file_obj=file_obj
        )

        self.assertIsNotNone(doc.id)
