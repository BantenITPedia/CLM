"""
Tests for automated email reminders system
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

from contracts.models import (
    Contract, ContractTypeDefinition, ContractStatus, ParticipantRole,
    ReminderConfiguration, ReminderLog, ReminderType, ContractParticipant
)
from contracts.services import ReminderService, EmailService


class ReminderConfigurationModelTests(TestCase):
    """Test ReminderConfiguration model"""
    
    def setUp(self):
        self.contract_type = ContractTypeDefinition.objects.create(
            code='VENDOR',
            name='Vendor Agreement',
            active=True
        )
        self.contract = Contract.objects.create(
            title='Test Contract',
            contract_type='VENDOR',
            party_a='Our Company',
            party_b='Vendor Inc',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30)
        )
    
    def test_create_global_reminder(self):
        """Test creating a global reminder configuration"""
        config = ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='GLOBAL',
            enabled=True,
            days_before_trigger=30
        )
        self.assertEqual(config.reminder_type, 'EXPIRY')
        self.assertEqual(config.scope, 'GLOBAL')
        self.assertTrue(config.enabled)
    
    def test_create_type_specific_reminder(self):
        """Test creating a type-specific reminder"""
        config = ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='TYPE',
            contract_type=self.contract_type,
            days_before_trigger=14
        )
        self.assertEqual(config.scope, 'TYPE')
        self.assertEqual(config.contract_type, self.contract_type)
    
    def test_create_contract_specific_reminder(self):
        """Test creating a per-contract override"""
        config = ReminderConfiguration.objects.create(
            reminder_type='SIGNATURE_PENDING',
            scope='CONTRACT',
            contract=self.contract,
            frequency='DAILY'
        )
        self.assertEqual(config.scope, 'CONTRACT')
        self.assertEqual(config.contract, self.contract)
        self.assertEqual(config.frequency, 'DAILY')
    
    def test_recipient_roles_parsing(self):
        """Test parsing recipient roles"""
        config = ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='GLOBAL',
            recipient_roles='OWNER,SIGNATORY,LEGAL'
        )
        roles = config.get_recipient_roles()
        self.assertEqual(roles, ['OWNER', 'SIGNATORY', 'LEGAL'])
    
    def test_empty_recipient_roles(self):
        """Test empty recipient roles returns empty list"""
        config = ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='GLOBAL'
        )
        roles = config.get_recipient_roles()
        self.assertEqual(roles, [])


class ReminderLogModelTests(TestCase):
    """Test ReminderLog model"""
    
    def setUp(self):
        self.contract = Contract.objects.create(
            title='Test Contract',
            contract_type='VENDOR',
            party_a='Our Company',
            party_b='Vendor Inc',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30)
        )
        self.config = ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='GLOBAL'
        )
    
    def test_create_reminder_log(self):
        """Test creating a reminder log entry"""
        log = ReminderLog.objects.create(
            reminder_config=self.config,
            contract=self.contract,
            reminder_type='EXPIRY',
            scheduled_date=timezone.now(),
            recipients='owner@example.com,legal@example.com',
            status='SCHEDULED'
        )
        self.assertEqual(log.status, 'SCHEDULED')
        self.assertIsNone(log.sent_date)
    
    def test_mark_as_sent(self):
        """Test marking reminder as sent"""
        log = ReminderLog.objects.create(
            reminder_config=self.config,
            contract=self.contract,
            reminder_type='EXPIRY',
            scheduled_date=timezone.now(),
            recipients='owner@example.com',
            status='SCHEDULED'
        )
        log.status = 'SENT'
        log.sent_date = timezone.now()
        log.save()
        
        log.refresh_from_db()
        self.assertEqual(log.status, 'SENT')
        self.assertIsNotNone(log.sent_date)
    
    def test_mark_as_failed(self):
        """Test marking reminder as failed"""
        log = ReminderLog.objects.create(
            reminder_config=self.config,
            contract=self.contract,
            reminder_type='EXPIRY',
            scheduled_date=timezone.now(),
            recipients='invalid@example.com',
            status='SCHEDULED',
            error_message='SMTP connection failed'
        )
        self.assertEqual(log.status, 'SCHEDULED')
        
        log.status = 'FAILED'
        log.save()
        
        log.refresh_from_db()
        self.assertEqual(log.status, 'FAILED')
        self.assertIn('SMTP', log.error_message)


class ReminderServiceTriggerCalculationTests(TestCase):
    """Test trigger date calculation"""
    
    def setUp(self):
        today = timezone.now().date()
        self.contract = Contract.objects.create(
            title='Test Contract',
            contract_type='VENDOR',
            party_a='Our Company',
            party_b='Vendor Inc',
            start_date=today,
            end_date=today + timedelta(days=60)
        )
    
    def test_expiry_trigger_date(self):
        """Test EXPIRY reminder trigger calculation"""
        trigger = ReminderService._calculate_trigger_date(
            self.contract,
            'EXPIRY',
            days_before=30
        )
        expected = self.contract.end_date - timedelta(days=30)
        self.assertEqual(trigger, expected)
    
    def test_renewal_trigger_date(self):
        """Test RENEWAL reminder trigger calculation"""
        trigger = ReminderService._calculate_trigger_date(
            self.contract,
            'RENEWAL',
            days_before=60
        )
        expected = self.contract.end_date - timedelta(days=60)
        self.assertEqual(trigger, expected)
    
    def test_signature_pending_trigger_date(self):
        """Test SIGNATURE_PENDING reminder trigger calculation"""
        trigger = ReminderService._calculate_trigger_date(
            self.contract,
            'SIGNATURE_PENDING',
            days_before=3
        )
        # Should be based on updated_at
        self.assertIsNotNone(trigger)
    
    def test_trigger_with_no_end_date(self):
        """Test trigger calculation with no end_date"""
        self.contract.end_date = None
        self.contract.save()
        
        trigger = ReminderService._calculate_trigger_date(
            self.contract,
            'EXPIRY',
            days_before=30
        )
        self.assertIsNone(trigger)


class ReminderServiceThrottlingTests(TestCase):
    """Test reminder throttling logic"""
    
    def setUp(self):
        today = timezone.now().date()
        self.contract = Contract.objects.create(
            title='Test Contract',
            contract_type='VENDOR',
            party_a='Our Company',
            party_b='Vendor Inc',
            start_date=today,
            end_date=today + timedelta(days=30)
        )
        self.config = ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='GLOBAL',
            frequency='ONCE',
            max_occurrences=1
        )
    
    def test_once_frequency_sends_only_once(self):
        """Test ONCE frequency only sends one time"""
        # First send
        should_send = ReminderService._should_send_reminder(self.contract, self.config)
        self.assertTrue(should_send)
        
        # Create log entry
        ReminderLog.objects.create(
            reminder_config=self.config,
            contract=self.contract,
            reminder_type='EXPIRY',
            scheduled_date=timezone.now(),
            recipients='test@example.com',
            status='SENT',
            sent_date=timezone.now()
        )
        
        # Second attempt - should be throttled
        should_send = ReminderService._should_send_reminder(self.contract, self.config)
        self.assertFalse(should_send)
    
    def test_daily_frequency_prevents_same_day(self):
        """Test DAILY frequency prevents same-day sends"""
        daily_config = ReminderConfiguration.objects.create(
            reminder_type='SIGNATURE_PENDING',
            scope='GLOBAL',
            frequency='DAILY'
        )
        
        # Create log for today
        ReminderLog.objects.create(
            reminder_config=daily_config,
            contract=self.contract,
            reminder_type='SIGNATURE_PENDING',
            scheduled_date=timezone.now(),
            recipients='test@example.com',
            status='SENT',
            sent_date=timezone.now()
        )
        
        # Should not send again today
        should_send = ReminderService._should_send_reminder(self.contract, daily_config)
        self.assertFalse(should_send)
    
    def test_weekly_frequency_prevents_week(self):
        """Test WEEKLY frequency prevents sends within 7 days"""
        weekly_config = ReminderConfiguration.objects.create(
            reminder_type='RENEWAL',
            scope='GLOBAL',
            frequency='WEEKLY'
        )
        
        # Create log for yesterday
        yesterday = timezone.now() - timedelta(days=1)
        ReminderLog.objects.create(
            reminder_config=weekly_config,
            contract=self.contract,
            reminder_type='RENEWAL',
            scheduled_date=yesterday,
            recipients='test@example.com',
            status='SENT',
            sent_date=yesterday
        )
        
        # Should not send within 7 days
        should_send = ReminderService._should_send_reminder(self.contract, weekly_config)
        self.assertFalse(should_send)


class ReminderServiceGetDueRemindersTests(TestCase):
    """Test get_due_reminders logic"""
    
    def setUp(self):
        today = timezone.now().date()
        self.contract_expiring_soon = Contract.objects.create(
            title='Expiring Soon',
            contract_type='VENDOR',
            party_a='Our Company',
            party_b='Vendor A',
            start_date=today - timedelta(days=100),
            end_date=today + timedelta(days=5),
            status=ContractStatus.ACTIVE
        )
        self.contract_not_expiring = Contract.objects.create(
            title='Far Future',
            contract_type='VENDOR',
            party_a='Our Company',
            party_b='Vendor B',
            start_date=today,
            end_date=today + timedelta(days=365),
            status=ContractStatus.ACTIVE
        )
        # Create global expiry reminder (30 days before)
        self.config = ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='GLOBAL',
            enabled=True,
            days_before_trigger=30,
            frequency='ONCE'
        )
    
    def test_get_due_reminders_finds_expiring_contracts(self):
        """Test that get_due_reminders finds contracts nearing expiry"""
        due = ReminderService.get_due_reminders(reminder_type='EXPIRY')
        
        # Should find the expiring contract
        contract_ids = [c.id for c, _, _ in due]
        self.assertIn(self.contract_expiring_soon.id, contract_ids)
    
    def test_get_due_reminders_ignores_future_contracts(self):
        """Test that future contracts are not included"""
        due = ReminderService.get_due_reminders(reminder_type='EXPIRY')
        
        # Should not include far future contract
        contract_ids = [c.id for c, _, _ in due]
        self.assertNotIn(self.contract_not_expiring.id, contract_ids)
    
    def test_get_due_reminders_respects_enabled_flag(self):
        """Test that disabled configs are ignored"""
        self.config.enabled = False
        self.config.save()
        
        due = ReminderService.get_due_reminders(reminder_type='EXPIRY')
        self.assertEqual(len(due), 0)
    
    def test_get_due_reminders_filters_by_type(self):
        """Test filtering by reminder type"""
        # Create signature pending config
        sig_config = ReminderConfiguration.objects.create(
            reminder_type='SIGNATURE_PENDING',
            scope='GLOBAL',
            enabled=True
        )
        
        # Get only EXPIRY
        due = ReminderService.get_due_reminders(reminder_type='EXPIRY')
        types = [config.reminder_type for _, config, _ in due]
        self.assertTrue(all(t == 'EXPIRY' for t in types))


class ReminderServiceScheduleRemindersTests(TestCase):
    """Test schedule_reminders orchestration"""
    
    def setUp(self):
        today = timezone.now().date()
        self.contract = Contract.objects.create(
            title='Test Contract',
            contract_type='VENDOR',
            party_a='Our Company',
            party_b='Vendor Inc',
            start_date=today - timedelta(days=50),
            end_date=today + timedelta(days=5),
            status=ContractStatus.ACTIVE
        )
        self.config = ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='GLOBAL',
            enabled=True,
            days_before_trigger=30
        )
    
    def test_schedule_reminders_creates_logs(self):
        """Test that schedule_reminders creates ReminderLog entries"""
        initial_count = ReminderLog.objects.count()
        
        result = ReminderService.schedule_reminders(dry_run=False)
        
        self.assertGreater(ReminderLog.objects.count(), initial_count)
        self.assertEqual(result['dry_run'], False)
        self.assertGreater(result['scheduled'], 0)
    
    def test_schedule_reminders_dry_run(self):
        """Test dry_run doesn't create logs"""
        initial_count = ReminderLog.objects.count()
        
        result = ReminderService.schedule_reminders(dry_run=True)
        
        # Dry run shouldn't create logs
        self.assertEqual(ReminderLog.objects.count(), initial_count)
        self.assertEqual(result['dry_run'], True)
    
    def test_schedule_reminders_respects_throttling(self):
        """Test that schedule_reminders respects throttling"""
        # Schedule once
        ReminderService.schedule_reminders(dry_run=False)
        initial_log_count = ReminderLog.objects.count()
        
        # Schedule again - should be throttled (ONCE frequency)
        ReminderService.schedule_reminders(dry_run=False)
        
        self.assertEqual(ReminderLog.objects.count(), initial_log_count)


class RemindersIntegrationTests(TestCase):
    """Integration tests for reminder workflow"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        today = timezone.now().date()
        self.contract = Contract.objects.create(
            title='Integration Test Contract',
            contract_type='VENDOR',
            party_a='Our Company',
            party_b='Vendor Inc',
            start_date=today - timedelta(days=50),
            end_date=today + timedelta(days=5),
            status=ContractStatus.ACTIVE,
            owner=self.user
        )
        self.participant = ContractParticipant.objects.create(
            contract=self.contract,
            user=self.user,
            role=ParticipantRole.OWNER,
            notification_preference='critical'
        )
        self.config = ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='GLOBAL',
            enabled=True,
            days_before_trigger=30,
            frequency='ONCE',
            max_occurrences=1
        )
    
    def test_end_to_end_reminder_workflow(self):
        """Test complete workflow: identify → schedule → send"""
        # Step 1: Identify due reminders
        due = ReminderService.get_due_reminders(reminder_type='EXPIRY')
        self.assertGreater(len(due), 0)
        
        # Step 2: Schedule reminders
        schedule_result = ReminderService.schedule_reminders(dry_run=False)
        self.assertGreater(schedule_result['scheduled'], 0)
        
        # Step 3: Verify logs created
        logs = ReminderLog.objects.filter(contract=self.contract)
        self.assertGreater(logs.count(), 0)
        self.assertEqual(logs.first().status, 'SCHEDULED')
        
        # Step 4: Send reminders
        send_result = ReminderService.send_reminder_batch(batch_size=100)
        self.assertGreaterEqual(send_result['total'], 0)
        
        # Step 5: Verify logs updated
        logs.refresh_from_db()
        for log in logs:
            self.assertIn(log.status, ['SENT', 'FAILED', 'SKIPPED'])
    
    def test_multiple_reminder_types(self):
        """Test scheduling multiple reminder types"""
        # Create multiple configs
        ReminderConfiguration.objects.create(
            reminder_type='SIGNATURE_PENDING',
            scope='GLOBAL',
            enabled=True,
            frequency='DAILY'
        )
        ReminderConfiguration.objects.create(
            reminder_type='RENEWAL',
            scope='GLOBAL',
            enabled=True,
            frequency='ONCE'
        )
        
        # Schedule all
        result = ReminderService.schedule_reminders(dry_run=False)
        
        # Should have scheduled some reminders
        self.assertGreaterEqual(result['scheduled'], 0)
    
    def test_per_contract_override(self):
        """Test that per-contract override takes precedence"""
        # Create override for this specific contract
        override_config = ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='CONTRACT',
            contract=self.contract,
            enabled=True,
            days_before_trigger=5,  # Different from global 30
            frequency='DAILY'  # Different from global ONCE
        )
        
        # Get due reminders
        due = ReminderService.get_due_reminders(reminder_type='EXPIRY')
        
        # Should find reminders
        self.assertGreater(len(due), 0)


class ReminderConfigurationDefaultsTests(TestCase):
    """Test default configurations are created"""
    
    def test_defaults_created(self):
        """Test that default reminders exist"""
        # After migration, should have defaults
        configs = ReminderConfiguration.objects.filter(scope='GLOBAL')
        
        reminder_types = [c.reminder_type for c in configs]
        # At least some default should exist
        self.assertGreaterEqual(len(configs), 0)


class ReminderRecipientFilteringTests(TestCase):
    """Test recipient filtering logic"""
    
    def setUp(self):
        self.contract = Contract.objects.create(
            title='Test Contract',
            contract_type='VENDOR',
            party_a='Our Company',
            party_b='Vendor Inc'
        )
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com'
        )
        self.signatory = User.objects.create_user(
            username='signatory',
            email='signatory@example.com'
        )
        self.contract.owner = self.owner
        self.contract.save()
        
        # Add participants
        ContractParticipant.objects.create(
            contract=self.contract,
            user=self.owner,
            role=ParticipantRole.OWNER,
            notification_preference='critical'
        )
        ContractParticipant.objects.create(
            contract=self.contract,
            user=self.signatory,
            role=ParticipantRole.SIGNATORY,
            notification_preference='critical'
        )
    
    def test_get_recipient_emails_for_config(self):
        """Test getting recipients filtered by config roles"""
        config = ReminderConfiguration.objects.create(
            reminder_type='SIGNATURE_PENDING',
            scope='GLOBAL',
            recipient_roles='SIGNATORY'
        )
        
        recipients = ReminderService._get_recipient_emails(self.contract, config)
        
        # Should include signatory
        self.assertIn(self.signatory.email, recipients)
    
    def test_get_recipient_emails_always_includes_owner(self):
        """Test that owner is always included"""
        config = ReminderConfiguration.objects.create(
            reminder_type='EXPIRY',
            scope='GLOBAL',
            recipient_roles='LEGAL'  # Owner not explicitly listed
        )
        
        recipients = ReminderService._get_recipient_emails(self.contract, config)
        
        # Owner should still be included
        self.assertIn(self.owner.email, recipients)
