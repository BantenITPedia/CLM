from datetime import date
from decimal import Decimal

from django.test import TestCase

from contracts.models import Contract, ContractType
from contracts.services import ContractTargetService, TemplateService


class ContractTargetServiceTests(TestCase):
    def setUp(self):
        self.contract = Contract.objects.create(
            title='Sales Agreement',
            contract_type=ContractType.GENERAL_TRADE,
            party_a='Company A',
            party_b='Company B',
            start_date=date(2026, 2, 1),
            end_date=date(2027, 1, 31)
        )

    def test_calculate_quarters_from_start_date(self):
        quarters = ContractTargetService.calculate_quarters(
            self.contract.start_date,
            self.contract.end_date
        )

        self.assertEqual(len(quarters), 4)
        self.assertEqual(quarters[0][1], date(2026, 2, 1))
        self.assertEqual(quarters[0][2], date(2026, 4, 30))
        self.assertEqual(quarters[1][1], date(2026, 5, 1))
        self.assertEqual(quarters[1][2], date(2026, 7, 31))
        self.assertEqual(quarters[2][1], date(2026, 8, 1))
        self.assertEqual(quarters[2][2], date(2026, 10, 31))
        self.assertEqual(quarters[3][1], date(2026, 11, 1))
        self.assertEqual(quarters[3][2], date(2027, 1, 31))

    def test_upsert_targets_creates_quarters(self):
        ContractTargetService.upsert_targets(self.contract, '1000')

        quarters = list(self.contract.quarters.order_by('quarter_number'))
        self.assertEqual(len(quarters), 4)
        self.assertEqual(quarters[0].target_amount, Decimal('250.00'))
        self.assertEqual(quarters[1].target_amount, Decimal('250.00'))
        self.assertEqual(quarters[2].target_amount, Decimal('250.00'))
        self.assertEqual(quarters[3].target_amount, Decimal('250.00'))

    def test_upsert_targets_ignored_for_non_sales(self):
        non_sales = Contract.objects.create(
            title='Non Sales',
            contract_type=ContractType.VENDOR,
            party_a='Company A',
            party_b='Company C',
            start_date=date(2026, 2, 1),
            end_date=date(2027, 1, 31)
        )

        result = ContractTargetService.upsert_targets(non_sales, '1000')
        self.assertIsNone(result)
        self.assertEqual(non_sales.quarters.count(), 0)


class TemplateContextQuarterTests(TestCase):
    def setUp(self):
        self.contract = Contract.objects.create(
            title='Sales Agreement',
            contract_type=ContractType.MODERN_TRADE,
            party_a='Company A',
            party_b='Company B',
            start_date=date(2026, 2, 1),
            end_date=date(2027, 1, 31)
        )
        ContractTargetService.upsert_targets(self.contract, '2000')

    def test_template_context_includes_quarters(self):
        context = TemplateService.build_template_context(self.contract, {})

        self.assertIn('annual_target', context)
        self.assertIn('quarters', context)
        self.assertEqual(len(context['quarters']), 4)
        self.assertIn('q1_target', context)
        self.assertIn('q4_end', context)
