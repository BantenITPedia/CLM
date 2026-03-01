# Participant Email Notification System - Complete Guide

## Overview

The system now supports sending notifications to both internal and external participants with granular control over notification preferences.

---

## 1. Participant Types

### Internal Participants
- System users (staff, legal, sales team)
- Email from Django User model (`user.email`)
- Can be assigned roles: OWNER, SALES, LEGAL, CUSTOMER, SIGNATORY, APPROVER

### External Participants  
- Vendors, customers, external signatories
- Email stored in `external_email` field
- Name stored in `external_name` field
- Can have same roles as internal users

---

## 2. Notification Preferences

Each participant can choose their notification level:

| Preference | Description | When to Use |
|-----------|-------------|------------|
| **critical** | Only important action items | Recommended - Reduces email noise |
| **all** | All events and updates | For active participants who want full info |
| **none** | No email notifications | For observers or external parties |

**Default:** `critical` (recommended)

---

## 3. Setup: Adding Participants with Email

### Method 1: Admin Interface

#### For Internal Participant:
1. Go to Admin → Contracts → [Select Contract]
2. Scroll to "Contract Participants" section
3. Click "Add another Contract Participant"
4. **User**: Select from system users
5. **Role**: Choose role (LEGAL, SIGNATORY, etc.)
6. **Notification Preference**: Select preference (default: critical)
7. Leave External fields blank
8. Save

#### For External Participant:
1. Go to Admin → Contracts → [Select Contract]
2. Scroll to "Contract Participants" section
3. Click "Add another Contract Participant"
4. **User**: Leave blank (optional)
5. **Role**: Choose role (SIGNATORY, APPROVER, etc.)
6. **External Name**: Enter name (e.g., "John Smith from Acme Inc")
7. **External Email**: Enter email (e.g., vendor@acme.com)
8. **Notification Preference**: Select (default: critical)
9. Save

#### Using Contract Participant Admin:
1. Go to Admin → Contract Participants
2. Click "Add Contract Participant"
3. Select contract, user/external info, role, notification level
4. Save

---

## 4. Automatic Notifications

### Critical Actions (Default - Sent by Default)

**Sent when:** Contract events happen  
**Who receives:** Participants with `critical` or `all` preference

| Action | Recipients | Email | Example |
|--------|-----------|-------|---------|
| Data Submitted | LEGAL, APPROVER | "[\[ACTION\]] Data Submitted for Contract..." | Legal team reviews submitted data |
| Draft Generated | All participants | "[\[DRAFT\]] Generated: Contract (v1)" | Everyone sees new version |
| Signature Needed | SIGNATORY | "[\[ACTION REQUIRED\]] Signature Needed" | Signatories asked to sign |
| Approval Needed | APPROVER | "[\[ACTION REQUIRED\]] Approval Needed" | Approvers asked to approve |
| Expiry Reminder | OWNER | Sent 30 days before expiry | Owner alerted to renewal needed |
| Contract Expired | OWNER | Sent on expiry date | Owner notified of expiry |

---

## 5. Email Templates

The system includes these email templates:

```
templates/emails/
├── data_submitted.html           # When structured data submitted
├── draft_generated.html          # When draft generated
├── signature_request_participant.html   # Signature request to individual
├── approval_request_participant.html    # Approval request to individual
├── contract_created.html         # New contract created
├── legal_review.html             # Legal review needed
├── contract_approved.html        # Contract approved
├── expiry_reminder.html          # Before expiry
└── contract_expired.html         # On expiry
```

---

## 6. Code Examples

### Sending Notification to Individual Participant

```python
from contracts.services import EmailService

# Get participant
participant = contract.participants.get(role='SIGNATORY')

# Send signature request
EmailService.send_signature_request_to_participant(contract, participant)

# Send approval request
EmailService.send_approval_request_to_participant(contract, participant)
```

### Getting Participants with Email

```python
# Get all active participants with emails
for participant in contract.participants.filter(is_active=True):
    if participant.email:  # Uses external_email if set, otherwise user.email
        print(f"{participant.name}: {participant.email}")

# Get only participants who want notifications
legal_participants = contract.participants.filter(
    role='LEGAL',
    notification_preference__in=['critical', 'all'],
    is_active=True
)
```

### Checking Notification Preference

```python
participant = contract.participants.get(pk=1)

# Check if they want notifications
if participant.notification_preference != 'none':
    # Send email
    EmailService.send_signature_request_to_participant(contract, participant)
```

---

## 7. Testing Notifications

### Step 1: Add Participants to Test Contract

```python
from django.contrib.auth.models import User
from contracts.models import Contract, ContractParticipant

contract = Contract.objects.get(pk=5)  # Acme Software contract

# Add internal legal reviewer
legal_user = User.objects.get(username='legal_reviewer')
ContractParticipant.objects.create(
    contract=contract,
    user=legal_user,
    role='LEGAL',
    notification_preference='critical'
)

# Add external vendor as signatory
ContractParticipant.objects.create(
    contract=contract,
    role='SIGNATORY',
    external_name='John Smith',
    external_email='john@acme.com',
    notification_preference='critical'
)
```

### Step 2: Trigger Events

```python
from contracts.services import EmailService
from contracts.models import ContractData, ContractDraft

# 1. Submit data (triggers notification to LEGAL)
data = ContractData.objects.create(
    contract=contract,
    version=1,
    submitted_by=User.objects.get(username='admin'),
    data={'vendor_name': 'Acme Inc', ...}
)
EmailService.send_data_submitted_email(contract, data.submitted_by)

# 2. Generate draft (triggers notification to all participants)
draft = ContractDraft.objects.create(
    contract=contract,
    version=1,
    file=...
)
EmailService.send_draft_generated_email(contract, draft)

# 3. Send signature request to signatory
signatory = contract.participants.get(role='SIGNATORY')
EmailService.send_signature_request_to_participant(contract, signatory)
```

### Step 3: Check Emails Sent

**In development mode**, emails are printed to console:
```
docker-compose logs web | grep "Subject: \["
```

**Production emails** are sent to configured SMTP server (check settings.EMAIL_BACKEND)

---

## 8. Notification Preferences in Admin

### View/Edit Participants:
1. Admin → Contract Participants
2. List shows: Participant Name, Email Address, Role, Notification Preference
3. Click to edit individual preferences

### Bulk Actions (Future Enhancement):
- Could add "Mark all as critical" or "Disable notifications" actions

---

## 9. Best Practices

### For Internal Teams:
- Set LEGAL/APPROVER roles to `critical` (action required)
- Set OWNER role to `critical` (needs to know important events)
- Set observers to `all` (want all updates) or `none` (don't want emails)

### For External Parties:
- Always set to `critical` (avoid overwhelming external participants)
- Only include when action is truly needed
- Test email delivery before going live

### Managing Email Overload:
- Default is `critical` - focuses on actionable items
- Users can self-manage preference in future portal update
- Admins can bulk update via Django shell or admin actions

---

## 10. Future Enhancements

### Phase 2 Features:
- [ ] Self-service notification preferences in contract portal
- [ ] Email digest (batch multiple actions)
- [ ] Slack/Teams notifications for critical actions
- [ ] SMS alerts for urgent items
- [ ] In-app notifications (no email required)
- [ ] Workflow automations (auto-escalate if no action taken)

---

## 11. Troubleshooting

| Issue | Solution |
|-------|----------|
| External participant not getting emails | Check `external_email` field is filled and `notification_preference` ≠ 'none' |
| Email not sending at all | Check Django email settings (settings.EMAIL_BACKEND) and mail server logs |
| Getting duplicates | System deduplicates emails before sending |
| Internal user not getting emails | Check user has .email field filled and notification_preference is set |
| Participant not in list | Check `is_active=True` |

---

## 12. Configuration in Settings

Current settings (if using console backend):
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Dev
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Prod

DEFAULT_FROM_EMAIL = 'noreply@legalclm.com'
EMAIL_HOST = 'smtp.gmail.com'  # or your mail server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

---

## Summary

The system now provides:

✅ **Internal + External Participants** - Flexible participant management  
✅ **Notification Preferences** - Control over email frequency  
✅ **Critical-Only Default** - Reduced email noise  
✅ **Admin Interface** - Easy setup and management  
✅ **Smart Recipients** - Uses external email if available  
✅ **Audit Logging** - All emails logged for compliance  
✅ **Scalable** - Easy to add more notification types  

Start using it by adding participants to contracts in the admin interface!
