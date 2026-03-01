# Implementation Checklist: Core CLM Spec vs Current System

**Master Reference:** `docs/core_clm_spec.md`  
**Analysis Date:** January 30, 2026  
**Deadline:** February 6, 2026 (Production-usable)

---

## EXECUTIVE SUMMARY

The current system has many features implemented, but is **significantly misaligned** with the actual spec in `core_clm_spec.md`. 

**Key Findings:**
- ✅ System has 7 contract types; spec requires exactly 3 template-based + 2 non-template = 5 total
- ✅ Template system exists but uses HTML not DOCX
- ✅ Dynamic forms exist but are overly complex
- ✅ Lifecycle tracking exists but is overly complex (12 states)
- ⚠️ **Quarterly target calculation is completely missing**
- ⚠️ **Target logic for sales agreements is completely missing**
- ✅ Email reminders exist but not fully configurable per spec
- ✅ E-signature system exists and working
- ❌ No "Calendar year assumptions NOT allowed" safeguards in code

---

## SECTION 1: CONTRACT TYPES

### Current Implementation
- 7 contract types in `ContractType` enum: NDA, VENDOR, SERVICE, EMPLOYMENT, LEASE, PURCHASE, OTHER
- Each configurable in admin via `ContractTypeDefinition` model
- Template system supports all types equally

### Spec Requirement
```
Template-Based Contracts (3):
1. General Trade Agreement
2. Modern Trade Agreement
3. Distributor Agreement

Non-Template Contracts (2):
4. Vendor Agreement
5. Purchase Agreement

Total: 5 contract types (not 7)
```

### GAP ANALYSIS

| Contract Type | Current | Spec | Status | Action |
|---|---|---|---|---|
| General Trade Agreement | ❌ Not defined | ✅ Required | MISSING | Create model mapping |
| Modern Trade Agreement | ❌ Not defined | ✅ Required | MISSING | Create model mapping |
| Distributor Agreement | ❌ Not defined | ✅ Required | MISSING | Create model mapping |
| Vendor Agreement | ✅ Exists as SERVICE | ✅ Required (non-template) | MISMATCH | Map to Vendor Agreement, disable template |
| Purchase Agreement | ✅ Exists as PURCHASE | ✅ Required (non-template) | MISMATCH | Map to Purchase Agreement, disable template |
| NDA | ✅ Exists | ❌ Not in spec | EXTRA | Mark as non-spec or v2 feature |
| EMPLOYMENT | ✅ Exists | ❌ Not in spec | EXTRA | Mark as non-spec or v2 feature |
| LEASE | ✅ Exists | ❌ Not in spec | EXTRA | Mark as non-spec or v2 feature |
| OTHER | ✅ Exists | ❌ Not in spec | EXTRA | Mark as non-spec or v2 feature |

### Implementation Checklist
- [ ] **Create Contract Type Mapping Table:**
  - [ ] Map NDA, EMPLOYMENT, LEASE to "Extended" tier (not MVP)
  - [ ] Map OTHER to "Fallback" tier (not MVP)
  - [ ] Keep VENDOR as non-template contract type
  - [ ] Keep PURCHASE as non-template contract type
  - [ ] Rename/add: General Trade Agreement (template-based)
  - [ ] Rename/add: Modern Trade Agreement (template-based)
  - [ ] Rename/add: Distributor Agreement (template-based)

- [ ] **Add `is_template_based` field to ContractTypeDefinition:**
  - [ ] Template-based types: True
  - [ ] Non-template types (Vendor, Purchase): False
  - [ ] Add admin validation: template only for True types

- [ ] **Ensure form validation:**
  - [ ] Template-based contracts: form required, template required
  - [ ] Non-template contracts: form optional, document upload required

---

## SECTION 2: TEMPLATE & FORM SYSTEM

### Current Implementation
- `ContractTemplate` model: stores HTML templates with Django template syntax
- `ContractField` model: defines dynamic form fields per contract type
- `ContractDataForm`: dynamically builds forms from field definitions
- Supports 5 field types: text, number, date, select, file
- Templates rendered via Django template engine → HTML output

### Spec Requirement
```
Each template-based contract has:
- A document template (DOCX implied)
- A form schema (configurable in admin)

Admin can add/remove fields without code changes
Field values injected into templates
```

### GAP ANALYSIS

| Feature | Current | Spec | Status | Action |
|---|---|---|---|---|
| Template storage | HTML Django templates | Document templates (DOCX?) | MISMATCH | Clarify if DOCX required; if yes, add support |
| Form field configuration | Admin interface exists | Admin configurable | ✅ MATCH | Keep existing |
| Dynamic field types | 5 types (text, number, date, select, file) | Not specified | ✅ MATCH | Keep existing |
| Field validation | Built into form | Implied | ✅ MATCH | Keep existing |
| Template rendering | Django template engine | Not specified | ✅ MATCH | Keep existing if DOCX not required |
| Field removal without code | Possible via admin | Explicit requirement | ✅ MATCH | Verify admin UI works smoothly |

### Implementation Checklist

- [ ] **Document Template Format Decision:**
  - [ ] Confirm: Is DOCX template support required?
  - [ ] If YES: Plan python-docx integration
  - [ ] If NO: Confirm HTML templates acceptable

- [ ] **Ensure Form Schema is Fully Configurable:**
  - [ ] Test: Add new field via admin
  - [ ] Test: Remove field via admin
  - [ ] Test: Change field type via admin
  - [ ] Test: Reorder fields via admin
  - [ ] Test: Mark field as required/optional via admin

- [ ] **Template Versioning:**
  - [ ] Ensure admin can create new template versions
  - [ ] Ensure old versions not deleted (maintain history)
  - [ ] Ensure "active" template can be switched

- [ ] **Verify Field Injection Logic:**
  - [ ] Confirm all form fields map to template variables
  - [ ] Test draft generation with injected values
  - [ ] Test missing optional fields don't break rendering

---

## SECTION 3: CONTRACT PERIOD LOGIC

### Current Implementation
- `Contract` model has: `start_date`, `end_date`
- `days_until_expiry` property calculates remaining days
- `is_expiring_soon` property checks reminder period
- `is_expired` property checks past end date

### Spec Requirement
```
Contract has:
- Start Date
- End Date

These dates drive:
- Contract validity
- Reminder schedule
- Quarterly target calculation
```

### GAP ANALYSIS

| Feature | Current | Spec | Status | Action |
|---|---|---|---|---|
| Start Date field | ✅ Exists | ✅ Required | ✅ MATCH | Keep |
| End Date field | ✅ Exists | ✅ Required | ✅ MATCH | Keep |
| Contract validity checking | ✅ Exists (`is_expired`) | ✅ Implied | ✅ MATCH | Keep |
| Reminder schedule calculation | ✅ Exists | ✅ Implied | ✅ MATCH | Keep |
| Quarterly target calculation | ❌ **MISSING** | ✅ **REQUIRED** | **GAP** | **CREATE** |

### Implementation Checklist

- [ ] **Quarterly Target Calculation (CRITICAL):**
  - [ ] Create `ContractQuarter` model to store quarterly targets
  - [ ] Implement logic to divide annual target into 4 equal quarters
  - [ ] Calculate quarters based on contract START DATE (not calendar year)
  - [ ] Example workflow:
    - Start: February
    - Q1: Feb–Apr (target = annual/4)
    - Q2: May–Jul (target = annual/4)
    - Q3: Aug–Oct (target = annual/4)
    - Q4: Nov–Jan (target = annual/4)
  - [ ] Add safeguard: No calendar year assumptions allowed

- [ ] **Contract Period Validation:**
  - [ ] Ensure start_date < end_date
  - [ ] Calculate contract duration in days
  - [ ] Display contract status based on current date vs end_date

- [ ] **Reminder Schedule Calculation:**
  - [ ] Test: Reminders scheduled correctly based on dates
  - [ ] Test: No reminders sent after contract expires
  - [ ] Test: No reminders sent before contract starts

---

## SECTION 4: TARGET & QUARTER LOGIC (Sales Agreements)

### Current Implementation
- `Contract` model has `contract_value` field
- NO quarterly breakdown
- NO target tracking model
- NO quarter calculation logic
- Renewal logic exists but doesn't handle quarterly targets

### Spec Requirement
```
For Sales Agreements (Modern Trade Agreement, Distributor Agreement):
- Annual target is user input
- System divides target into 4 equal quarters
- Quarters calculated based on contract START DATE
- Calendar year assumptions NOT allowed
```

### GAP ANALYSIS

| Feature | Current | Spec | Status | Action |
|---|---|---|---|---|
| Annual target input | ✅ `contract_value` exists | ✅ Required | PARTIAL | Clarify if `contract_value` is "annual target" |
| Quarterly division logic | ❌ **MISSING** | ✅ **REQUIRED** | **GAP** | **CREATE** |
| Quarter date calculation | ❌ **MISSING** | ✅ **REQUIRED** | **GAP** | **CREATE** |
| Target tracking model | ❌ **MISSING** | ✅ Implied | **GAP** | **CREATE** |
| Calendar year safeguards | ❌ No code | ✅ **REQUIRED** | **GAP** | **ADD** |

### Implementation Checklist

- [ ] **Create Contract Quarter Model:**
  - [ ] Fields: contract (FK), quarter_number (1-4), start_date, end_date, target_amount
  - [ ] Auto-populate on contract creation
  - [ ] Validate quarter dates don't overlap
  - [ ] Validate dates don't exceed contract period

- [ ] **Implement Quarter Calculation Logic:**
  - [ ] Service method: `calculate_quarters(contract, annual_target)`
  - [ ] Logic: Divide annual_target by 4
  - [ ] Logic: Calculate dates starting from contract.start_date
  - [ ] Handle edge cases: leap years, month boundaries

- [ ] **Add Safeguard: No Calendar Year Assumptions:**
  - [ ] Add validation: Quarter dates must be based on contract.start_date
  - [ ] Add validation: Q1 always equals contract.start_date (month 1-3 relative to start)
  - [ ] Add test cases for non-standard start dates (Feb, May, Oct, etc.)

- [ ] **Create Quarter Tracking:**
  - [ ] Service method to track actual vs target per quarter
  - [ ] (Note: Current system doesn't track sales, so placeholder for now)

- [ ] **Admin Interface for Quarters:**
  - [ ] Display quarters inline in contract admin
  - [ ] Show quarter dates and targets
  - [ ] Read-only (auto-calculated)

- [ ] **Quarterly Target in Forms:**
  - [ ] If sales agreement: Show form fields for annual target
  - [ ] System auto-calculates quarters on save
  - [ ] Display quarters in contract detail view

---

## SECTION 5: REMINDER SYSTEM

### Current Implementation
- `EmailService` class with 13 email types
- `send_expiry_reminder_email()`: sends reminders for contracts within `renewal_reminder_days`
- `send_renewal_reminders()` Celery task: runs daily at 10 AM
- Configurable `renewal_reminder_days` per contract
- Also supports: signature requests, approval requests, data submitted, draft generated

### Spec Requirement
```
Automated email reminders for:
- Contract expiration
- Signature pending
- Renewal notification

Reminder schedules must be configurable
```

### GAP ANALYSIS

| Feature | Current | Spec | Status | Action |
|---|---|---|---|---|
| Expiration reminders | ✅ Exists | ✅ Required | ✅ MATCH | Keep |
| Signature pending reminders | ✅ Exists | ✅ Required | ✅ MATCH | Keep |
| Renewal reminders | ✅ Exists | ✅ Required | ✅ MATCH | Keep |
| Configurable schedules | ⚠️ Partial | ✅ Required | PARTIAL | Enhance |
| Global config vs per-contract | ⚠️ Per-contract only | Implied flexible | PARTIAL | Add global defaults |
| Reminder history | ❌ No tracking | Implied | MISSING | Add tracking |

### Implementation Checklist

- [ ] **Ensure Reminder Configurability:**
  - [ ] Per-contract `renewal_reminder_days` setting works (already exists)
  - [ ] Test: Can change reminder days in contract form
  - [ ] Test: Reminders respect new days value

- [ ] **Add Global Reminder Defaults:**
  - [ ] Create admin setting for default reminder days (e.g., 30)
  - [ ] Create admin setting for signature reminder days (e.g., 7)
  - [ ] Create admin setting for renewal reminder days (e.g., 30)
  - [ ] Use global defaults if not set per-contract

- [ ] **Add Reminder History Tracking:**
  - [ ] Create `ReminderLog` model: contract, type, sent_date, recipient_email
  - [ ] Log every reminder sent to prevent duplicate sends
  - [ ] Query: Show reminder history in contract detail view

- [ ] **Test Reminder Timing:**
  - [ ] Expiration reminder: X days before end_date
  - [ ] Signature reminder: when status = PENDING_SIGNATURE
  - [ ] Renewal reminder: when auto_renew enabled and within renewal_reminder_days
  - [ ] No reminders sent if contract already expired
  - [ ] No reminders sent if contract not yet started

- [ ] **Verify Celery Tasks Schedule:**
  - [ ] `check_contract_expiry`: runs daily (confirm 9 AM)
  - [ ] `send_renewal_reminders`: runs daily (confirm 10 AM)
  - [ ] Both tasks working in Docker setup

---

## SECTION 6: E-SIGNATURE SYSTEM

### Current Implementation
- `ContractSignature` model: canvas-based capture, Base64 storage, IP/timestamp
- `sign_contract()` view: displays canvas, captures signature
- `SignatureForm`: hidden field for Base64 data
- Signals: auto-trigger signature emails on save
- Audit logging: every signature tracked
- Multi-signatory support: multiple users can sign same contract

### Spec Requirement
```
Uses existing e-signature functionality
```

### GAP ANALYSIS

| Feature | Current | Spec | Status | Action |
|---|---|---|---|---|
| E-signature system exists | ✅ Yes | ✅ Implied required | ✅ MATCH | Keep as-is |
| Canvas-based capture | ✅ Yes | ✅ Implied | ✅ MATCH | Keep |
| Signature storage | ✅ Base64 | ✅ Implied | ✅ MATCH | Keep |
| IP/timestamp tracking | ✅ Yes | ✅ Implied | ✅ MATCH | Keep |
| Audit logging | ✅ Yes | ✅ Implied | ✅ MATCH | Keep |
| Signature workflow | ✅ Multi-user | ✅ Implied | ✅ MATCH | Keep |

### Implementation Checklist

- [ ] **Verify E-Signature System Working:**
  - [ ] Test: Sign contract successfully
  - [ ] Test: Signature stored with IP and timestamp
  - [ ] Test: Email sent on signature
  - [ ] Test: Audit log entry created
  - [ ] Test: Multiple signatures per contract

- [ ] **No Changes Required:**
  - This system is working and meets spec requirements
  - PRESERVE all existing functionality

---

## SECTION 7: CONTRACT CREATION FLOW

### Current Implementation
- User selects contract type in UI
- System loads dynamic form based on type
- User fills form fields
- On submit:
  - ContractData record created (versioned)
  - Draft generated (if template-based)
  - Status changes to DATA_COMPLETED
  - Email sent
  - Contract enters workflow

### Spec Requirement
```
1. User selects contract type
2. System loads dynamic form based on contract type
3. User inputs required data
4. System:
   - Generates draft (template contracts only)
   - Stores contract metadata
   - Initiates signature flow
5. Contract lifecycle begins
```

### GAP ANALYSIS

| Step | Current | Spec | Status | Action |
|---|---|---|---|---|
| Select contract type | ✅ Exists | ✅ Required | ✅ MATCH | Keep |
| Load dynamic form | ✅ Exists | ✅ Required | ✅ MATCH | Keep |
| Input required data | ✅ Exists | ✅ Required | ✅ MATCH | Keep |
| Generate draft | ✅ For template contracts | ✅ Required (template only) | ✅ MATCH | Keep |
| Store metadata | ✅ Exists | ✅ Required | ✅ MATCH | Keep |
| Initiate signature flow | ⚠️ Manual | ✅ Automatic? | UNCLEAR | Clarify: Auto or manual? |
| Lifecycle begins | ✅ Yes | ✅ Required | ✅ MATCH | Keep |

### Implementation Checklist

- [ ] **Clarify Signature Flow Initiation:**
  - [ ] Question: Should signature flow start automatically after form submission?
  - [ ] Current: Manual (user clicks "Sign Contract" link)
  - [ ] Spec says "Initiates signature flow" (unclear if auto or manual)
  - [ ] Decision needed: Auto-redirect or keep manual initiation?

- [ ] **Verify Non-Template Contract Flow:**
  - [ ] For Vendor/Purchase agreements: No draft generation
  - [ ] For Vendor/Purchase agreements: Document upload required
  - [ ] Test form validation: requires document for non-template types

- [ ] **Test Complete Flow End-to-End:**
  - [ ] Create General Trade Agreement (template-based)
  - [ ] Fill form → Draft generated
  - [ ] View draft
  - [ ] Sign contract
  - [ ] Contract enters workflow

---

## SECTION 8: LIFECYCLE TRACKING

### Current Implementation
- 12-step workflow: DRAFT → TERMINATED
- Comprehensive AuditLog: 18 action types
- Status auto-updates: expiry checking, renewal creation
- Role-based permissions: owner, legal, signatory, etc.
- Complex approval routing: legal review, approver roles

### Spec Requirement
```
Manages contract lifecycle
(Not specifically defined what steps are required)
```

### GAP ANALYSIS

| Feature | Current | Spec | Status | Action |
|---|---|---|---|---|
| Lifecycle tracking | ✅ Comprehensive | ✅ Required | ✅ MATCH | Keep |
| Workflow steps | 12 states | Not specified | ✅ MATCH | Keep (exceeds but doesn't contradict) |
| Status updates | ✅ Auto-updates | ✅ Implied | ✅ MATCH | Keep |
| Audit trail | ✅ Comprehensive | ✅ Implied | ✅ MATCH | Keep |
| Permissions | ✅ Role-based | ✅ Implied | ✅ MATCH | Keep |

### Implementation Checklist

- [ ] **Verify Lifecycle is Working:**
  - [ ] Test: Create contract (DRAFT)
  - [ ] Test: Submit data (DATA_COMPLETED)
  - [ ] Test: Move to PENDING_REVIEW
  - [ ] Test: Move to LEGAL_REVIEW
  - [ ] Test: Approve (APPROVED)
  - [ ] Test: Request signature (PENDING_SIGNATURE)
  - [ ] Test: Sign (SIGNED)
  - [ ] Test: Activate (ACTIVE)
  - [ ] Test: Auto-expiry (EXPIRING_SOON → EXPIRED)

- [ ] **No Major Changes Required:**
  - Current 12-step workflow exceeds spec but doesn't contradict it
  - Keep all states and workflow logic

---

## SECTION 9: TECHNICAL CONSTRAINTS

### Current Implementation
- Framework: Django 4.2 LTS ✅
- Database: PostgreSQL 15 ✅
- Background jobs: Celery + Redis ✅
- E-signature: Canvas-based ✅
- Authentication: Django built-in ✅
- Deployment: Docker ✅

### Spec Requirement
```
- Framework: Django
- Use existing e-signature implementation
- Do NOT redesign authentication unless required
- Prioritize working features over abstraction
- Code must be readable and maintainable
```

### GAP ANALYSIS

| Constraint | Current | Status | Action |
|---|---|---|---|
| Django framework | ✅ Django 4.2 LTS | ✅ MATCH | Keep |
| Existing e-signature | ✅ Canvas-based | ✅ MATCH | Keep |
| Authentication | ✅ Django built-in | ✅ MATCH | Keep as-is |
| Working features priority | ✅ System functional | ✅ MATCH | Keep focus |
| Code readability | ⚠️ Moderate | ⚠️ REVIEW | Improve where needed |

### Implementation Checklist

- [ ] **Code Maintainability Review:**
  - [ ] Add docstrings to services (EmailService)
  - [ ] Add docstrings to task functions
  - [ ] Add inline comments for complex logic (quarter calculation)
  - [ ] Review model relationships for clarity

- [ ] **No Authentication Redesign:**
  - [ ] Keep Django built-in User model
  - [ ] Keep existing permission system
  - [ ] No OAuth/SAML/SSO changes

- [ ] **Prioritize Working Over Abstraction:**
  - [ ] Don't over-engineer new features
  - [ ] Keep implementations simple and direct

---

## SECTION 10: DELIVERY PRIORITY

### Spec Requirement
```
1. Core lifecycle working
2. Template generation working
3. Reminder emails working
4. Admin configurability
5. UI improvements (last)

This system must be usable before 6 Feb 2026.
```

### Current Status
1. ✅ Core lifecycle working
2. ✅ Template generation working (HTML)
3. ✅ Reminder emails working
4. ⚠️ Admin configurability (partial)
5. ⚠️ UI (Bootstrap 5, functional but needs review)

### Implementation Checklist (Priority Order)

**PRIORITY 1: Core Lifecycle (DONE - Verify)**
- [ ] Test: All 12 states working
- [ ] Test: Expiry detection working
- [ ] Test: Auto-renewal working

**PRIORITY 2: Template Generation (DONE - Verify)**
- [ ] Test: Template rendering working
- [ ] Test: Fields injected correctly
- [ ] Test: Draft versioning working
- [ ] Decision: DOCX support needed?

**PRIORITY 3: Reminder Emails (DONE - Verify)**
- [ ] Test: Expiration reminders working
- [ ] Test: Signature reminders working
- [ ] Test: Renewal reminders working
- [ ] Test: No duplicate reminders

**PRIORITY 4: Quarterly Targets (CRITICAL MISSING)**
- [ ] Create ContractQuarter model
- [ ] Implement quarter calculation
- [ ] Add quarter tracking
- [ ] Test quarterly logic

**PRIORITY 5: Admin Configurability (PARTIAL - Enhance)**
- [ ] Review: Contract type admin
- [ ] Review: Field definition admin
- [ ] Review: Template admin
- [ ] Add: Reminder settings admin
- [ ] Add: Global configuration options

**PRIORITY 6: UI Improvements (LAST)**
- [ ] Review: Dashboard layout
- [ ] Review: Forms usability
- [ ] Review: Contract detail page
- [ ] Responsive design check

---

## IMPLEMENTATION CHECKLIST SUMMARY

### ✅ ALREADY COMPLETE (Verify & Keep)
- [ ] Django framework and dependencies
- [ ] PostgreSQL database setup
- [ ] E-signature system (canvas-based)
- [ ] Email notification system
- [ ] Celery background tasks
- [ ] Contract lifecycle tracking
- [ ] Template system
- [ ] Dynamic form generation
- [ ] Audit logging
- [ ] Docker deployment

### ⚠️ PARTIALLY COMPLETE (Review & Enhance)
- [ ] Contract type definitions (need to map to spec: 3 template + 2 non-template)
- [ ] Admin interface (need to add more configuration options)
- [ ] Reminder system (working but need global settings)
- [ ] Template format (clarify DOCX vs HTML)
- [ ] Contract creation flow (clarify auto vs manual signature initiation)

### ❌ MISSING (Create)
- [ ] Quarterly target calculation model
- [ ] Quarter creation and tracking logic
- [ ] Calendar year safeguards
- [ ] Global reminder configuration
- [ ] Reminder history tracking
- [ ] Automated tests (basic test coverage)

### 🔍 NEEDS CLARIFICATION
- [ ] Template format: DOCX required or HTML acceptable?
- [ ] Signature flow: Auto-initiate or manual?
- [ ] Contract types: Rename existing to match spec names?
- [ ] Extended types (NDA, EMPLOYMENT, LEASE): Include in MVP or v2?

---

## NEXT STEPS

1. **Review this checklist with stakeholders**
2. **Resolve clarification questions**
3. **Set priorities based on Feb 6 deadline**
4. **Implement in order: Core → Template → Reminders → Quarterly → UI**
5. **Test each section thoroughly**
6. **Deploy to production by Feb 6**

---

**Document Generated:** January 30, 2026  
**Status:** Ready for Stakeholder Review  
**No Code Changes Yet** - Awaiting Clarifications
