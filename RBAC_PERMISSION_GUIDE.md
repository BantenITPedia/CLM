# RBAC & Permission System Guide

## Overview

The Legal CLM system uses **Role-Based Access Control (RBAC)** to manage who can do what with contracts. Each user is assigned one or more roles per contract, and each role has specific permissions.

## Current Workflow

```
User (OWNER/SALES) → Creates Contract → Uploads Documents
              ↓
        Status: DRAFT
              ↓
   User submits for review
              ↓
     Status: SUBMITTED
              ↓
Legal Team (LEGAL role) → Reviews Contract
              ↓
   Legal approves/rejects
              ↓
    Status: LEGAL_REVIEW
              ↓
Approver (APPROVER role) → Final approval
              ↓
       Status: APPROVED
              ↓
       Status: ACTIVE
```

---

## User Roles

### 1. **OWNER** (Contract Owner)
- **Who**: The person who creates the contract (usually sales or business user)
- **Permissions**:
  - ✅ View contract
  - ✅ Edit contract details
  - ✅ Delete contract
  - ✅ Update contract status
  - ✅ Manage participants (add/remove people)
  - ✅ Add documents
  - ✅ Upload final signed document
  - ✅ Add comments
  - ✅ Edit structured data

### 2. **SALES** (Sales Representative)
- **Who**: Sales team members working on the contract
- **Permissions**:
  - ✅ View contract
  - ✅ Edit contract details
  - ✅ Add documents
  - ✅ Add comments
  - ✅ Edit structured data

### 3. **LEGAL** (Legal Reviewer)
- **Who**: Legal team members who review and approve contracts
- **Permissions**:
  - ✅ View contract
  - ✅ Update contract status (approve/reject)
  - ✅ Manage participants
  - ✅ Add documents
  - ✅ Upload final signed document
  - ✅ Add comments
  - ✅ Edit structured data
  - ✅ Regenerate contract drafts

### 4. **APPROVER** (Final Approver)
- **Who**: Management/executives who give final approval
- **Permissions**:
  - ✅ View contract
  - ✅ Update contract status
  - ✅ Add comments

### 5. **CUSTOMER** (External Customer)
- **Who**: Customer/partner organizations
- **Permissions**:
  - ✅ View contract
  - ✅ Add comments

### 6. **SIGNATORY** (Authorized Signer)
- **Who**: People authorized to sign the contract
- **Permissions**:
  - ✅ View contract

---

## Available Permissions

| Permission | Description | Who Can Use |
|------------|-------------|-------------|
| `view_contract` | View contract details | All roles |
| `edit_contract` | Edit contract information | OWNER, SALES |
| `delete_contract` | Delete contract | OWNER only |
| `update_status` | Change contract status | OWNER, LEGAL, APPROVER |
| `manage_participants` | Add/remove users | OWNER, LEGAL |
| `add_document` | Upload documents | OWNER, SALES, LEGAL |
| `upload_final_document` | Upload signed contract | OWNER, LEGAL |
| `add_comment` | Add comments/notes | OWNER, SALES, LEGAL, CUSTOMER, APPROVER |
| `edit_structured_data` | Edit contract data fields | OWNER, SALES, LEGAL |
| `regenerate_draft` | Regenerate contract draft | LEGAL only |

---

## How to Set Up Roles & Permissions

### Method 1: Django Admin (Recommended)

1. **Access Admin Panel**
   ```
   URL: http://your-domain/admin/
   Login with staff/superuser account
   ```

2. **Navigate to "Contract Role Permissions"**
   ```
   Admin → Contracts → Contract role permissions
   ```

3. **View/Edit Permissions**
   - You'll see a list of all role-permission combinations
   - Toggle the "Allowed" checkbox to enable/disable
   - Click "Save" at the bottom

4. **Add New Permission Rules**
   - Click "Add Contract Role Permission"
   - Select Role (e.g., LEGAL)
   - Select Permission (e.g., update_status)
   - Check "Allowed" checkbox
   - Save

### Method 2: Assign Roles to Users

#### Via Admin Interface:
1. Go to Admin → Contracts → Contracts
2. Open a contract
3. Scroll to "Contract Participants" section
4. Add user and select their role
5. Save

#### Via Contract Detail Page:
1. Open contract detail page
2. Look for "Participants" or "Team Members" section
3. Click "Add Participant"
4. Select user and role
5. Save

---

## Typical Setup Scenarios

### Scenario 1: Standard Business Contract

**Contract Owner**: Sales Representative (OWNER role)
- Creates contract
- Uploads initial documents
- Submits for legal review

**Legal Reviewer**: Legal Team Member (LEGAL role)
- Reviews contract
- Adds comments/feedback
- Approves or requests changes
- Updates status to LEGAL_REVIEW → APPROVED

**Final Approver**: Department Head (APPROVER role)
- Reviews approved contract
- Gives final approval
- Changes status to ACTIVE

### Scenario 2: Customer-Facing Contract

**Contract Owner**: Account Manager (OWNER role)
**Customer Contact**: External User (CUSTOMER role)
- Can view contract
- Can add comments
- Cannot edit or approve

**Legal Team**: (LEGAL role)
- Reviews and approves
- Uploads final signed document

---

## Staff vs Regular Users

### Staff Users (`is_staff = True`)
- Have ALL permissions automatically
- Can access Django Admin panel
- Should be limited to IT admins and legal team leads

### Regular Users
- Need explicit role assignment per contract
- Permissions based on their role
- Cannot access admin panel

---

## Permission Check Examples

### In Views (Python Code):
```python
from contracts.permissions import has_contract_permission, ContractPermission

# Check if user can edit contract
if has_contract_permission(user, contract, ContractPermission.EDIT_CONTRACT):
    # Allow edit
    pass

# Check if user can approve
if has_contract_permission(user, contract, ContractPermission.UPDATE_STATUS):
    # Show approve button
    pass
```

### In Templates:
```django
{% if can_edit_contract %}
    <button>Edit Contract</button>
{% endif %}
```

---

## Best Practices

### 1. **Principle of Least Privilege**
- Give users only the permissions they need
- Don't make everyone OWNER

### 2. **Clear Role Assignment**
- Assign LEGAL role only to legal team
- Use SALES for sales representatives
- Use APPROVER for management approval

### 3. **Regular Audits**
- Review who has access to sensitive contracts
- Check audit logs regularly
- Remove inactive participants

### 4. **Status-Based Workflow**
- DRAFT → Only owner/sales can edit
- SUBMITTED → Legal can review
- LEGAL_REVIEW → Legal approves
- APPROVED → Awaiting final approval
- ACTIVE → Contract in effect

### 5. **External Users**
- Use CUSTOMER role for external parties
- Consider using external_email for non-system users
- Be careful with sensitive information visibility

---

## Troubleshooting

### User Can't See Contract
- ✓ Check if user is added as participant
- ✓ Check if participant is_active = True
- ✓ Verify user is logged in

### User Can't Edit Contract
- ✓ Check user's role (OWNER or SALES needed)
- ✓ Check ContractRolePermission settings
- ✓ Verify contract is not locked/approved

### Legal Can't Approve
- ✓ Assign LEGAL role to user
- ✓ Check update_status permission
- ✓ Verify contract status allows approval

---

## Database Tables

### `contracts_contractparticipant`
- Links users to contracts with roles
- Fields: `user`, `contract`, `role`, `is_active`

### `contracts_contractrolepermission`
- Defines what each role can do
- Fields: `role`, `permission`, `allowed`

---

## Quick Setup Commands

### Initialize Default Permissions (Run Once)
```bash
python manage.py setup_default_permissions
```

### List All Permissions for a Role
```bash
python manage.py shell
from contracts.permissions import PERMISSION_ROLE_MAP, ParticipantRole
legal_perms = [p for p, roles in PERMISSION_ROLE_MAP.items() if ParticipantRole.LEGAL in roles]
print(legal_perms)
```

---

## Support

For questions or issues with permissions:
1. Check this guide first
2. Review Django Admin → Audit Logs
3. Contact system administrator
4. Check application logs for permission errors
