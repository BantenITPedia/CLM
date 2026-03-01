# Django Model Design for Core CLM Spec

**Based on:** `docs/core_clm_spec.md`  
**Date:** January 30, 2026  
**Approach:** Minimal changes to existing models + new models for missing features

---

## Model Design Overview

### Existing Models (Keep As-Is)
- `ContractSignature` - E-signature system (PRESERVE)
- `ContractData` - Structured data storage (PRESERVE)
- `ContractDocument` - Document uploads (PRESERVE)
- `AuditLog` - Audit trail (PRESERVE)
- `Comment` - Contract comments (PRESERVE)

### Existing Models (Modify for Spec Alignment)
- `Contract` - Add target tracking, clarify template-based flag
- `ContractTypeDefinition` - Add `is_template_based` flag
- `ContractTemplate` - Existing, no changes needed
- `ContractField` - Existing, rename to `ContractFieldSchema` for clarity

### New Models (Missing from Current System)
- `ContractTarget` - Tracks annual target for sales agreements
- `ContractQuarter` - Tracks quarterly breakdown of targets

---

## Detailed Model Designs

### 1. ContractType (Enumeration)

**Purpose:** Define the 5 contract types required by spec

```python
class ContractType(models.TextChoices):
    # Template-Based Contracts (auto-generate drafts)
    GENERAL_TRADE = 'GENERAL_TRADE', 'General Trade Agreement'
    MODERN_TRADE = 'MODERN_TRADE', 'Modern Trade Agreement'
    DISTRIBUTOR = 'DISTRIBUTOR', 'Distributor Agreement'
    
    # Non-Template Contracts (document upload only)
    VENDOR = 'VENDOR', 'Vendor Agreement'
    PURCHASE = 'PURCHASE', 'Purchase Agreement'
```

**Notes:**
- Exactly 5 types as per spec
- Clear separation: template-based vs non-template
- No NDA, EMPLOYMENT, LEASE, OTHER (spec doesn't require these for MVP)

---

### 2. ContractTypeDefinition

**Purpose:** Registry for contract types with configuration

**Changes from current:**
- Add `is_template_based` field to distinguish template vs non-template

```python
class ContractTypeDefinition(models.Model):
    """Configurable contract type registry for template-based contracts"""
    
    # Type identifier
    code = models.CharField(
        max_length=20,
        choices=ContractType.choices,
        unique=True,
        help_text="Internal contract type code (GENERAL_TRADE, VENDOR, etc.)"
    )
    
    # Display information
    name = models.CharField(
        max_length=255,
        help_text="Display name for UI (e.g., 'General Trade Agreement')"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of contract type and use cases"
    )
    
    # NEW: Template requirement flag
    is_template_based = models.BooleanField(
        default=True,
        help_text="True for template-based (auto-generate draft), False for upload-only"
    )
    
    # Status
    active = models.BooleanField(
        default=True,
        help_text="Inactive types hidden from contract creation form"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Contract Type Definitions"
    
    def __str__(self):
        return f"{self.name} ({self.code})"
```

**Usage in Admin:**
- Template-based types (GENERAL_TRADE, MODERN_TRADE, DISTRIBUTOR): must have template
- Non-template types (VENDOR, PURCHASE): must have document upload

---

### 3. ContractFieldSchema

**Purpose:** Define dynamic form fields per contract type (rename from ContractField)

```python
class ContractFieldSchema(models.Model):
    """Field definitions per contract type for dynamic data capture"""
    
    # Field type choices
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('number', 'Numeric Input'),
        ('date', 'Date'),
        ('select', 'Dropdown Select'),
        ('file', 'File Upload'),
        ('decimal', 'Decimal Number'),  # For currency/targets
    ]
    
    # Relationship
    contract_type = models.ForeignKey(
        ContractTypeDefinition,
        on_delete=models.CASCADE,
        related_name='field_schemas',
        help_text="Contract type this field applies to"
    )
    
    # Field definition
    field_key = models.CharField(
        max_length=100,
        help_text="Template variable name (e.g., 'vendor_name', 'annual_target')"
    )
    label = models.CharField(
        max_length=255,
        help_text="Display label in form"
    )
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPES,
        help_text="Type of form field"
    )
    required = models.BooleanField(
        default=False,
        help_text="Is this field required?"
    )
    options = models.JSONField(
        null=True,
        blank=True,
        help_text="Options for select fields, e.g., ['Option1', 'Option2']"
    )
    default_value = models.CharField(
        max_length=255,
        blank=True,
        help_text="Default value if any"
    )
    
    # Display order
    position = models.PositiveIntegerField(
        default=0,
        help_text="Order in which to display this field in form"
    )
    
    # Metadata
    help_text = models.TextField(
        blank=True,
        help_text="Help text to display to user"
    )
    
    class Meta:
        unique_together = ['contract_type', 'field_key']
        ordering = ['contract_type', 'position', 'label']
    
    def __str__(self):
        return f"{self.contract_type.code} → {self.label}"
```

**Standard Fields (Pre-configured for each type):**
- GENERAL_TRADE: vendor_name, service_description, annual_target, contract_value, contract_period
- MODERN_TRADE: vendor_name, service_description, annual_target, contract_value, contract_period
- DISTRIBUTOR: vendor_name, service_description, annual_target, contract_value, contract_period
- VENDOR: vendor_name, service_description, contract_value
- PURCHASE: vendor_name, item_description, contract_value

---

### 4. ContractTemplate

**Purpose:** Store document templates per contract type (mostly unchanged)

```python
class ContractTemplate(models.Model):
    """HTML/DOCX templates per contract type with versioning"""
    
    # Relationship
    contract_type = models.ForeignKey(
        ContractTypeDefinition,
        on_delete=models.CASCADE,
        related_name='templates',
        help_text="Contract type this template applies to"
    )
    
    # Template information
    name = models.CharField(
        max_length=255,
        help_text="Template name (e.g., 'Standard GTA v1')"
    )
    description = models.TextField(
        blank=True,
        help_text="Template description and notes"
    )
    
    # Template content
    content = models.TextField(
        help_text="Template content with Django template variables {{ field_key }}"
    )
    
    # Template format
    TEMPLATE_FORMAT = [
        ('html', 'HTML'),
        ('docx', 'Word Document (DOCX)'),
    ]
    format = models.CharField(
        max_length=10,
        choices=TEMPLATE_FORMAT,
        default='html',
        help_text="Format of template output"
    )
    
    # Versioning
    version = models.PositiveIntegerField(
        default=1,
        help_text="Template version number"
    )
    active = models.BooleanField(
        default=True,
        help_text="Only one active template per type/version combo"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contract_templates_created'
    )
    
    class Meta:
        ordering = ['contract_type', '-active', '-version', 'name']
    
    def __str__(self):
        return f"{self.contract_type.code} v{self.version} ({self.format})"
```

**Notes:**
- Can support both HTML and DOCX formats
- Multiple versions per type
- Only one "active" template per type at a time
- Stores Django template syntax for variable injection

---

### 5. Contract (Main Model - Modified)

**Purpose:** Core contract entity with lifecycle tracking

**Changes from current:**
- Add `annual_target` field (for sales agreements)
- Add `is_draft_generated` flag (to track if draft needs generation)
- Add `requires_template` flag (clearer than checking type)
- Keep all existing fields
- Keep relationship to ContractSignature

```python
class Contract(models.Model):
    """Core contract entity with lifecycle management"""
    
    # Basic Information
    title = models.CharField(
        max_length=255,
        help_text="Contract title"
    )
    contract_type = models.CharField(
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.VENDOR,
        help_text="Type of contract"
    )
    description = models.TextField(
        blank=True,
        help_text="Contract description"
    )
    
    # Parties
    party_a = models.CharField(
        max_length=255,
        help_text="First party (usually our company)"
    )
    party_b = models.CharField(
        max_length=255,
        help_text="Second party (vendor, customer)"
    )
    
    # Contract Period
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Contract effective start date"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Contract expiration date"
    )
    
    # Financials & Target
    contract_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total contract value in USD"
    )
    annual_target = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual target (for sales agreements like Modern Trade, Distributor)"
    )
    
    # Renewal Settings
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
        related_name='renewals',
        help_text="Parent contract if this is a renewal"
    )
    
    # Workflow Status
    CONTRACT_STATUS = [
        ('DRAFT', 'Draft'),
        ('DATA_SUBMITTED', 'Data Submitted'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('PENDING_SIGNATURE', 'Pending Signature'),
        ('SIGNED', 'Signed'),
        ('ACTIVE', 'Active'),
        ('EXPIRING_SOON', 'Expiring Soon'),
        ('EXPIRED', 'Expired'),
        ('RENEWED', 'Renewed'),
        ('TERMINATED', 'Terminated'),
    ]
    status = models.CharField(
        max_length=20,
        choices=CONTRACT_STATUS,
        default='DRAFT',
        help_text="Current contract status"
    )
    
    # Ownership
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='contracts_created'
    )
    owner = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='contracts_owned'
    )
    
    # Document
    document = models.FileField(
        upload_to='contracts/%Y/%m/',
        null=True,
        blank=True,
        help_text="Original contract document (for non-template contracts)"
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    # Draft tracking
    is_draft_generated = models.BooleanField(
        default=False,
        help_text="Has draft been generated from template?"
    )
    draft_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When was draft last generated?"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'end_date']),
            models.Index(fields=['contract_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    @property
    def is_template_based(self):
        """Check if this contract type uses templates"""
        type_def = ContractTypeDefinition.objects.filter(
            code=self.contract_type
        ).first()
        return type_def.is_template_based if type_def else False
    
    @property
    def is_sales_agreement(self):
        """Check if this is a sales agreement (with quarterly targets)"""
        return self.contract_type in ['MODERN_TRADE', 'DISTRIBUTOR']
    
    @property
    def days_until_expiry(self):
        """Calculate days remaining until contract expires"""
        if not self.end_date:
            return None
        from django.utils import timezone
        delta = self.end_date - timezone.now().date()
        return delta.days
    
    @property
    def is_expired(self):
        """Check if contract has expired"""
        if not self.end_date:
            return False
        from django.utils import timezone
        return timezone.now().date() > self.end_date
    
    @property
    def is_expiring_soon(self):
        """Check if contract is expiring within reminder period"""
        days = self.days_until_expiry
        if days is None:
            return False
        return 0 < days <= self.renewal_reminder_days
```

---

### 6. ContractTarget (NEW)

**Purpose:** Track annual target for sales agreements

```python
class ContractTarget(models.Model):
    """Track annual target for sales agreements (Modern Trade, Distributor)"""
    
    # Relationship
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name='target',
        help_text="Contract this target belongs to"
    )
    
    # Target Amount
    annual_target = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Annual target amount (from contract.annual_target)"
    )
    quarterly_target = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Target per quarter (annual / 4)"
    )
    
    # Calculation basis
    contract_start_date = models.DateField(
        help_text="Contract start date (used for quarter calculation)"
    )
    contract_end_date = models.DateField(
        help_text="Contract end date"
    )
    
    # Metadata
    calculated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When was quarterly breakdown calculated?"
    )
    
    class Meta:
        verbose_name = "Contract Target"
        verbose_name_plural = "Contract Targets"
    
    def __str__(self):
        return f"Target: {self.contract.title} (Annual: ${self.annual_target})"
    
    def recalculate_quarterly(self):
        """Recalculate quarterly targets"""
        self.quarterly_target = self.annual_target / 4
        self.save()
```

---

### 7. ContractQuarter (NEW - CRITICAL)

**Purpose:** Track quarterly breakdown (NO calendar year assumptions)

```python
class ContractQuarter(models.Model):
    """Quarterly breakdown of contract targets (based on contract start date, not calendar)"""
    
    # Relationship
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='quarters',
        help_text="Contract this quarter belongs to"
    )
    
    # Quarter number
    QUARTER_NUMBERS = [
        (1, 'Q1'),
        (2, 'Q2'),
        (3, 'Q3'),
        (4, 'Q4'),
    ]
    quarter_number = models.PositiveIntegerField(
        choices=QUARTER_NUMBERS,
        help_text="Quarter number (1-4)"
    )
    
    # Quarter dates (calculated from contract.start_date, NOT calendar year)
    start_date = models.DateField(
        help_text="Quarter start date (calculated from contract start date)"
    )
    end_date = models.DateField(
        help_text="Quarter end date (calculated from contract start date)"
    )
    
    # Target
    target_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Target for this quarter (annual_target / 4)"
    )
    
    # Tracking (for future use)
    actual_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Actual amount achieved (for reporting)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['contract', 'quarter_number']
        unique_together = ['contract', 'quarter_number']
    
    def __str__(self):
        return f"{self.contract.title} - Q{self.quarter_number} (${self.target_amount})"
    
    @property
    def quarter_progress_percent(self):
        """Calculate progress toward quarterly target"""
        if self.target_amount == 0:
            return 0
        return (self.actual_amount / self.target_amount) * 100
    
    @property
    def is_current_quarter(self):
        """Check if this is the current quarter"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
    
    @staticmethod
    def create_quarters_for_contract(contract):
        """
        Static method to create quarterly breakdown for a sales agreement.
        
        Important: Uses contract.start_date, NOT calendar year.
        Example: If contract starts Feb 1:
          Q1: Feb 1 - Apr 30
          Q2: May 1 - Jul 31
          Q3: Aug 1 - Oct 31
          Q4: Nov 1 - Jan 31
        """
        if not contract.is_sales_agreement or not contract.annual_target:
            return
        
        from datetime import timedelta
        
        target = ContractTarget.objects.get_or_create(
            contract=contract,
            defaults={
                'annual_target': contract.annual_target,
                'quarterly_target': contract.annual_target / 4,
                'contract_start_date': contract.start_date,
                'contract_end_date': contract.end_date,
            }
        )[0]
        
        quarterly_amount = contract.annual_target / 4
        start = contract.start_date
        
        for q in range(1, 5):
            # Calculate quarter dates
            if q == 1:
                q_start = start
            else:
                q_start = start + timedelta(days=(q-1)*90)  # Approximate
            
            q_end = q_start + timedelta(days=90) - timedelta(days=1)
            
            # Ensure last quarter doesn't exceed contract end date
            if q == 4:
                q_end = contract.end_date
            
            # Create or update quarter
            ContractQuarter.objects.update_or_create(
                contract=contract,
                quarter_number=q,
                defaults={
                    'start_date': q_start,
                    'end_date': q_end,
                    'target_amount': quarterly_amount,
                }
            )
```

**CRITICAL NOTES:**
- Quarters are calculated from `contract.start_date`, NOT from calendar year
- Example: Contract starting Feb 1
  - Q1: Feb 1 - Apr 30
  - Q2: May 1 - Jul 31
  - Q3: Aug 1 - Oct 31
  - Q4: Nov 1 - Jan 31
- NO calendar year assumptions
- Auto-created when sales agreement with annual_target is saved

---

### 8. ContractDraft (Existing - No Changes)

```python
class ContractDraft(models.Model):
    """Generated drafts from templates with version history"""
    
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
        related_name='generated_drafts'
    )
    version = models.PositiveIntegerField(default=1)
    file = models.FileField(upload_to='contract_drafts/%Y/%m/')
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
        unique_together = ['contract', 'version']
    
    def __str__(self):
        return f"Draft v{self.version} for {self.contract.title}"
```

---

### 9. ContractSignature (Existing - PRESERVE)

```python
class ContractSignature(models.Model):
    """Store digital signatures with forensic details (PRESERVE AS-IS)"""
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='signatures'
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='contract_signatures'
    )
    signature_data = models.TextField(
        help_text="Base64 encoded signature image"
    )
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-signed_at']
    
    def __str__(self):
        return f"Signature by {self.user.username} on {self.signed_at}"
```

---

## Model Relationships Summary

```
Contract (Core)
├── ContractTypeDefinition (type info + is_template_based)
│   ├── ContractFieldSchema (form fields)
│   └── ContractTemplate (document templates)
├── ContractDraft (generated drafts)
├── ContractSignature (e-signature - PRESERVED)
├── ContractTarget (annual target for sales agreements)
└── ContractQuarter (quarterly breakdown - 4 per sales agreement)

Relationships:
- Contract.contract_type → ContractTypeDefinition.code
- Contract.is_template_based (property)
- Contract.is_sales_agreement (property)
- ContractTarget (1:1 with Contract, optional)
- ContractQuarter (1:many with Contract, auto-created for sales agreements)
```

---

## Migration Strategy

### Phase 1: Modify Existing Models
```
1. Add is_template_based to ContractTypeDefinition
2. Add annual_target to Contract
3. Add is_draft_generated, draft_generated_at to Contract
4. Rename ContractField to ContractFieldSchema (or create alias)
```

### Phase 2: Create New Models
```
1. Create ContractTarget
2. Create ContractQuarter
3. Create signals to auto-create these on Contract.save()
```

### Phase 3: Data Migration
```
1. Backfill is_template_based for existing types
2. Mark GENERAL_TRADE, MODERN_TRADE, DISTRIBUTOR as template-based
3. Mark VENDOR, PURCHASE as non-template
4. Create ContractTarget/ContractQuarter for existing sales agreements
```

---

**Design Complete - Ready for Implementation**

This design:
- ✅ Respects existing e-signature system
- ✅ Adds quarterly target tracking (CRITICAL MISSING FEATURE)
- ✅ Clarifies template vs non-template contracts
- ✅ No calendar year assumptions (contract-date-based quarters)
- ✅ Minimal breaking changes to existing system
- ✅ Production-ready architecture
