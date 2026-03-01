# Legal Contract Lifecycle Management (CLM) System

A production-ready Django application for managing legal contracts throughout their entire lifecycle, from creation to expiry and renewal.

## Features

✅ **Complete Contract Management**
- Create, edit, view, and delete contracts
- Multiple contract types (NDA, Vendor, Service, Employment, etc.)
- Status tracking throughout contract lifecycle
- Document upload and management

✅ **Digital Signatures**
- Canvas-based signature capture
- Base64 signature storage
- IP address and timestamp tracking
- Signature verification

✅ **Email Notifications**
- Automated emails for all contract events
- Customizable SMTP configuration
- Console backend for local testing
- Professional HTML email templates

✅ **Expiry & Renewal Management**
- Automatic expiry checking (daily Celery task)
- Configurable renewal reminders
- Auto-renewal capability
- Dashboard with expiry analytics

✅ **Audit Trail**
- Comprehensive logging of all actions
- User tracking for accountability
- Timestamp and IP address capture
- Email sent events tracked

✅ **Role-Based Access**
- Contract owners and participants
- Multiple participant roles (Owner, Sales, Legal, Customer, Signatory, Approver)
- Permission-based access control

✅ **Production-Ready**
- Docker & Docker Compose deployment
- Nginx reverse proxy
- PostgreSQL database with persistence
- Redis for Celery tasks
- Gunicorn WSGI server
- Security best practices

## Tech Stack

- **Backend:** Django 4.2 (LTS)
- **Database:** PostgreSQL 15
- **Cache/Queue:** Redis 7
- **Task Queue:** Celery + Celery Beat
- **Web Server:** Gunicorn + Nginx
- **Frontend:** Bootstrap 5, Vanilla JavaScript
- **Containerization:** Docker & Docker Compose

## Quick Start (Development)

### Prerequisites

- Docker Desktop installed
- Git (optional)

### Installation

1. **Clone or download the repository**

2. **Start the development environment:**

```bash
docker-compose up --build
```

3. **Access the application:**

- Application: http://localhost
- Admin Panel: http://localhost/admin/

4. **Default credentials:**

- Username: `admin`
- Password: `admin123`

### What Gets Created Automatically

- Django application with all migrations applied
- PostgreSQL database with persistent storage
- Redis for Celery tasks
- Celery worker for background tasks
- Celery beat for scheduled tasks
- Nginx reverse proxy
- Superuser account (admin/admin123)

## Project Structure

```
legal-clm/
├── contracts/               # Main Django app
│   ├── models.py           # Data models
│   ├── views.py            # View logic
│   ├── forms.py            # Form definitions
│   ├── admin.py            # Admin interface
│   ├── signals.py          # Signal handlers
│   ├── services.py         # Email service
│   ├── tasks.py            # Celery tasks
│   └── urls.py             # URL routing
├── legal_clm/              # Django project
│   ├── settings.py         # Configuration
│   ├── celery.py           # Celery config
│   ├── urls.py             # Main URL routing
│   └── wsgi.py             # WSGI application
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── contracts/          # Contract templates
│   └── emails/             # Email templates
├── static/                 # Static files (CSS, JS)
├── media/                  # User uploads
├── docker-compose.yml      # Development compose
├── docker-compose.prod.yml # Production compose
├── Dockerfile              # Development Dockerfile
├── Dockerfile.prod         # Production Dockerfile
├── nginx.conf              # Dev nginx config
├── nginx.prod.conf         # Prod nginx config
├── requirements.txt        # Python dependencies
├── .env                    # Dev environment variables
├── .env.prod.example       # Prod env template
└── README.md               # This file
```

## Core Models

### Contract
- Title, type, description, parties
- Start/end dates, contract value
- Renewal settings (reminder days, auto-renew, renewal period)
- Status tracking, ownership
- Document attachment

### ContractParticipant
- Links users to contracts
- Roles: Owner, Sales, Legal, Customer, Signatory, Approver
- Active/inactive status

### ContractSignature
- Digital signature storage (base64)
- User, timestamp, IP address
- User agent tracking

### AuditLog
- Comprehensive action logging
- User and timestamp tracking
- Old/new value comparison
- Email event tracking

### Comment
- Contract comments and notes
- Internal vs external visibility
- User and timestamp

## Email Notifications

The system sends automated emails for:

1. **Contract Created** - When a new contract is created
2. **Customer Invitation** - When a customer is added as participant
3. **Legal Review Required** - When status changes to legal review
4. **Contract Approved** - When contract is approved
5. **Signature Request** - When signature is required
6. **Contract Signed** - When someone signs
7. **Contract Activated** - When contract becomes active
8. **Expiry Reminder** - X days before expiration
9. **Contract Expired** - When contract expires
10. **Renewal Created** - When auto-renewal creates new contract

### Email Configuration

For development (console backend):
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

For production (SMTP):
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Celery Tasks

### Scheduled Tasks (via Celery Beat)

1. **check_contract_expiry** - Runs daily at 9 AM
   - Identifies expired contracts
   - Updates status to EXPIRED
   - Marks contracts as EXPIRING_SOON

2. **send_renewal_reminders** - Runs daily at 10 AM
   - Sends reminders for contracts within reminder period
   - Triggers auto-renewal for eligible contracts
   - Prevents duplicate reminders

3. **create_renewal_contract** - On-demand task
   - Creates renewal contract automatically
   - Copies participants from parent contract
   - Sets new start/end dates
   - Sends notification emails

### Testing Celery

Check if Celery is working:
```bash
docker-compose exec celery_worker celery -A legal_clm inspect active
```

Manually trigger expiry check:
```bash
docker-compose exec web python manage.py shell
>>> from contracts.tasks import check_contract_expiry
>>> check_contract_expiry.delay()
```

## User Workflows

### 1. Contract Creation
1. User logs in
2. Navigates to "Create Contract"
3. Fills in contract details
4. Sets renewal settings
5. Uploads contract document
6. Submits → Email sent to participants

### 2. Contract Review & Approval
1. Legal team receives email notification
2. Reviews contract details
3. Adds comments if needed
4. Updates status to "Approved"
5. Email sent to all participants

### 3. Digital Signature
1. Signatory receives email notification
2. Clicks "Sign Contract" link
3. Draws signature on canvas
4. Submits signature
5. Signature saved with timestamp and IP
6. Email sent confirming signature
7. Status updates when all signatures collected

### 4. Contract Activation
1. All signatures collected
2. Status changes to "Signed"
3. Owner activates contract
4. Status changes to "Active"
5. Email notification sent

### 5. Expiry & Renewal
1. Celery task runs daily
2. Checks contracts approaching expiry
3. Sends reminder emails
4. If auto-renew enabled:
   - Creates renewal contract
   - Copies participants
   - Sends notification
5. If expired:
   - Updates status to "Expired"
   - Sends expiry notification

## Dashboard Features

### Statistics Cards
- Total contracts count
- Active contracts
- Expiring soon
- Pending signature

### Expiry Overview
- Contracts expiring in 30 days
- Contracts expiring in 60 days
- Contracts expiring in 90 days
- Expired contracts

### Needs Attention
- Contracts requiring signature
- Contracts in legal review
- Contracts expiring soon

### Filters
- Contract type
- Status
- Owner
- Date range
- Search by title/party

## API Endpoints

| URL | Method | Description |
|-----|--------|-------------|
| `/` | GET | Login page |
| `/dashboard/` | GET | Main dashboard |
| `/contracts/` | GET | List all contracts |
| `/contracts/create/` | GET/POST | Create contract |
| `/contracts/<id>/` | GET | Contract details |
| `/contracts/<id>/edit/` | GET/POST | Edit contract |
| `/contracts/<id>/delete/` | POST | Delete contract |
| `/contracts/<id>/status/` | POST | Update status |
| `/contracts/<id>/sign/` | GET/POST | Sign contract |
| `/contracts/<id>/participant/` | POST | Add participant |
| `/contracts/<id>/document/` | POST | Add document |
| `/contracts/<id>/comment/` | POST | Add comment |
| `/contracts/expiring/` | GET | Expiring contracts |
| `/contracts/expired/` | GET | Expired contracts |
| `/admin/` | GET | Django admin |

## Production Deployment

### 1. Prepare Environment

Copy and configure production environment:
```bash
cp .env.prod.example .env.prod
```

Edit `.env.prod` and change:
- `SECRET_KEY` - Generate a secure random string
- `ALLOWED_HOSTS` - Your domain name
- `DB_PASSWORD` - Secure database password
- `EMAIL_*` - Production SMTP settings
- `SITE_URL` - Your production URL

### 2. SSL Certificates

Place SSL certificates in `ssl/` directory:
```
ssl/
├── cert.pem
└── key.pem
```

Update domain in `nginx.prod.conf`:
```nginx
server_name yourdomain.com www.yourdomain.com;
```

### 3. Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

Or manually:
```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Create Superuser

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 5. Verify Deployment

- Check application: https://yourdomain.com
- Check admin: https://yourdomain.com/admin/
- Check logs: `docker-compose -f docker-compose.prod.yml logs -f`

## Database Backup & Restore

### Backup

```bash
docker-compose exec db pg_dump -U clm_user legal_clm_db > backup.sql
```

### Restore

```bash
docker-compose exec -T db psql -U clm_user legal_clm_db < backup.sql
```

### Automated Backups

Add to crontab:
```cron
0 2 * * * cd /path/to/project && docker-compose exec -T db pg_dump -U clm_user legal_clm_db > backups/backup_$(date +\%Y\%m\%d).sql
```

## Monitoring & Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

### Service Status

```bash
docker-compose ps
```

### Django Shell

```bash
docker-compose exec web python manage.py shell
```

### Database Access

```bash
docker-compose exec db psql -U clm_user legal_clm_db
```

## Troubleshooting

### Issue: Container won't start

**Solution:**
```bash
docker-compose down -v
docker-compose up --build
```

### Issue: Database connection errors

**Solution:**
1. Check database is running: `docker-compose ps db`
2. Check logs: `docker-compose logs db`
3. Verify credentials in `.env`

### Issue: Static files not loading

**Solution:**
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Issue: Celery tasks not running

**Solution:**
1. Check Celery worker: `docker-compose logs celery_worker`
2. Check Redis: `docker-compose logs redis`
3. Restart services:
```bash
docker-compose restart celery_worker celery_beat
```

### Issue: Emails not sending

**Solution:**
1. Check EMAIL_BACKEND in `.env`
2. For console backend, check Django logs
3. For SMTP, verify credentials and network access

## Security Considerations

### Production Checklist

- [ ] Change SECRET_KEY to random string
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use strong database passwords
- [ ] Enable SSL/HTTPS
- [ ] Configure proper SMTP with authentication
- [ ] Set up firewall rules
- [ ] Regular backups enabled
- [ ] Monitor logs for suspicious activity
- [ ] Keep dependencies updated

### Default Security Features

- CSRF protection enabled
- SQL injection protection (Django ORM)
- XSS protection headers
- Secure session cookies (production)
- Password hashing (PBKDF2)
- Role-based access control

## Performance Optimization

### Database

- Indexes on frequently queried fields
- Database connection pooling
- Optimized queries with select_related/prefetch_related

### Caching

- Redis for Celery task results
- Static files cached by Nginx (30 days)
- Media files cached by Nginx (7 days)

### Web Server

- Gzip compression enabled
- Multiple Gunicorn workers
- Nginx reverse proxy
- Rate limiting configured

## Development

### Running Tests

```bash
docker-compose exec web python manage.py test
```

### Creating Migrations

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Adding Dependencies

1. Add to `requirements.txt`
2. Rebuild containers:
```bash
docker-compose up --build
```

## Support & Contact

For issues, questions, or contributions:
- Check documentation
- Review logs
- Test in development environment first

## License

This project is proprietary software. All rights reserved.

## Version History

- **v1.0.0** (2026-01-27) - Initial production release
  - Complete contract lifecycle management
  - Digital signatures
  - Email notifications
  - Automated expiry checking
  - Auto-renewal
  - Comprehensive audit trail
  - Docker deployment
  - Production-ready configuration
