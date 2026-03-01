# Legal CLM - Manual Test Scenarios

This document provides comprehensive test cases to verify all system functionality.

## Test Environment Setup

**Prerequisites:**
- Docker and Docker Compose installed
- Application running: `docker-compose up`
- Access to http://localhost

**Test User Accounts:**
- Admin: `admin` / `admin123` (created automatically)
- Create additional test users via Django admin

---

## PHASE 1: Authentication & Access Control

### Test Case 1.1: User Login
**Steps:**
1. Navigate to http://localhost
2. Enter username: `admin`
3. Enter password: `admin123`
4. Click "Login"

**Expected Result:**
- ✅ Redirected to dashboard
- ✅ Sidebar navigation visible
- ✅ Username displayed in top navbar

### Test Case 1.2: Invalid Login
**Steps:**
1. Navigate to http://localhost
2. Enter invalid credentials
3. Click "Login"

**Expected Result:**
- ✅ Error message displayed
- ✅ Remains on login page

### Test Case 1.3: Logout
**Steps:**
1. Click "Logout" in sidebar
2. Observe redirection

**Expected Result:**
- ✅ Logged out successfully
- ✅ Redirected to login page
- ✅ Success message displayed

---

## PHASE 2: Contract Creation & Management

### Test Case 2.1: Create Basic Contract
**Steps:**
1. Login as admin
2. Click "Create Contract" in sidebar
3. Fill in form:
   - Title: "Test NDA Agreement"
   - Type: "Non-Disclosure Agreement"
   - Party A: "Acme Corporation"
   - Party B: "ABC Consulting Ltd"
   - Contract Value: 50000
   - Start Date: Today
   - End Date: 1 year from today
   - Renewal Reminder Days: 30
   - Auto-Renew: Unchecked
4. Click "Create Contract"

**Expected Result:**
- ✅ Contract created successfully
- ✅ Redirected to contract detail page
- ✅ Success message displayed
- ✅ Audit log entry created
- ✅ Email notification in console (check Docker logs)

**Verify:**
```bash
docker-compose logs web | grep "Email"
```

### Test Case 2.2: Upload Contract Document
**Steps:**
1. On contract detail page
2. Click "Add" in Documents section
3. Upload a PDF file
4. Enter title: "Main Contract Document"
5. Submit

**Expected Result:**
- ✅ Document uploaded
- ✅ Download link available
- ✅ Audit log entry created

### Test Case 2.3: Edit Contract
**Steps:**
1. Click "Edit" button
2. Change title to "Updated NDA Agreement"
3. Change contract value to 75000
4. Save

**Expected Result:**
- ✅ Contract updated
- ✅ Redirected to detail page
- ✅ Changes reflected
- ✅ Audit log entry created

### Test Case 2.4: View Contract List
**Steps:**
1. Click "All Contracts" in sidebar
2. Observe the contract list

**Expected Result:**
- ✅ Contract appears in list
- ✅ All columns populated correctly
- ✅ Status badge visible
- ✅ Days to expiry calculated

### Test Case 2.5: Filter Contracts
**Steps:**
1. On contracts list page
2. Select "NDA" from Type dropdown
3. Select "DRAFT" from Status dropdown
4. Click "Filter"

**Expected Result:**
- ✅ Only matching contracts displayed
- ✅ Filter values retained

### Test Case 2.6: Search Contracts
**Steps:**
1. Enter "NDA" in search box
2. Click "Filter"

**Expected Result:**
- ✅ Contracts matching search term displayed

---

## PHASE 3: Participant Management

### Test Case 3.1: Add Contract Owner (Automatic)
**Steps:**
1. Check participants section of created contract

**Expected Result:**
- ✅ Contract creator automatically added as OWNER
- ✅ Participant visible in list

### Test Case 3.2: Add Additional Participant
**Steps:**
1. Click "Add" in Participants section
2. Select a user (create one via admin if needed)
3. Select role: "LEGAL"
4. Submit

**Expected Result:**
- ✅ Participant added
- ✅ Role displayed correctly
- ✅ Audit log entry created
- ✅ Email notification sent (if role is CUSTOMER)

### Test Case 3.3: Add Signatory
**Steps:**
1. Add another participant with role "SIGNATORY"
2. Verify addition

**Expected Result:**
- ✅ Signatory added successfully
- ✅ Visible in participants list

---

## PHASE 4: Status Workflow

### Test Case 4.1: Update to Legal Review
**Steps:**
1. In contract detail page
2. Select "Legal Review" from status dropdown
3. Click "Update Status"

**Expected Result:**
- ✅ Status updated
- ✅ Badge changes color
- ✅ Audit log entry created
- ✅ Email sent to legal reviewers

**Verify Email:**
```bash
docker-compose logs web | grep "Legal Review"
```

### Test Case 4.2: Approve Contract
**Steps:**
1. Update status to "Approved"
2. Submit

**Expected Result:**
- ✅ Status changes to Approved
- ✅ Email notification sent
- ✅ Badge color changes to green

### Test Case 4.3: Request Signatures
**Steps:**
1. Update status to "Pending Signature"
2. Submit

**Expected Result:**
- ✅ Status updated
- ✅ Signature request emails sent to signatories

---

## PHASE 5: Digital Signatures

### Test Case 5.1: Sign Contract
**Steps:**
1. Click "Sign Contract" button
2. Draw signature on canvas
3. Click "Sign Contract"

**Expected Result:**
- ✅ Signature captured
- ✅ Signature saved to database
- ✅ Signature preview visible
- ✅ Email notification sent
- ✅ Audit log entry created

### Test Case 5.2: Clear and Redraw Signature
**Steps:**
1. Navigate to sign page
2. Draw something
3. Click "Clear"
4. Draw new signature
5. Submit

**Expected Result:**
- ✅ Clear button works
- ✅ New signature saved correctly

### Test Case 5.3: Prevent Empty Signature
**Steps:**
1. Navigate to sign page
2. Don't draw anything
3. Click "Sign Contract"

**Expected Result:**
- ✅ Alert message: "Please provide your signature"
- ✅ Form not submitted

### Test Case 5.4: Prevent Duplicate Signature
**Steps:**
1. Try to sign the same contract again
2. Navigate to sign page

**Expected Result:**
- ✅ Warning message: "You have already signed"
- ✅ Redirected to detail page

### Test Case 5.5: Auto-Status Update After All Signatures
**Steps:**
1. Ensure at least 1 signatory is added
2. All signatories sign the contract
3. Check contract status

**Expected Result:**
- ✅ Status automatically changes to "SIGNED"
- ✅ Email notification sent

---

## PHASE 6: Comments & Communication

### Test Case 6.1: Add Internal Comment
**Steps:**
1. In contract detail page
2. Enter text: "This contract needs legal review"
3. Check "Internal comment" checkbox
4. Click "Add Comment"

**Expected Result:**
- ✅ Comment added
- ✅ Internal badge visible
- ✅ Timestamp and user displayed
- ✅ Audit log entry created

### Test Case 6.2: Add Public Comment
**Steps:**
1. Add another comment
2. Uncheck "Internal comment"
3. Submit

**Expected Result:**
- ✅ Comment added without internal badge
- ✅ Visible to all participants

---

## PHASE 7: Dashboard & Analytics

### Test Case 7.1: Dashboard Statistics
**Steps:**
1. Navigate to Dashboard
2. Observe statistics cards

**Expected Result:**
- ✅ Total Contracts count correct
- ✅ Active Contracts count correct
- ✅ Expiring Soon count correct
- ✅ Pending Signature count correct

### Test Case 7.2: Expiry Overview
**Steps:**
1. Observe expiry overview section
2. Verify counts

**Expected Result:**
- ✅ 30/60/90 day counts displayed
- ✅ Expired contracts count shown

### Test Case 7.3: Needs Attention Section
**Steps:**
1. Check "Needs Attention" widget
2. Verify contracts listed

**Expected Result:**
- ✅ Contracts requiring action listed
- ✅ Status badges visible
- ✅ Expiry information shown

### Test Case 7.4: Recent Contracts
**Steps:**
1. Check "Recent Contracts" widget

**Expected Result:**
- ✅ Latest contracts displayed
- ✅ Sorted by creation date
- ✅ Link to detail page works

---

## PHASE 8: Expiry & Renewal System

### Test Case 8.1: View Expiring Contracts
**Steps:**
1. Click "Expiring Soon" in sidebar
2. Verify contracts listed

**Expected Result:**
- ✅ Contracts expiring within 30 days shown
- ✅ Days remaining highlighted
- ✅ Auto-renew status visible

### Test Case 8.2: Filter Expiring Period
**Steps:**
1. On expiring contracts page
2. Click "60 Days" button
3. Then "90 Days"

**Expected Result:**
- ✅ List updates based on period
- ✅ Active button highlighted

### Test Case 8.3: View Expired Contracts
**Steps:**
1. Click "Expired" in sidebar
2. Verify list

**Expected Result:**
- ✅ Only expired contracts shown
- ✅ Days since expiry displayed
- ✅ Warning message visible

### Test Case 8.4: Test Expiry Check (Manual)
**Steps:**
1. Create a contract with end date = yesterday
2. Run expiry check task:
```bash
docker-compose exec web python manage.py shell
from contracts.tasks import check_contract_expiry
result = check_contract_expiry()
print(result)
```

**Expected Result:**
- ✅ Task executes without errors
- ✅ Contract status changes to "EXPIRED"
- ✅ Email notification sent
- ✅ Audit log entry created

### Test Case 8.5: Test Renewal Reminder
**Steps:**
1. Create contract with end date = 15 days from now
2. Set renewal_reminder_days = 30
3. Run reminder task:
```bash
docker-compose exec web python manage.py shell
from contracts.tasks import send_renewal_reminders
result = send_renewal_reminders()
print(result)
```

**Expected Result:**
- ✅ Task executes
- ✅ Reminder email sent
- ✅ Audit log entry created

### Test Case 8.6: Test Auto-Renewal
**Steps:**
1. Create contract with:
   - End date = 5 days from now
   - auto_renew = True
   - renewal_period_months = 12
2. Run reminder task (triggers auto-renewal for contracts within 7 days)
3. Check for renewal contract

**Expected Result:**
- ✅ New contract created
- ✅ Title includes "(Renewal)"
- ✅ Parent contract referenced
- ✅ Start date = day after parent end date
- ✅ End date = start + renewal period
- ✅ Participants copied
- ✅ Status = DRAFT
- ✅ Email notification sent
- ✅ Audit logs in both contracts

---

## PHASE 9: Audit Trail

### Test Case 9.1: View Audit Log
**Steps:**
1. Open any contract detail page
2. Scroll to "Audit Log" section

**Expected Result:**
- ✅ All actions logged
- ✅ Timestamps visible
- ✅ User names shown
- ✅ Action details clear
- ✅ Email events included

### Test Case 9.2: Verify Email Tracking
**Steps:**
1. Create a contract
2. Check audit log
3. Look for "Email Sent" entries

**Expected Result:**
- ✅ Email sent events logged
- ✅ Recipients listed in details
- ✅ Email subject included

### Test Case 9.3: Verify Status Change Tracking
**Steps:**
1. Change contract status multiple times
2. Check audit log

**Expected Result:**
- ✅ Each status change logged
- ✅ Old and new values shown
- ✅ User who made change recorded

---

## PHASE 10: Email System

### Test Case 10.1: Verify Console Email Backend
**Steps:**
1. Trigger any email event (create contract)
2. Check Docker logs:
```bash
docker-compose logs web | grep -A 20 "Subject:"
```

**Expected Result:**
- ✅ Email content visible in logs
- ✅ Subject line shown
- ✅ Recipients listed
- ✅ HTML content rendered

### Test Case 10.2: Test All Email Templates
**Trigger each email type and verify in logs:**

1. **Contract Created** - Create new contract
2. **Customer Invitation** - Add participant with CUSTOMER role
3. **Legal Review** - Change status to LEGAL_REVIEW
4. **Contract Approved** - Change status to APPROVED
5. **Signature Request** - Change status to PENDING_SIGNATURE
6. **Contract Signed** - Sign contract
7. **Contract Activated** - Change status to ACTIVE
8. **Expiry Reminder** - Run send_renewal_reminders task
9. **Contract Expired** - Run check_contract_expiry task
10. **Renewal Created** - Trigger auto-renewal

**Expected Result:**
- ✅ All 10 email types send successfully
- ✅ Content relevant to action
- ✅ Links to contract included
- ✅ Professional HTML formatting

---

## PHASE 11: Celery Tasks

### Test Case 11.1: Verify Celery Worker Running
**Steps:**
```bash
docker-compose ps celery_worker
docker-compose logs celery_worker
```

**Expected Result:**
- ✅ Container running
- ✅ No errors in logs
- ✅ "ready" message visible

### Test Case 11.2: Verify Celery Beat Running
**Steps:**
```bash
docker-compose ps celery_beat
docker-compose logs celery_beat
```

**Expected Result:**
- ✅ Container running
- ✅ Scheduler initialized
- ✅ Beat tasks listed

### Test Case 11.3: Test Task Execution
**Steps:**
```bash
docker-compose exec web python manage.py shell
from contracts.tasks import test_email_task
result = test_email_task.delay()
print(result.get())
```

**Expected Result:**
- ✅ Task executes
- ✅ Returns "Test task completed"
- ✅ Visible in celery worker logs

### Test Case 11.4: Verify Scheduled Tasks
**Steps:**
1. Wait for scheduled time (9 AM, 10 AM)
2. Or manually trigger:
```bash
docker-compose exec celery_beat celery -A legal_clm call contracts.tasks.check_contract_expiry
```

**Expected Result:**
- ✅ Tasks run automatically
- ✅ Results logged
- ✅ Actions performed correctly

---

## PHASE 12: Security & Access Control

### Test Case 12.1: Unauthorized Access
**Steps:**
1. Logout
2. Try to access: http://localhost/dashboard/

**Expected Result:**
- ✅ Redirected to login page
- ✅ Cannot access without authentication

### Test Case 12.2: Permission Check
**Steps:**
1. Create two users: UserA and UserB
2. UserA creates a contract
3. Login as UserB
4. Try to edit UserA's contract

**Expected Result:**
- ✅ UserB can view (if participant)
- ✅ UserB cannot edit (not owner)
- ✅ Error message if attempting

### Test Case 12.3: CSRF Protection
**Steps:**
1. Inspect any form
2. Look for CSRF token

**Expected Result:**
- ✅ Hidden CSRF token field present
- ✅ Forms won't submit without token

---

## PHASE 13: File Upload & Download

### Test Case 13.1: Upload Contract Document
**Steps:**
1. Create contract
2. Upload main document
3. Click upload button

**Expected Result:**
- ✅ File uploads successfully
- ✅ File saved to media/contracts/
- ✅ Download link works

### Test Case 13.2: Upload Additional Document
**Steps:**
1. Add additional document via modal
2. Fill in title and upload file
3. Submit

**Expected Result:**
- ✅ Document added
- ✅ Listed in documents section
- ✅ Downloadable

### Test Case 13.3: File Size Limit
**Steps:**
1. Try uploading file > 100MB

**Expected Result:**
- ✅ Error message displayed
- ✅ Upload rejected

---

## PHASE 14: Production Deployment

### Test Case 14.1: Production Build
**Steps:**
```bash
docker-compose -f docker-compose.prod.yml build
```

**Expected Result:**
- ✅ Builds without errors
- ✅ All services built

### Test Case 14.2: Production Environment
**Steps:**
1. Copy `.env.prod.example` to `.env.prod`
2. Configure variables
3. Start production stack:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Expected Result:**
- ✅ All containers start
- ✅ Database migrations run
- ✅ Static files collected
- ✅ Nginx serves application

### Test Case 14.3: SSL Configuration (if SSL certs available)
**Steps:**
1. Place certs in ssl/
2. Update nginx.prod.conf
3. Restart nginx

**Expected Result:**
- ✅ HTTPS works
- ✅ HTTP redirects to HTTPS
- ✅ Security headers present

---

## PHASE 15: Database Operations

### Test Case 15.1: Database Backup
**Steps:**
```bash
docker-compose exec db pg_dump -U clm_user legal_clm_db > backup_test.sql
ls -lh backup_test.sql
```

**Expected Result:**
- ✅ Backup file created
- ✅ File size > 0
- ✅ Contains SQL statements

### Test Case 15.2: Database Restore
**Steps:**
```bash
docker-compose exec -T db psql -U clm_user legal_clm_db < backup_test.sql
```

**Expected Result:**
- ✅ Restore completes without errors
- ✅ Data intact

### Test Case 15.3: Data Persistence
**Steps:**
1. Create a contract
2. Stop containers: `docker-compose down`
3. Start containers: `docker-compose up`
4. Check if contract still exists

**Expected Result:**
- ✅ Contract data persists
- ✅ No data loss

---

## Test Results Checklist

Complete this checklist after running all tests:

### Core Functionality
- [ ] Login/Logout works
- [ ] Contract CRUD operations work
- [ ] Status workflow functions correctly
- [ ] Digital signatures captured and displayed
- [ ] Participants management works
- [ ] Documents upload and download
- [ ] Comments system functional

### Automation
- [ ] Celery worker running
- [ ] Celery beat scheduling tasks
- [ ] Expiry check runs correctly
- [ ] Renewal reminders sent
- [ ] Auto-renewal creates contracts

### Email System
- [ ] All 10 email types send successfully
- [ ] Email content appropriate
- [ ] Recipients correct
- [ ] Audit logs track emails

### Dashboard & Reports
- [ ] Statistics accurate
- [ ] Filters work
- [ ] Search functional
- [ ] Expiry views correct

### Security
- [ ] Authentication required
- [ ] Permission checks work
- [ ] CSRF protection enabled
- [ ] Secure file handling

### Infrastructure
- [ ] Docker containers healthy
- [ ] Database persists data
- [ ] Nginx serves correctly
- [ ] Backups functional

---

## Troubleshooting Failed Tests

### If Email Not Showing in Logs:
```bash
docker-compose logs web | grep -i email
docker-compose logs web | grep -i "Content-Type: text/html"
```

### If Celery Task Fails:
```bash
docker-compose logs celery_worker
docker-compose restart celery_worker
```

### If Database Error:
```bash
docker-compose exec web python manage.py migrate
docker-compose restart web
```

### If Static Files Missing:
```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart nginx
```

---

## Performance Tests (Optional)

### Load Test with Multiple Contracts
```bash
# Create 100 contracts via Django shell
docker-compose exec web python manage.py shell
from contracts.models import Contract
from django.contrib.auth.models import User
user = User.objects.first()
for i in range(100):
    Contract.objects.create(
        title=f"Test Contract {i}",
        party_a="Company A",
        party_b=f"Client {i}",
        owner=user,
        created_by=user
    )
```

**Expected Result:**
- ✅ Dashboard loads quickly
- ✅ List view paginated or handles load
- ✅ Filters still responsive

---

## Final Verification

After completing all tests, verify:

1. ✅ All core features work as expected
2. ✅ No errors in application logs
3. ✅ Database remains consistent
4. ✅ Email notifications functional
5. ✅ Celery tasks execute on schedule
6. ✅ Security measures in place
7. ✅ Production deployment successful

**System Status: PRODUCTION READY** ✅
