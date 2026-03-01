# LCMS Staging Environment Deployment Guide

## Overview

The **staging environment** is a complete replica of production for safe testing:
- ✅ Isolated database (separate from production)
- ✅ Isolated containers (separate from production)
- ✅ Same infrastructure as production
- ✅ Easy rollback if issues occur

## Architecture

\\\
User Request to staging.clm.perfectcompanion.co.id
    ↓
System Nginx (port 443, SSL)
    ↓
localhost:8002 (Staging Nginx Container)
    ↓
Staging Django + Celery + PostgreSQL + Redis
\\\

## Deployment Steps

### 1. Build Staging Containers

\\\ash
cd /home/bitpedia/clm
docker-compose -f docker-compose.staging.yml build --no-cache
\\\

### 2. Start Staging Services

\\\ash
docker-compose -f docker-compose.staging.yml up -d
\\\

### 3. Run Migrations (First Time Only)

\\\ash
docker-compose -f docker-compose.staging.yml exec -T web-staging python manage.py migrate --no-input
\\\

### 4. Collect Static Files

\\\ash
docker-compose -f docker-compose.staging.yml exec -T web-staging python manage.py collectstatic --no-input
\\\

### 5. Reload Nginx (System)

\\\ash
sudo systemctl reload nginx
\\\

### 6. Verify Services

\\\ash
docker-compose -f docker-compose.staging.yml ps

# Should see:
# clm-db-staging          postgresql healthy
# clm-redis-staging       redis healthy
# clm-app-staging         gunicorn running
# clm-celery-worker-staging  celery worker running
# clm-celery-beat-staging    celery beat running
# clm-nginx-staging       nginx running (port 8002)
\\\

## Testing Workflow

### Test a Feature on Staging

1. **Check out staging branch**
   \\\ash
   git checkout staging
   git pull origin staging
   \\\

2. **Merge feature into staging**
   \\\ash
   git merge feature/my-feature
   git push origin staging
   \\\

3. **Pull latest code to server**
   \\\ash
   cd /home/bitpedia/clm
   git pull origin staging
   \\\

4. **Rebuild containers with new code**
   \\\ash
   docker-compose -f docker-compose.staging.yml down
   docker-compose -f docker-compose.staging.yml build --no-cache
   docker-compose -f docker-compose.staging.yml up -d
   \\\

5. **Run any new migrations**
   \\\ash
   docker-compose -f docker-compose.staging.yml exec -T web-staging python manage.py migrate
   \\\

6. **Test on https://staging.clm.perfectcompanion.co.id**

7. **If OK** → Merge to main and deploy to production
   \\\ash
   git checkout main
   git merge staging
   git push origin main
   \\\

### Revert Staging if Issues

If staging breaks, immediately revert to last known good version:

\\\ash
# Find last good commit
git log --oneline

# Revert to it
git revert <commit-hash>
git push origin staging

# Rebuild staging containers
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml build --no-cache
docker-compose -f docker-compose.staging.yml up -d
\\\

## Quick Commands

### View Staging Logs
\\\ash
docker-compose -f docker-compose.staging.yml logs -f web-staging
docker-compose -f docker-compose.staging.yml logs -f db-staging
docker-compose -f docker-compose.staging.yml logs -f celery-worker-staging
\\\

### SSH into Staging Django Container
\\\ash
docker-compose -f docker-compose.staging.yml exec web-staging bash
\\\

### Create Staging Django Superuser
\\\ash
docker-compose -f docker-compose.staging.yml exec -T web-staging python manage.py createsuperuser
\\\

### Backup Staging Database
\\\ash
docker-compose -f docker-compose.staging.yml exec db-staging pg_dump -U clm_user_staging legal_clm_db_staging > staging_backup_\.sql
\\\

### Restore from Production to Staging (For Testing)

\\\ash
# 1. Backup production database
cd /home/bitpedia/clm
docker-compose exec db pg_dump -U clm_user legal_clm_db > prod_backup.sql

# 2. Restore to staging database
docker-compose -f docker-compose.staging.yml exec db-staging psql -U clm_user_staging legal_clm_db_staging < prod_backup.sql
\\\

## Environment Variables

Staging uses **.env.staging** with:
- Database: \legal_clm_db_staging\ (separate from production)
- User: \clm_user_staging\
- Password: \ClmStaging2026Pass!\ (staging-only)
- Redis: \edis-staging\
- Domain: \staging.clm.perfectcompanion.co.id\
- SSL: Auto-configured by Let's Encrypt

## Monitoring

### Check Container Health
\\\ash
docker-compose -f docker-compose.staging.yml ps
\\\

### View System Resources
\\\ash
docker stats clm-app-staging clm-db-staging clm-redis-staging
\\\

### Test HTTP Response
\\\ash
curl -I https://staging.clm.perfectcompanion.co.id/
\\\

## Troubleshooting

### Port 8002 Already in Use
\\\ash
# Find process using port 8002
lsof -i :8002

# Kill it if needed
kill -9 <PID>
\\\

### Database Connection Error
\\\ash
# Check if staging database is healthy
docker-compose -f docker-compose.staging.yml ps db-staging

# Check database logs
docker-compose -f docker-compose.staging.yml logs db-staging
\\\

### Static Files Not Loading
\\\ash
# Recollect static files
docker-compose -f docker-compose.staging.yml exec -T web-staging python manage.py collectstatic --clear --no-input
\\\

## Key Differences: Staging vs Production

| Aspect | Staging | Production |
|--------|---------|------------|
| Database | \legal_clm_db_staging\ | \legal_clm_db\ |
| User | \clm_user_staging\ | \clm_user\ |
| Password | \ClmStaging2026Pass!\ | \ClmSecure2026Pass!\ |
| Docker Compose File | \docker-compose.staging.yml\ | \docker-compose.yml\ |
| Environment File | \.env.staging\ | \.env.prod\ |
| Domain | \staging.clm.perfectcompanion.co.id\ | \clm.perfectcompanion.co.id\ |
| Container Port | 8002 | 8001 |
| Data | Test/temporary | Real/critical |

## Development → Staging → Production Pipeline

\\\
┌─────────────────────────────────────────────────────────┐
│                   FEATURE DEVELOPMENT                     │
│  Developer creates feature/my-feature from dev branch     │
└──────────────────────┬──────────────────────────────────┘
                       ↓
            ┌──────────────────────┐
            │  Merge to dev branch  │
            │ (local testing)       │
            └──────────┬───────────┘
                       ↓
           ┌───────────────────────┐
           │ Merge to staging      │
           │ (module testing)      │
           │ Deploy to staging env │
           │ Test in staging       │
           └──────────┬────────────┘
                      ↓
                   APPROVED?
                      ↓
        ┌─────────────────────────┐
        │  Merge to main          │
        │  (production release)   │
        │  Deploy to production   │
        └─────────────────────────┘
\\\

## Safety Benefits

✅ **Isolation**: Staging database completely separate from production
✅ **Testing**: Full feature testing in production-like environment
✅ **Rollback**: Easy revert to known good version if issues occur
✅ **Confidence**: Test all modules before impacting live system
✅ **Learning**: Safe space for experimenting with AI-generated code

