# Email Notification Strategy - Legal CLM

## Current System Overview

### What Exists:
The system currently sends emails for these key events:
1. **Contract Created** → to contract owner/sales team
2. **Legal Review Required** → to legal team
3. **Contract Approved** → to owner
4. **Signature Request** → to signatories
5. **Contract Signed** → to participants
6. **Contract Activated** → to participants
7. **Expiry Reminder** → to owner (30 days before)
8. **Contract Expired** → to owner
9. **Data Submitted** → to legal team
10. **Draft Generated** → to stakeholders

---

## Problem & Solution

### Current Issue:
- Emails use User model email (from auth.User)
- No participant-specific emails yet
- External participants may not be in system
- Cannot easily notify external parties (vendors, customers)

### Recommended Solution:

I recommend a **2-Tier Notification System**:

#### **TIER 1: Internal Notifications** (Current + Enhanced)
- Send to system users who are participants
- Use User.email from Django auth
- Include: contract details, data submitted, drafts ready, signature needed
- **When:** Any status change, data submission, approval needed

#### **TIER 2: External Notifications** (New - Phase 2)
- For external participants (vendors, customers, signatories)
- Store email addresses directly on ContractParticipant (external_email field)
- Simpler notifications: "Action needed" + link to portal
- **When:** Only critical actions (signature request, approval needed)

---

## RECOMMENDED: Practical Approach

**Start Simple, Scale Complex**

### For Now (Phase 1 - SIMPLE):
Only send notifications for these critical events:
1. **Contract Created** → Legal team gets notified
2. **Data Submitted** → Legal team reviews
3. **Signature Required** → Signatories notified
4. **Expiry Reminder** → Owner alerted 30 days before

**Benefits:**
- Reduces email noise
- Focuses on critical actions
- Users aren't overwhelmed
- Easy to expand later

---

## Implementation Plan

### Step 1: Add External Email to Participants

**Modify ContractParticipant Model:**

```python
class ContractParticipant(models.Model):
    contract = ForeignKey(Contract, ...)
    user = ForeignKey(User, ...)
    role = CharField(...)
    added_at = DateTimeField(auto_now_add=True)
    is_active = BooleanField(default=True)
    
    # NEW FIELDS:
    external_email = models.EmailField(
        blank=True, 
        null=True,
        help_text="Email for external participants (vendors, customers)"
    )
    notification_preference = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Notifications'),
            ('critical', 'Critical Actions Only'),  # <- Recommended default
            ('none', 'No Email')
        ],
        default='critical'
    )
```

### Step 2: Enhanced Email Service

```python
class EmailService:
    
    @classmethod
    def send_critical_action_email(cls, contract, action, recipient_email):
        """
        Send simplified email for critical actions
        
        action: 'signature_needed', 'approval_needed', 'data_submitted', etc.
        recipient_email: email address (internal or external)
        """
        if action == 'signature_needed':
            subject = f"Action Required: {contract.title} - Signature Needed"
            message = f"""
            Contract "{contract.title}" requires your signature.
            
            Click here to review: http://localhost/contracts/{contract.pk}/
            
            Action needed by: {contract.end_date}
            """
            
        elif action == 'approval_needed':
            subject = f"Action Required: {contract.title} - Approval Needed"
            message = f"""
            Contract "{contract.title}" is ready for approval.
            
            Review data: http://localhost/contracts/{contract.pk}/
            
            Status: {contract.get_status_display()}
            """
            
        send_email(
            subject=subject,
            message=message,
            recipient_list=[recipient_email],
            html_message=render_to_string('emails/critical_action.html', {...})
        )
```

### Step 3: Who Gets What

| Event | Recipient | Condition |
|-------|-----------|-----------|
| Contract Created | Owner + Legal | Always |
| Data Submitted | Legal Reviewers | If role='LEGAL' |
| Signature Needed | Signatories | If role='SIGNATORY' |
| Approval Needed | Approvers | If role='APPROVER' |
| Expiry Reminder | Owner | 30 days before |
| Contract Activated | All Participants | If notification != 'none' |

---

## Simple Implementation (Recommended Start)

I'll implement this approach:

1. **Add external_email field to ContractParticipant**
2. **Add notification_preference field** (default: 'critical')
3. **Enhance EmailService** with participant-aware sending
4. **Update admin interface** to show/edit emails
5. **Automatic notifications** for critical events only

---

## Benefits

### Simple Version:
✓ Users not overwhelmed with emails  
✓ Focus on actionable items only  
✓ Easy to manage and understand  
✓ Support for internal AND external participants  
✓ Preference to opt-in/opt-out  

### Expandable Later:
- Add workflow triggers (auto-escalate after 3 days if no action)
- Add more detailed notifications as needs grow
- Add SMS notifications
- Add in-app notifications

---

## Should I Implement This?

**My Recommendation:** YES - Implement the Simple Version

**What will be added:**

1. **New Fields:**
   ```
   - external_email (for vendors, customers, external signatories)
   - notification_preference (all / critical / none)
   ```

2. **New Admin Interface:**
   - Show email in participant list
   - Edit notification preferences
   - Preview what emails they'll receive

3. **Smart Notifications:**
   - Automatic to legal team when data submitted
   - Automatic to signatories when signature needed
   - Automatic to owner when expiry near
   - Respects notification_preference setting

4. **Email Templates:**
   - Simple action-oriented emails
   - Clear subject lines
   - Direct links to required action

---

## Example Usage

### In Admin:
```
Contract: Acme Software Agreement
Participant 1:
  - User: john@company.com (internal)
  - Role: Legal Reviewer
  - External Email: (blank)
  - Notifications: Critical Only
  - Email sent when: Data submitted, draft ready for review

Participant 2:
  - User: (none - external)
  - Role: Signatory  
  - External Email: vendor@acme.com
  - Notifications: Critical Only
  - Email sent when: Signature requested
```

### Automatically Sent:
1. Data submitted → john@company.com gets notified
2. Signature needed → vendor@acme.com gets notified
3. Both can click link to view contract details
4. No spam - only critical actions

---

## Questions for You:

1. **Should I implement this now?** (Recommended: YES)
2. **Preference level:** 
   - Simple critical-only? (Recommended)
   - Or comprehensive all-events?
3. **External participants important?** 
   - Need to notify external vendors? (Likely YES)
   - Need to notify external signatories? (Likely YES)

Let me know and I'll implement immediately!
