from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class ContractType(models.TextChoices):
    GENERAL_TRADE = 'GENERAL_TRADE', 'General Trade Agreement'
    MODERN_TRADE = 'MODERN_TRADE', 'Modern Trade Agreement'
    DISTRIBUTOR = 'DISTRIBUTOR', 'Distributor Agreement'
    NDA = 'NDA', 'Non-Disclosure Agreement'
    VENDOR = 'VENDOR', 'Vendor Agreement'
    SERVICE = 'SERVICE', 'Service Agreement'
    EMPLOYMENT = 'EMPLOYMENT', 'Employment Contract'
    LEASE = 'LEASE', 'Lease Agreement'
    PURCHASE = 'PURCHASE', 'Purchase Agreement'
    OTHER = 'OTHER', 'Other'


class ContractStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    SUBMITTED = 'SUBMITTED', 'Submitted for Review'
    LEGAL_REVIEW = 'LEGAL_REVIEW', 'Legal Review'
    APPROVED = 'APPROVED', 'Approved'
    ACTIVE = 'ACTIVE', 'Active'
    EXPIRING_SOON = 'EXPIRING_SOON', 'Expiring Soon'
    TERMINATED = 'TERMINATED', 'Terminated'


class ParticipantRole(models.TextChoices):
    OWNER = 'OWNER', 'Contract Owner'
    SALES = 'SALES', 'Sales Representative'
    LEGAL = 'LEGAL', 'Legal Reviewer'
    CUSTOMER = 'CUSTOMER', 'Customer'
    SIGNATORY = 'SIGNATORY', 'Signatory'
    APPROVER = 'APPROVER', 'Approver'


class ContractPermission(models.TextChoices):
    VIEW_CONTRACT = 'view_contract', 'View contract'
    EDIT_CONTRACT = 'edit_contract', 'Edit contract'
    DELETE_CONTRACT = 'delete_contract', 'Delete contract'
    UPDATE_STATUS = 'update_status', 'Update status'
    MANAGE_PARTICIPANTS = 'manage_participants', 'Manage participants'
    ADD_DOCUMENT = 'add_document', 'Add documents'
    UPLOAD_FINAL_DOCUMENT = 'upload_final_document', 'Upload final approved document'
    ADD_COMMENT = 'add_comment', 'Add comments'
    EDIT_STRUCTURED_DATA = 'edit_structured_data', 'Edit structured data'
    REGENERATE_DRAFT = 'regenerate_draft', 'Regenerate drafts'


class ContractTypeDefinition(models.Model):
    """Configurable contract type registry for dynamic fields and templates"""

    code = models.CharField(
        max_length=20,
        choices=ContractType.choices,
        unique=True,
        help_text="Internal contract type code (matches Contract.contract_type)"
    )
    name = models.CharField(max_length=255, help_text="Display name for admin use")
    description = models.TextField(blank=True)
    is_template_based = models.BooleanField(
        default=False,
        help_text="Whether this contract type uses template-based generation"
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Contract(models.Model):
    # Basic Information
    title = models.CharField(max_length=255)
    contract_type = models.CharField(
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.OTHER
    )
    description = models.TextField(blank=True)
    
    # Parties
    party_a = models.CharField(max_length=255, help_text="First party (usually our company)")
    party_b = models.CharField(max_length=255, help_text="Second party (customer/vendor)")
    
    # Contract Details
    contract_value = models.DecimalField(
        max_digits=18,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="Contract value in IDR (Indonesian Rupiah) - up to 999 trillion"
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Expiry & Renewal
    renewal_reminder_days = models.IntegerField(
        default=30,
        help_text="Days before expiry to send reminder"
    )
    auto_renew = models.BooleanField(
        default=False,
        help_text="Automatically create renewal contract"
    )
    renewal_period_months = models.IntegerField(
        default=12,
        help_text="Renewal period in months"
    )
    parent_contract = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='renewals'
    )
    
    # Status & Workflow
    status = models.CharField(
        max_length=20,
        choices=ContractStatus.choices,
        default=ContractStatus.DRAFT
    )

    # Draft tracking
    is_draft_generated = models.BooleanField(
        default=False,
        help_text="Whether a draft has been generated from a template"
    )
    draft_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time a draft was generated"
    )
    
    # Ownership
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_contracts'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_contracts'
    )
    
    # Documents
    document = models.FileField(upload_to='contracts/%Y/%m/', null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'end_date']),
            models.Index(fields=['contract_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    @property
    def days_until_expiry(self):
        """Calculate days remaining until contract expires"""
        if not self.end_date:
            return None
        delta = self.end_date - timezone.now().date()
        return delta.days
    
    @property
    def is_expiring_soon(self):
        """Check if contract is expiring within reminder period"""
        days = self.days_until_expiry
        if days is None:
            return False
        return 0 < days <= self.renewal_reminder_days
    
    @property
    def contract_duration(self):
        """
        Calculate total contract duration in days (from start_date to end_date)
        Uses inclusive counting (both start and end dates are counted)
        Example: Mar 1, 2026 to Feb 28, 2027 = 365 days (1 year)
        """
        if not self.start_date or not self.end_date:
            return None
        delta = self.end_date - self.start_date
        return delta.days + 1  # +1 for inclusive counting (business logic)
    
    @property
    def contract_duration_display(self):
        """Display contract duration in human-readable format"""
        duration = self.contract_duration
        if duration is None:
            return None
        
        if duration >= 364 and duration <= 366:
            return f"1 year ({duration} days)"
        elif duration >= 729 and duration <= 731:  # ~2 years
            return f"2 years ({duration} days)"
        elif duration >= 1094 and duration <= 1096:  # ~3 years
            return f"3 years ({duration} days)"
        elif duration >= 30 and duration % 30 == 0:
            months = duration // 30
            return f"{months} months ({duration} days)"
        else:
            return f"{duration} days"
    
    @property
    def is_expired(self):
        """Check if contract has expired"""
        if not self.end_date:
            return False
        return timezone.now().date() > self.end_date

    @property
    def is_sales_agreement(self):
        """Check if contract is a sales agreement (template-based)"""
        return self.contract_type in {
            ContractType.GENERAL_TRADE,
            ContractType.MODERN_TRADE,
            ContractType.DISTRIBUTOR,
        }

    @property
    def is_template_based(self):
        """Check if contract type is template-based"""
        type_def = ContractTypeDefinition.objects.filter(
            code=self.contract_type,
            active=True
        ).first()

        if type_def is not None:
            return type_def.is_template_based

        return self.is_sales_agreement

    @property
    def annual_target(self):
        """Return annual target for sales agreements (if configured)"""
        target = ContractTarget.objects.filter(contract=self).first()
        return target.annual_target if target else None
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('contract_detail', kwargs={'pk': self.pk})


class ContractRolePermission(models.Model):
    role = models.CharField(max_length=20, choices=ParticipantRole.choices)
    permission = models.CharField(max_length=32, choices=ContractPermission.choices)
    allowed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['role', 'permission']
        indexes = [
            models.Index(fields=['role', 'permission']),
        ]

    def __str__(self):
        return f"{self.get_role_display()} - {self.get_permission_display()}"


class ContractField(models.Model):
    """Field definitions per contract type for dynamic data capture"""

    FIELD_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('select', 'Select'),
        ('file', 'File Upload'),
    ]

    contract_type = models.ForeignKey(
        ContractTypeDefinition,
        on_delete=models.CASCADE,
        related_name='fields'
    )
    field_key = models.CharField(max_length=100, help_text="Template variable name")
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    options = models.JSONField(null=True, blank=True, help_text="Options for select fields")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['contract_type', 'field_key']
        ordering = ['contract_type', 'position', 'label']

    def __str__(self):
        return f"{self.contract_type.code} - {self.label}"


class ContractData(models.Model):
    """Captured structured data for a contract"""

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='structured_data_versions'
    )
    data = models.JSONField(default=dict, blank=True)
    version = models.PositiveIntegerField(default=1)
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-version']
        unique_together = ['contract', 'version']

    def __str__(self):
        return f"Data v{self.version} for {self.contract.title}"


class ContractDataFile(models.Model):
    """Store uploaded files from dynamic form fields"""

    contract_data = models.ForeignKey(
        ContractData,
        on_delete=models.CASCADE,
        related_name='files'
    )
    field_key = models.CharField(max_length=100)
    file = models.FileField(upload_to='contract_data_files/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.field_key} - {self.file.name}"


class ContractTarget(models.Model):
    """Annual target for sales agreements"""

    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name='target'
    )
    annual_target = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Annual sales target value"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Annual Target for {self.contract.title}"


class ContractQuarter(models.Model):
    """Quarterly targets for sales agreements"""

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='quarters'
    )
    quarter_number = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    target_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    class Meta:
        ordering = ['contract', 'quarter_number']
        unique_together = ['contract', 'quarter_number']
        indexes = [
            models.Index(fields=['contract', 'quarter_number']),
        ]

    def __str__(self):
        return f"Q{self.quarter_number} - {self.contract.title}"


class ContractTemplate(models.Model):
    """HTML templates per contract type with versioning"""

    contract_type = models.ForeignKey(
        ContractTypeDefinition,
        on_delete=models.CASCADE,
        related_name='templates'
    )
    name = models.CharField(max_length=255)
    content = models.TextField(help_text="Use Django template variables like {{ party_name }}")
    active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['contract_type', '-active', '-version', 'name']

    def __str__(self):
        return f"{self.contract_type.code} - v{self.version} - {self.name}"


class ContractDraft(models.Model):
    """Generated drafts with version history"""

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='drafts'
    )
    template = models.ForeignKey(
        ContractTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drafts'
    )
    version = models.PositiveIntegerField(default=1)
    file = models.FileField(upload_to='contract_drafts/%Y/%m/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['contract', 'version']

    def __str__(self):
        return f"Draft v{self.version} for {self.contract.title}"


class ContractParticipant(models.Model):
    """Track all participants involved in a contract"""
    
    NOTIFICATION_PREFERENCES = [
        ('all', 'All Notifications'),
        ('critical', 'Critical Actions Only'),
        ('none', 'No Email Notifications'),
    ]
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contract_participations',
        null=True,
        blank=True,
        help_text="Internal system user (optional if external_email provided)"
    )
    role = models.CharField(
        max_length=20,
        choices=ParticipantRole.choices
    )
    
    # External Participant Support
    external_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email for external participants (vendors, customers, signatories)"
    )
    external_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of external participant"
    )
    
    # Notification Settings
    notification_preference = models.CharField(
        max_length=20,
        choices=NOTIFICATION_PREFERENCES,
        default='critical',
        help_text="Email notification preference for this participant"
    )
    
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['role', 'added_at']
    
    def __str__(self):
        if self.user:
            return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"
        else:
            return f"{self.external_name} ({self.external_email}) - {self.get_role_display()}"
    
    @property
    def email(self):
        """Get email address - prioritize external_email, fall back to user email"""
        if self.external_email:
            return self.external_email
        elif self.user:
            return self.user.email
        return None
    
    @property
    def name(self):
        """Get participant name"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.external_name


class ContractSignature(models.Model):
    """Store digital signatures for contracts"""
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='signatures'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='signatures'
    )
    signature_data = models.TextField(help_text="Base64 encoded signature image")
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-signed_at']
    
    def __str__(self):
        return f"Signature by {self.user.username} on {self.signed_at}"


class ContractDocument(models.Model):
    """Additional documents attached to contracts"""
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='additional_documents'
    )
    title = models.CharField(max_length=255)
    document = models.FileField(upload_to='contract_documents/%Y/%m/')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    version = models.PositiveIntegerField(
        default=1,
        help_text="Document version number for this contract"
    )
    is_current = models.BooleanField(
        default=True,
        help_text="Whether this is the latest document version"
    )
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title


class FinalApprovedDocument(models.Model):
    """Final signed and approved contract document"""
    
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name='final_approved_document'
    )
    document = models.FileField(upload_to='final_contracts/%Y/%m/')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_final_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Notes about the final signed document")
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Final Document for {self.contract.title}"


class AuditLog(models.Model):
    """Comprehensive audit trail for all contract actions"""
    
    ACTION_CHOICES = [
        ('CREATE', 'Contract Created'),
        ('UPDATE', 'Contract Updated'),
        ('STATUS_CHANGE', 'Status Changed'),
        ('DOCUMENT_UPLOAD', 'Document Uploaded'),
        ('FINAL_DOCUMENT_UPLOAD', 'Final Document Uploaded'),
        ('PARTICIPANT_ADDED', 'Participant Added'),
        ('PARTICIPANT_REMOVED', 'Participant Removed'),
        ('SIGNATURE_ADDED', 'Signature Added'),
        ('EMAIL_SENT', 'Email Sent'),
        ('RENEWAL_REMINDER', 'Renewal Reminder Sent'),
        ('EXPIRY_CHECK', 'Expiry Check Performed'),
        ('AUTO_RENEWAL', 'Auto Renewal Created'),
        ('COMMENT_ADDED', 'Comment Added'),
        ('APPROVAL_REQUESTED', 'Approval Requested'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('DATA_SUBMITTED', 'Structured Data Submitted'),
        ('DRAFT_GENERATED', 'Draft Generated'),
        ('DRAFT_UPDATED', 'Draft Updated'),
    ]
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        null=True,
        blank=True
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['contract', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.timestamp}"


class Comment(models.Model):
    """Comments and notes on contracts"""
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_internal = models.BooleanField(
        default=True,
        help_text="Internal comments not visible to customers"
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username if self.user else 'Unknown'} on {self.created_at}"

class ReminderType(models.TextChoices):
    """Reminder types as per core_clm_spec.md"""
    EXPIRY = 'EXPIRY', 'Contract Expiration'
    SIGNATURE_PENDING = 'SIGNATURE_PENDING', 'Signature Pending'
    RENEWAL = 'RENEWAL', 'Renewal Notification'


class ReminderConfiguration(models.Model):
    """
    Configurable reminder schedules as defined in core_clm_spec.md
    
    Supports:
    - Global schedules (applies to all contracts)
    - Contract-type-specific schedules
    - Per-contract overrides
    """
    
    reminder_type = models.CharField(
        max_length=20,
        choices=ReminderType.choices,
        help_text="Type of reminder: expiry, signature pending, or renewal"
    )
    
    # Scope: applies to all contracts, specific type, or specific contract
    scope = models.CharField(
        max_length=20,
        choices=[
            ('GLOBAL', 'Apply to all contracts'),
            ('TYPE', 'Apply to specific contract type'),
            ('CONTRACT', 'Apply to specific contract only'),
        ],
        default='GLOBAL',
        help_text="Scope of this reminder configuration"
    )
    
    contract_type = models.ForeignKey(
        ContractTypeDefinition,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reminder_configurations',
        help_text="Contract type this applies to (if scope=TYPE)"
    )
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reminder_configurations',
        help_text="Specific contract this applies to (if scope=CONTRACT)"
    )
    
    # Schedule configuration
    enabled = models.BooleanField(
        default=True,
        help_text="Enable/disable this reminder"
    )
    
    days_before_trigger = models.IntegerField(
        default=30,
        help_text="Days before contract date to trigger reminder (e.g., 30 days before expiry)"
    )
    
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('ONCE', 'Send once'),
            ('DAILY', 'Send daily'),
            ('WEEKLY', 'Send weekly'),
        ],
        default='ONCE',
        help_text="How often to send reminder once trigger date is reached"
    )
    
    max_occurrences = models.IntegerField(
        default=1,
        help_text="Maximum number of times to send this reminder (0=unlimited)"
    )
    
    recipient_roles = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated roles to notify (e.g., OWNER,SIGNATORY). Empty=all"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, help_text="Admin notes about this configuration")
    
    class Meta:
        ordering = ['reminder_type', 'scope', '-enabled']
        indexes = [
            models.Index(fields=['reminder_type', 'scope', 'enabled']),
            models.Index(fields=['contract_type', 'enabled']),
            models.Index(fields=['contract', 'enabled']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['reminder_type', 'scope'],
                condition=models.Q(contract_type__isnull=True, contract__isnull=True),
                name='unique_global_reminder'
            ),
        ]
    
    def __str__(self):
        scope_name = {
            'GLOBAL': 'Global',
            'TYPE': f"Type: {self.contract_type}",
            'CONTRACT': f"Contract: {self.contract}",
        }.get(self.scope, 'Unknown')
        return f"{self.get_reminder_type_display()} - {scope_name}"
    
    def get_recipient_roles(self):
        """Parse comma-separated roles into list"""
        if not self.recipient_roles:
            return []
        return [r.strip() for r in self.recipient_roles.split(',')]


class ReminderLog(models.Model):
    """
    Log of all sent reminders - prevents duplicates and tracks delivery
    
    Used to implement throttling (e.g., don't send same reminder twice in 7 days)
    """
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('SKIPPED', 'Skipped (throttled)'),
    ]
    
    reminder_config = models.ForeignKey(
        ReminderConfiguration,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text="Reminder configuration that triggered this"
    )
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='reminder_logs',
        help_text="Contract this reminder is about"
    )
    
    reminder_type = models.CharField(
        max_length=20,
        choices=ReminderType.choices,
        help_text="Type of reminder sent"
    )
    
    scheduled_date = models.DateTimeField(
        help_text="When this reminder was scheduled/due"
    )
    
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the reminder was actually sent"
    )
    
    recipients = models.TextField(
        help_text="Comma-separated email addresses that received this"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED'
    )
    
    error_message = models.TextField(
        blank=True,
        help_text="Error details if status=FAILED"
    )
    
    email_subject = models.CharField(
        max_length=255,
        blank=True,
        help_text="Email subject line sent"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['contract', '-scheduled_date']),
            models.Index(fields=['reminder_type', 'status']),
            models.Index(fields=['sent_date']),
        ]
    
    def __str__(self):
        return f"{self.get_reminder_type_display()} for {self.contract.title} ({self.status})"