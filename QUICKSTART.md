# 🚀 Legal CLM - Quick Start Guide

Get your Legal Contract Lifecycle Management system running in **3 minutes**!

## Prerequisites

- Windows 10/11 with WSL2 or macOS/Linux
- Docker Desktop installed and running
- 4GB RAM available
- 10GB disk space

---

## Step 1: Start the Application (30 seconds)

Open PowerShell/Terminal in the project directory and run:

```powershell
docker-compose up --build
```

**What's happening:**
- Building Docker images (first time takes 2-3 minutes)
- Starting PostgreSQL database
- Starting Redis
- Running Django migrations
- Creating superuser automatically
- Starting Celery worker and beat
- Starting Nginx

**Wait for:** `"ready"` messages from all services.

---

## Step 2: Access the Application (10 seconds)

Open your browser and go to:

**Application:** http://localhost

**Login with:**
- Username: `admin`
- Password: `admin123`

---

## Step 3: Create Your First Contract (2 minutes)

1. Click **"Create Contract"** in the sidebar
2. Fill in the form:
   - **Title:** "My First NDA"
   - **Type:** "Non-Disclosure Agreement"
   - **Party A:** "My Company Inc"
   - **Party B:** "Client Company LLC"
   - **Contract Value:** 25000
   - **Start Date:** Today
   - **End Date:** 1 year from today
   - **Renewal Reminder Days:** 30
3. Click **"Create Contract"**

**Result:**
- ✅ Contract created
- ✅ Email notification sent (visible in Docker logs)
- ✅ Audit log entry created
- ✅ Dashboard statistics updated

---

## Step 4: Test Digital Signature (1 minute)

1. On the contract detail page, click **"Add"** in Participants
2. Add yourself as a **"Signatory"**
3. Click **"Sign Contract"** button
4. Draw your signature on the canvas
5. Click **"Sign Contract"**

**Result:**
- ✅ Signature captured and saved
- ✅ Signature visible on contract page
- ✅ Email notification sent
- ✅ Status may auto-update to "Signed"

---

## Step 5: Test Email System (1 minute)

Check the Docker logs to see email notifications:

```powershell
docker-compose logs web | Select-String "Subject:"
```

You should see emails for:
- Contract created
- Participant added
- Signature added

---

## Step 6: Test Celery Tasks (30 seconds)

Manually trigger the expiry check:

```powershell
docker-compose exec web python manage.py shell
```

Then paste:

```python
from contracts.tasks import check_contract_expiry
result = check_contract_expiry()
print(result)
exit()
```

**Result:** Task executes and returns statistics.

---

## 🎉 Success!

Your Legal CLM system is now fully operational with:

✅ **Contract Management** - Create, edit, view, delete  
✅ **Digital Signatures** - Canvas-based signing  
✅ **Email Notifications** - Automated alerts  
✅ **Expiry Tracking** - Automated monitoring  
✅ **Celery Tasks** - Background processing  
✅ **Audit Trail** - Complete history  

---

## Common Commands

### View All Logs
```powershell
docker-compose logs -f
```

### Stop Application
```powershell
docker-compose down
```

### Restart Application
```powershell
docker-compose restart
```

### Access Django Shell
```powershell
docker-compose exec web python manage.py shell
```

### Create Additional Users
```powershell
docker-compose exec web python manage.py createsuperuser
```

### View Database
```powershell
docker-compose exec db psql -U clm_user legal_clm_db
```

---

## Next Steps

1. **Explore Dashboard** - View statistics and expiring contracts
2. **Add More Contracts** - Test different contract types
3. **Test Status Workflow** - Move contracts through lifecycle
4. **Add Participants** - Assign roles to users
5. **Test Auto-Renewal** - Create contract with auto-renew enabled
6. **Review Audit Logs** - Check comprehensive tracking
7. **Configure SMTP** - Set up real email sending (see README.md)

---

## Troubleshooting

### Application won't start?
```powershell
docker-compose down -v
docker-compose up --build
```

### Can't access http://localhost?
- Check Docker Desktop is running
- Check port 80 is not in use
- Try http://127.0.0.1

### Database errors?
```powershell
docker-compose exec web python manage.py migrate
docker-compose restart web
```

### Need to reset everything?
```powershell
docker-compose down -v
docker volume prune -f
docker-compose up --build
```

---

## Production Deployment

Ready for production? See:
- **README.md** - Complete documentation
- **TEST_SCENARIOS.md** - Comprehensive testing
- **docker-compose.prod.yml** - Production configuration
- **.env.prod.example** - Production environment template

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                    Nginx                         │
│              (Reverse Proxy)                     │
└─────────────────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ↓                         ↓
┌──────────────────┐      ┌──────────────────┐
│   Django App     │      │   Static Files   │
│   (Gunicorn)     │      │   Media Files    │
└──────────────────┘      └──────────────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌─────────┐  ┌─────────┐
│PostgreSQL│  │  Redis  │
└─────────┘  └─────────┘
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
┌──────────┐    ┌──────────┐
│  Celery  │    │  Celery  │
│  Worker  │    │   Beat   │
└──────────┘    └──────────┘
```

---

## Key Features Demonstrated

1. **Contract Lifecycle** - Draft → Review → Approved → Signed → Active → Expiring → Expired
2. **Participant Roles** - Owner, Sales, Legal, Customer, Signatory, Approver
3. **Email Events** - 10 different email types for all lifecycle events
4. **Digital Signatures** - Canvas-based with timestamp and IP tracking
5. **Auto-Renewal** - Automatic contract renewal before expiry
6. **Audit Trail** - Complete logging of all actions
7. **Dashboard** - Real-time statistics and expiry tracking
8. **Celery Tasks** - Daily expiry checks and renewal reminders
9. **Security** - CSRF protection, authentication, role-based access
10. **Production Ready** - Docker, Gunicorn, Nginx, PostgreSQL

---

## Support

For detailed documentation, see **README.md**

For comprehensive testing, see **TEST_SCENARIOS.md**

---

**Built with:** Django 4.2 | PostgreSQL 15 | Celery | Redis | Docker | Bootstrap 5

**Status:** ✅ PRODUCTION READY

**Version:** 1.0.0 (January 2026)
