# Admin Reference Guide - All Models & Configuration

## Quick Access
Admin Panel: http://localhost/admin/ (admin/admin123)

---

## 1. **Contract Type Definitions**
**Purpose:** Configure contract types and their dynamic fields

**Location:** Admin → Contract Type Definitions

### Pre-configured Types:
- **NDA** - Non-Disclosure Agreement
- **VENDOR** - Vendor Agreement  
- **SERVICE** - Service Agreement
- **EMPLOYMENT** - Employment Contract
- **LEASE** - Lease Agreement
- **PURCHASE** - Purchase Agreement
- **OTHER** - Other

**For each type, you can:**
- View/Edit description
- Add dynamic fields (see below)
- Assign templates
- Set as active/inactive

---

## 2. **Contract Fields** (Dynamic Form Fields)
**Purpose:** Define what data needs to be collected for each contract type

**Location:** Admin → Contract Fields

### Example: Vendor Agreement Fields
These are already configured. You can:

| Field Key | Label | Type | Required |
|-----------|-------|------|----------|
| vendor_name | Vendor Company Name | Text | ✓ |
| vendor_contact | Primary Contact | Text | ✓ |
| service_description | Services/Products | Text | ✓ |
| contract_value | Total Contract Value | Number | ✓ |
| payment_terms | Payment Terms | Select | ✓ |
| start_date | Service Start Date | Date | ✓ |
| end_date | Service End Date | Date | ✓ |
| insurance_required | Insurance Required | Select | ✗ |
| sow_document | Statement of Work | File | ✗ |

### How to Add New Field:
1. Click "Add Contract Field"
2. Fill:
   - **Contract type**: Select type (Vendor, NDA, etc.)
   - **Field key**: machine_name (no spaces, lowercase)
   - **Label**: Display name
   - **Field type**: text, number, date, select, or file
   - **Required**: checkbox
   - **Position**: order (1, 2, 3...)
   - **Options**: (JSON array for select: ["Option1", "Option2"])
3. Save

### Field Types:
- **text** - Short text input
- **number** - Numeric input
- **date** - Date picker
- **select** - Dropdown (requires JSON options)
- **file** - File upload

---

## 3. **Contracts**
**Purpose:** Main contract records

**Location:** Admin → Contracts

**Pre-loaded samples:**
- Acme Software Services Agreement (Vendor)
- Sarah Johnson - Senior Developer (Employment)
- TechCorp NDA (NDA)

**Fields to set:**
- **Title**: Contract name
- **Type**: Contract type (linked to type definition)
- **Status**: DRAFT, ACTIVE, PENDING_REVIEW, LEGAL_REVIEW, APPROVED, etc.
- **Owner**: Assigned user
- **Party A/B**: Company names
- **Value**: Contract amount (IDR)
- **Dates**: Start and end dates
- **Renewal**: Auto-renewal settings
- **Description**: Notes

---

## 4. **Contract Fields** (Add/Edit Fields)
**Purpose:** Configure structured data fields for each contract type

**Location:** Admin → Contract Fields

**Configuration Examples:**

### NDA Type Fields:
```
- disclosing_party (text, required)
- receiving_party (text, required)
- confidentiality_period (number, required)
- effective_date (date, required)
- nda_type (select, required) → ["Unilateral", "Bilateral", "Multilateral"]
```

### Employment Type Fields:
```
- employee_name (text, required)
- position_title (text, required)
- annual_salary (number, required)
- start_date (date, required)
- employment_type (select, required) → ["Full-time", "Part-time", "Contract"]
- reporting_to (text, required)
```

---

## 5. **Contract Templates**
**Purpose:** HTML templates that merge with submitted data

**Location:** Admin → Contract Templates

### Pre-loaded Templates:
- Standard NDA Template
- Standard Vendor Agreement Template
- Employment Contract Template
- Service Agreement Template

### How to Create/Edit Template:

1. Click "Add Contract Template"
2. **Contract type**: Select type
3. **Name**: Template name
4. **Content**: HTML with Django template variables
5. **Active**: Check to use this template
6. **Version**: Auto-incremented

### Template Variables (Match Field Keys):
```html
<!-- Example for Vendor Agreement -->
<h1>VENDOR SERVICE AGREEMENT</h1>
<p>Vendor: {{ vendor_name }}</p>
<p>Service: {{ service_description }}</p>
<p>Value: Rp {{ contract_value }}</p>
<p>Terms: {{ payment_terms }}</p>
<p>Period: {{ start_date }} to {{ end_date }}</p>
```

### Template Best Practices:
- Use `{{ variable_name }}` matching contract field keys
- Use HTML formatting for styling
- Test variable names before saving
- Version is auto-tracked

---

## 6. **Contract Data** (Submitted Structured Data)
**Location:** Admin → Contract Data

**Shows:**
- Submitted data values (JSON)
- Version number
- Submitted date/time
- User who submitted
- Related contract
- Attached files

**Versioning:**
- Each submission creates new version
- Old versions preserved
- Latest version used for draft generation

---

## 7. **Contract Data Files** (Uploaded Files)
**Location:** Admin → Contract Data Files

**Shows:**
- Files uploaded via form fields
- Field key (which form field)
- File name and path
- Upload timestamp
- Related contract data

---

## 8. **Contract Drafts** (Generated Documents)
**Location:** Admin → Contract Drafts

**Shows:**
- Generated HTML drafts
- Version number
- Template used
- Creation date
- File download link

**How created:**
- Automatically when data is submitted
- Manually by admin using "Regenerate" button
- One version per data version

---

## 9. **Contract Participants** (People Involved)
**Location:** Admin → Contract Participants

**Roles:**
- OWNER - Contract owner
- SALES - Sales representative
- LEGAL - Legal reviewer
- CUSTOMER - Customer
- SIGNATORY - Will sign
- APPROVER - Has approval authority

**How to add:**
1. Select contract
2. Select user
3. Choose role
4. Save

---

## 10. **Contract Signatures**
**Location:** Admin → Contract Signatures

**Shows:**
- Who signed
- When they signed
- Contract reference

---

## 11. **Contract Documents** (Attached Files)
**Location:** Admin → Contract Documents

**Add Supporting Docs:**
1. Select contract
2. **Title**: Document name
3. **Document**: Upload file
4. **Description**: What it is
5. **Uploaded by**: User uploading
6. Save

**Examples:**
- Signed copies
- Statements of Work
- Schedules/Appendices
- Supporting agreements

---

## 12. **Audit Logs** (Change History)
**Location:** Admin → Audit Logs

**Auto-logged Actions:**
- CREATED - Contract created
- UPDATED - Contract modified
- DATA_SUBMITTED - Data submission
- DRAFT_GENERATED - Draft created
- STATUS_CHANGED - Status update
- etc.

**Shows:**
- User who made change
- What action
- When
- Details/notes
- Contract affected

---

## 13. **Comments** (Notes & Discussion)
**Location:** Admin → Comments

**Add Comment:**
1. Select contract
2. Enter text
3. Mark as internal/external (default: internal)
4. Save

**Internal vs External:**
- **Internal**: Only visible to admin/legal
- **External**: Could be shared (future feature)

---

## 14. **Users** (System Users)
**Location:** Admin → Users

**Pre-created Users:**
- **admin** - Admin/superuser
- **legal_reviewer** - Legal team (staff)
- **sales_rep** - Sales (regular user)

**Roles:**
- **Superuser**: Full access
- **Staff**: Can access admin, has permissions
- **Regular**: Limited to app interface only

---

## Workflow Example

### 1. Setup Phase (Admin)
```
1. Go to Admin → Contract Type Definitions → VENDOR
2. Verify 9 fields are configured (vendor_name, payment_terms, etc.)
3. Go to Admin → Contract Templates
4. Verify "Standard Vendor Agreement Template" exists
5. Template should contain {{ vendor_name }}, {{ payment_terms }}, etc.
```

### 2. Contract Creation (Admin/Sales)
```
1. Admin → Contracts → Add Contract
2. Title: "Acme Software Agreement"
3. Type: VENDOR (Vendor Agreement)
4. Parties: Our Company Inc / Acme Inc
5. Value: $50,000
6. Dates: Jan 27, 2026 - Jan 27, 2027
7. Owner: sales_rep
8. Save
```

### 3. Data Entry (Sales/Legal)
```
1. Go to http://localhost/contracts/5/
2. Click "Add Data"
3. Fill form:
   - Vendor Name: Acme Software Inc
   - Service: Cloud Hosting & Support
   - Value: 50000
   - Terms: Net 60
   - Dates: 2026-01-27 to 2027-01-27
   - Document: Upload SOW.pdf
4. Click "Save Data"
```

### 4. Auto-Generation
```
✓ Data saved as Version 1
✓ Files uploaded and stored
✓ Template merged with data
✓ Draft v1 generated (HTML file)
✓ Email sent to legal team
✓ Status auto-updated
```

### 5. Review & Approval
```
1. Legal reviewer logs in
2. Checks "Structured Data" card
3. Reviews submitted values
4. Reviews "Drafts" card
5. Downloads draft to review
6. Adds comment "Looks good"
7. Admin regenerates if template changed
```

### 6. Multiple Submissions
```
1. Sales clicks "Edit Data"
2. Changes payment terms from Net 60 to Net 90
3. Clicks "Save Data"
4. New Version 2 created
5. Previous Version 1 still available
6. New draft v2 generated
```

---

## Tips & Best Practices

### Field Naming:
- Use lowercase with underscores: `vendor_name`, `payment_terms`
- No spaces or special characters
- Make them match template variables
- Example: field_key=`vendor_name` → use `{{ vendor_name }}` in template

### Templates:
- Test variable names exist as field keys
- Use proper HTML structure
- Include styling with `<style>` tags
- Always close HTML tags properly
- Use meaningful field names in display

### Contracts:
- Always set owner/responsible party
- Fill in party names accurately
- Use consistent contract types
- Set realistic dates
- Add clear descriptions

### Comments:
- Mark internal comments as "Internal"
- Use for audit trail and discussion
- Link to audit logs for reference

### Permissions:
- Admins/staff can see all contracts
- Regular users see assigned contracts
- Participants see their assigned contracts
- Audit logs show who did what

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No fields configured" | Go to Admin → Contract Fields, add fields for contract type |
| Template variables not showing | Check field_key matches {{ variable_name }} in template |
| Draft not generating | Verify template exists and is active |
| File not uploading | Ensure field_type is 'file' in Contract Fields |
| Duplicate participant error | Delete existing participant first, then add again |
| Email not sending | Check EMAIL_BACKEND in settings (default: console for dev) |

---

## Advanced Configuration

### Adding Custom Field Type:
Would require code changes in forms.py and models.py

### Workflow Automation:
- Celery tasks run daily at 9 AM (expiry check) and 10 AM (renewal reminder)
- Auto-status changes based on dates
- Email notifications for key events

### Integration Points:
- Email notifications to stakeholders
- Audit logging of all changes
- Document versioning and history
- Multi-user collaboration via comments

