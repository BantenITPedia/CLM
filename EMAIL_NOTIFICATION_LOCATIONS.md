# 📧 Email & Notification Information Locations

## 1. **Admin Panel - Participant Email Settings** ⚙️
**URL:** `http://localhost/admin/contracts/contractparticipant/`

### Where to see/edit:
- **Internal Participants:** User field shows who the participant is
- **External Participants:** 
  - `external_email` - Email address for external users (vendors, customers, signatories)
  - `external_name` - Name of external participant
  
- **Notification Preference:** 
  - `all` = Sends all notifications (contract updates, data submitted, drafts, etc.)
  - `critical` = Only sends critical actions (signature requests, approval requests)
  - `none` = No email notifications at all

### List View Shows:
- Name (user name or external_name)
- Email (external_email or user email)
- Contract
- Role (OWNER, SALES, LEGAL, CUSTOMER, SIGNATORY, APPROVER)
- **Notification Preference** ← You can filter by this!
- Active status

---

## 2. **Audit Log - All Email History** 📋
**URL:** `http://localhost/admin/contracts/auditlog/`

### What's Tracked:
- **EMAIL_SENT** - Every email that was sent
- Action = 'EMAIL_SENT'
- Details field contains: recipients, email type, participant info
- Timestamp of when email was sent
- User who triggered the action

### Filter by:
- Action = "Email Sent"
- Contract
- User
- Date range

### Example Actions in Audit Log:
```
Action: EMAIL_SENT
Details: "Email notification sent to legal_reviewer (legal@lcms.local) - Data submitted"
Timestamp: 2026-01-28 14:32:15

Action: EMAIL_SENT  
Details: "Email notification sent to vendor@company.com (external) - Signature request"
Timestamp: 2026-01-28 15:45:22
```

---

## 3. **Email Template Files** 📄
**Location:** `templates/emails/`

### Available Email Templates:

**Critical Action Emails (sent to specific participants):**
- `signature_request_participant.html` - For signatories (RED header - ACTION REQUIRED)
- `approval_request_participant.html` - For approvers (YELLOW header - ACTION REQUIRED)

**General Notifications (sent based on notification preference):**
- `data_submitted.html` - When contract data is submitted
- `draft_generated.html` - When contract draft is auto-generated
- `contract_created.html` - When contract is created
- `contract_signed.html` - When contract is signed
- `contract_approved.html` - When contract is approved
- `legal_review.html` - For legal review
- `expiry_reminder.html` - Renewal/expiry reminders
- `renewal_created.html` - Auto-renewal notifications

### Email Content Includes:
- Contract details (type, parties, value, dates)
- Action required (if critical)
- Direct link to contract
- Participant-specific information

---

## 4. **Email Service Logic** ⚙️
**Location:** `contracts/services.py` → `EmailService` class

### Key Methods:

#### `_get_participant_emails(contract, roles, notification_filter)`
```python
# Gets emails of participants based on:
# - Role (LEGAL, SIGNATORY, APPROVER, etc.)
# - Notification preference (critical/all/none)
# - Active status

# Returns list of emails to send to
```

#### `send_data_submitted_email(contract)`
- Sends to: LEGAL & APPROVER roles
- Filter: critical preference (won't send to 'none')
- Prefix: [ACTION] in email subject

#### `send_draft_generated_email(contract)`
- Sends to: all participants
- Filter: critical preference (won't send to 'none')
- Prefix: [DRAFT] in email subject

#### `send_signature_request_to_participant(contract, participant)`
- Sends to: specific SIGNATORY participant
- Filter: critical preference (won't send to 'none')
- Uses: `signature_request_participant.html` template

#### `send_approval_request_to_participant(contract, participant)`
- Sends to: specific APPROVER participant  
- Filter: critical preference (won't send to 'none')
- Uses: `approval_request_participant.html` template

---

## 5. **Database Records** 💾
**In Django Admin, look at:**

### ContractParticipant Table:
```
Fields:
- id (auto)
- contract_id (which contract)
- user_id (internal user, null if external)
- role (OWNER, SALES, LEGAL, CUSTOMER, SIGNATORY, APPROVER)
- external_email (email if external participant)
- external_name (name if external participant)
- notification_preference (all/critical/none)
- added_at (when added)
- is_active (boolean)
```

### AuditLog Table:
```
Fields:
- id (auto)
- contract_id (which contract)
- action (CREATE, UPDATE, EMAIL_SENT, DRAFT_GENERATED, etc.)
- details (JSON with specifics)
- performed_by (user who triggered)
- timestamp (when it happened)
- ip_address (optional)
```

---

## 6. **How Notifications Flow** 📊

### Critical Actions (Signature/Approval):
```
User Action (sign/approve needed)
    ↓
View triggers: send_signature_request_to_participant()
    ↓
Check: participant.notification_preference != 'none'
    ↓
Get: participant.external_email or participant.user.email
    ↓
Send: signature_request_participant.html template
    ↓
Log: AuditLog with action='EMAIL_SENT', details with recipient
```

### General Notifications (Data/Draft):
```
System Action (data submitted/draft generated)
    ↓
Signal/Task triggers: send_data_submitted_email()
    ↓
Filter: LEGAL & APPROVER roles WHERE notification_preference IN ['critical', 'all']
    ↓
Get emails of filtered participants
    ↓
Send: data_submitted.html or draft_generated.html template
    ↓
Log: AuditLog with action='EMAIL_SENT'
```

---

## 7. **Viewing Email Content** 👁️

### In Development (Console Backend):
Emails print to console/terminal where you run Docker:
```
From: Legal Review <notifications@lcms.local>
To: legal_reviewer@example.com, approver@example.com
Subject: [ACTION] Contract Data Submitted - TechCorp NDA

Body:
<HTML email content>
```

### In Production (SMTP Backend):
Emails sent via real SMTP server - check:
- Email inbox for intended recipients
- Email logs/audit trail in this system (AuditLog table)
- Your SMTP provider's logs

---

## 8. **Quick Reference - Where to Check What** 🔍

| What You Want | Where to Look |
|---|---|
| Email address of a participant | Admin → Participants → external_email or user.email |
| Whether someone gets emails | Admin → Participants → notification_preference |
| All emails sent for a contract | Admin → Audit Log → filter by Contract + Action="Email Sent" |
| Who gets notified on action | contracts/services.py → _get_participant_emails() method |
| Email templates/content | templates/emails/*.html files |
| Who was notified and when | AuditLog → details field + timestamp |
| Reason email wasn't sent | AuditLog → filter and check for blocked participant (preference='none') |
| Test sending email | Add participant with external_email, trigger action, check AuditLog |

---

## 9. **Testing Email Notifications** 🧪

### Step 1: Add a Participant
1. Go to Admin → Contracts → [Select Contract]
2. Click "Add Participant"
3. Fill in:
   - **For Internal:** Select User, Role, Notification Preference
   - **For External:** Leave User blank, fill external_name + external_email, Role, Notification Preference

### Step 2: Set Notification Preference
- `critical` - Only gets important emails (signatures, approvals)
- `all` - Gets all emails
- `none` - Gets no emails (test that email NOT sent)

### Step 3: Trigger Action
- Submit contract data → `send_data_submitted_email()` fires
- Generate draft → `send_draft_generated_email()` fires
- Request signature → `send_signature_request_to_participant()` fires

### Step 4: Check Results
1. **Console Output:** Look at terminal where Docker runs - email will print there
2. **Audit Log:** Admin → Audit Log → filter by Action="Email Sent"
3. **Details:** See exactly which participant got notified

---

## 10. **Email Template Variables Available** 📝

All email templates have access to:
```
{{ contract }}           - Contract object
{{ contract.title }}     - Contract title
{{ contract.contract_type }} - Type (NDA, VENDOR, etc.)
{{ contract.value }}     - Contract value
{{ contract.start_date }} - Start date
{{ contract.end_date }}  - End date

{{ participant }}        - Current recipient (if participant-specific)
{{ participant.name }}   - Participant name
{{ participant.email }}  - Participant email
{{ participant.role }}   - Participant role

{{ site_url }}          - Your site URL for action links
```

Use these variables to customize emails for specific recipients!

---

## 📌 Summary

- **Manage who gets emails:** Admin → Participants → Set notification_preference
- **See all emails sent:** Admin → Audit Log → Filter by Email Sent
- **Check email content:** templates/emails/*.html
- **Configure logic:** contracts/services.py → EmailService class
- **Track history:** AuditLog table has every action with timestamp
- **External participants:** Add external_email + external_name instead of selecting user
