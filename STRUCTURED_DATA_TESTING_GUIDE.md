# Complete Structured Data System - Testing Guide

## What is "Structured Data"?

**Structured Data** = Standardized, reusable form fields for capturing contract-specific information.

### Traditional Approach (Limited)
```
Every contract has the same fields:
- Party A
- Party B  
- Start Date
- End Date
```

### Dynamic Approach (What We Built)
```
NDA Contract needs:
  - Party Name
  - Confidentiality Duration
  - Disclosure Date

Vendor Agreement needs:
  - Vendor Name
  - Service Description
  - Payment Terms
  - Start/End Date

Employment Contract needs:
  - Employee Name
  - Salary
  - Position
  - Start Date
```

**Why?** Different contract types have completely different data requirements.

---

## Full System Workflow - Step by Step Test

### PHASE 1: Setup (Admin Panel)

**Goal:** Configure what fields are needed for "Vendor Agreement" contracts

**Steps:**

1. Open http://localhost/admin/ (login: admin/admin123)

2. Click **"Contract type definitions"** → Click **"VENDOR"** (Vendor Agreement)

3. Verify these 7 contract fields are created. If not, click "Add Contract Field":

   | Field Key | Label | Type | Required | Position |
   |-----------|-------|------|----------|----------|
   | vendor_name | Vendor Name | text | ✓ | 1 |
   | service_description | Service Description | text | ✓ | 2 |
   | contract_value | Contract Value | number | ✓ | 3 |
   | payment_terms | Payment Terms | select | ✓ | 4 |
   | start_date | Service Start Date | date | ✓ | 5 |
   | end_date | Service End Date | date | ✓ | 6 |
   | document | Supporting Document | file | ✗ | 7 |

   **For payment_terms select field**, add options in "Options" field (JSON):
   ```json
   ["Net 30", "Net 60", "Net 90", "Upon Delivery"]
   ```

4. Create **Contract Template** for VENDOR:
   - Go to Admin → **"Contract templates"**
   - Add Template:
     - Contract Type: VENDOR
     - Name: Standard Vendor Agreement
     - Content:
     ```html
     <h1>VENDOR SERVICE AGREEMENT</h1>
     <p><b>Vendor:</b> {{ vendor_name }}</p>
     <p><b>Service:</b> {{ service_description }}</p>
     <p><b>Value:</b> ${{ contract_value }}</p>
     <p><b>Terms:</b> {{ payment_terms }}</p>
     <p><b>Period:</b> {{ start_date }} to {{ end_date }}</p>
     ```
     - Active: ✓

---

### PHASE 2: Submit Data (User/Legal Team)

**Goal:** Fill out the dynamic form with contract-specific data

**Steps:**

1. Go to http://localhost/contracts/1/ (the "Test" contract with type=Vendor Agreement)

2. You'll see alert: **"No structured data submitted yet"** with link to Admin

3. Click blue **"Add Data"** button in "Structured Data" card

4. A dynamic form appears with 7 fields:
   - Vendor Name: [text input]
   - Service Description: [text input]
   - Contract Value: [number input]
   - Payment Terms: [dropdown with Net 30/60/90, Upon Delivery]
   - Service Start Date: [date picker]
   - Service End Date: [date picker]
   - Supporting Document: [file upload]

5. Fill in example data:
   ```
   Vendor Name: Acme Software Inc
   Service Description: Cloud hosting and support services
   Contract Value: 50000
   Payment Terms: Net 60
   Start Date: 2026-02-01
   End Date: 2027-01-31
   Document: (upload a test PDF)
   ```

6. Click blue **"Save Data"** button

---

### PHASE 3: Automatic Draft Generation

**What happens automatically:**

1. ✓ Data is saved as **Version 1** with timestamp and user attribution
2. ✓ Files uploaded to cloud storage
3. ✓ **Contract Template is merged with your data** using Django template engine
4. ✓ HTML draft is generated and saved
5. ✓ Email notifications sent to legal team
6. ✓ Contract status auto-updates to **"Data Completed"**

**Result:**

You're redirected to contract detail page showing:
- ✓ **"Structured Data"** card shows submitted data (v1)
- ✓ **"Drafts"** card shows generated draft with download button
- ✓ All uploaded files listed with download links

---

### PHASE 4: Multiple Submissions (Versioning)

**Goal:** Demonstrate multi-version support

**Steps:**

1. In Structured Data card, click **"Edit Data"** button

2. Change some values:
   ```
   Vendor Name: Acme Software Inc (unchanged)
   Contract Value: 55000 (changed from 50000)
   Payment Terms: Net 90 (changed from Net 60)
   ```

3. Upload different/new file

4. Click **"Save Data"**

**What happens:**

- Data saved as **Version 2** (not replacing v1)
- New draft generated from template using v2 data
- "Structured Data" shows Version 2 prominently
- Can click "View Previous Versions" to see all submissions

---

### PHASE 5: Draft Regeneration (Admin/Legal Only)

**Goal:** Regenerate draft if template was updated

**Steps:**

1. As staff/admin, go to Admin → Contract Templates

2. Edit the VENDOR template, change something:
   ```html
   OLD: <p><b>Vendor:</b> {{ vendor_name }}</p>
   NEW: <p><b>Vendor Name:</b> {{ vendor_name }} (Approved)</p>
   ```

3. Return to contract detail page

4. Click **"Regenerate"** button in Drafts card (only shows if data exists)

**Result:**

- New draft version created with updated template
- Old draft still available for download
- Version history preserved

---

## Testing Approval/Signatory Workflows

**Note:** Current system auto-generates drafts when data is submitted.

Future enhancement could add:
- Manual approval workflow (Legal reviews data, approves/rejects)
- Email notifications to stakeholders
- Status tracking (PENDING_REVIEW → LEGAL_REVIEW → APPROVED → PENDING_SIGNATURE)

---

## Key Concepts to Understand

| Component | Purpose |
|-----------|---------|
| **Contract Type Definition** | Registry (NDA, Vendor, Employment, etc.) |
| **Contract Field** | Individual input field (vendor_name, payment_terms, etc.) |
| **Contract Data** | Submitted values (versioned, tracked by user/timestamp) |
| **Contract Template** | HTML template with variables that gets merged with data |
| **Contract Draft** | Generated HTML file (one per data version) |
| **Contract Data File** | Uploaded files from dynamic form fields |

---

## Troubleshooting

### "No dynamic fields configured"
- Go to Admin → Contract Fields
- Add fields for the contract type
- Return to contract and try again

### No "Add Data" button appears
- Contract doesn't have matching contract type in database
- Go to Admin → Contracts → Select contract → verify Type is set

### Draft not generating
- Template might have syntax error
- Check template uses correct variable names matching field_keys
- Example: field_key=`vendor_name` → use `{{ vendor_name }}` in template

### File not uploading
- Ensure field_type is 'file'
- Form must have enctype="multipart/form-data" (already set)
- Media folder must be writable in container

