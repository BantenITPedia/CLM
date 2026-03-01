# CLM SYSTEM – CORE SPECIFICATION (MASTER PROMPT)

## 1. Purpose
Build a Contract Lifecycle Management (CLM) system using Django that:
- Auto-generates contract drafts from templates
- Manages contract lifecycle
- Sends automated email reminders
- Uses existing e-signature functionality
- Is production-usable before 6 Feb 2026

Copilot MUST follow this document as the single source of truth.

---

## 2. Contract Types

### Template-Based Contracts
1. General Trade Agreement
2. Modern Trade Agreement
3. Distributor Agreement

These contracts:
- Use predefined document templates
- Are auto-generated from user input
- Have configurable form fields
- Include contract period and target logic

### Non-Template Contracts
4. Vendor Agreement
5. Purchase Agreement

These contracts:
- Do NOT use templates
- Require document upload
- Are lifecycle-tracked only

---

## 3. Contract Creation Flow

1. User selects contract type
2. System loads dynamic form based on contract type
3. User inputs required data
4. System:
   - Generates draft (template contracts only)
   - Stores contract metadata
   - Initiates signature flow
5. Contract lifecycle begins

---

## 4. Template & Form System

- Each template-based contract has:
  - A document template
  - A form schema (configurable)
- Admin can add/remove fields without code changes
- Field values are injected into templates

---

## 5. Contract Period Logic

- Contract has:
  - Start Date
  - End Date
- These dates drive:
  - Contract validity
  - Reminder schedule
  - Quarterly target calculation

---

## 6. Target & Quarter Logic (Sales Agreements)

- Annual target is user input
- System divides target into 4 equal quarters
- Quarters are calculated based on contract start date
- Example:
  - Start: February
  - Q1: Feb–Apr
  - Q2: May–Jul
  - Q3: Aug–Oct
  - Q4: Nov–Jan

Calendar year assumptions are NOT allowed.

---

## 7. Reminder System

Automated email reminders for:
- Contract expiration
- Signature pending
- Renewal notification

Reminder schedules must be configurable.

---

## 8. Technical Constraints

- Framework: Django
- Use existing e-signature implementation
- Do NOT redesign authentication unless required
- Prioritize working features over abstraction
- Code must be readable and maintainable

---

## 9. Delivery Priority

1. Core lifecycle working
2. Template generation working
3. Reminder emails working
4. Admin configurability
5. UI improvements (last)

This system must be usable before 6 Feb 2026.
