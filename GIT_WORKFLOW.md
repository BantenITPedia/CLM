# LCMS Git Workflow

## Branch Structure

Three branches for safe, controlled deployments:

### 1. **main** (Production)
- **Purpose:** Live code only
- **Status:** Stable, tested
- **Deploy:** Automatic to live server (103.129.149.2)
- **Protection:** Requires pull request review before merging
- **Access:** Limited to senior developers/DevOps
- **Docker Compose:** docker-compose.yml (production settings)

### 2. **staging** (Testing/QA)
- **Purpose:** Test new features before production
- **Status:** Pre-production environment
- **Deploy:** Manual to staging server (or test container)
- **Testing:** Module testing, feature validation, UAT
- **Docker Compose:** docker-compose.prod.yml (production-like)
- **Merge From:** Feature branches merged to staging first
- **Merge To:** main (after approval)

### 3. **dev** (Development)
- **Purpose:** Active development
- **Status:** Unstable, constantly changing
- **Deploy:** Local developer machines only
- **Testing:** Unit tests, integration tests
- **Docker Compose:** docker-compose.yml (dev settings)
- **Merge From:** Feature branches (eature/*)
- **Merge To:** staging (when stable)

## Workflow

`
Feature Development
        ↓
   feature/my-feature
        ↓
    Merge to dev
        ↓
   Testing & QA
        ↓
    Merge to staging
        ↓
  Module Testing
        ↓
   Merge to main
        ↓
Deploy to Production
`

## Commands

### Create Feature Branch
`ash
git checkout dev
git pull origin dev
git checkout -b feature/my-feature-name
`

### Push Feature Branch
`ash
git add .
git commit -m  Describe your changes
git push origin feature/my-feature-name
`

### Merge to Staging (After Dev Testing)
`ash
git checkout staging
git pull origin staging
git merge feature/my-feature-name
git push origin staging
`

### Merge to Main (Production Release)
`ash
git checkout main
git pull origin main
git merge staging
git push origin main
# Tag the release
git tag -a v1.0.0 -m Release version 1.0.0
git push origin main --tags
`

## Deployment

### Development (Local)
`ash
git checkout dev
docker-compose up -d
`

### Staging (Test Server)
`ash
git checkout staging
docker-compose -f docker-compose.prod.yml up -d
`

### Production (Live Server)
`ash
git checkout main
docker-compose up -d
# Restart services
docker-compose restart web celery_worker celery_beat
`

## Branch Naming Conventions

- **Features:** eature/add-payment-module
- **Bug Fixes:** ugfix/fix-email-notification
- **Hotfixes:** hotfix/critical-security-patch
- **Documentation:** docs/update-readme

## Environment Files

⚠️ **DO NOT COMMIT THESE** (in .gitignore):
- .env - Development environment variables
- .env.prod - Production environment variables
- .env.local - Local overrides

Use environment examples instead:
- .env.example - Template with dummy values
- Docs show how to fill them in

## Protection Rules (Recommended on GitHub/GitLab)

### main branch:
- ✅ Require pull request reviews
- ✅ Dismiss stale PR approvals
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Restrict who can push

### staging branch:
- ✅ Require pull request reviews
- ✅ Require status checks to pass

### dev branch:
- No restrictions (fast-moving development)

## Common Scenarios

### Testing New Feature
`ash
# Developer
git checkout -b feature/send-email-reminders dev
# ... make changes ...
git push origin feature/send-email-reminders

# Create Pull Request: dev ← feature/send-email-reminders
# After testing locally, merge to dev

# QA Lead
git checkout staging
git merge feature/send-email-reminders
git push origin staging
# Test in staging environment

# DevOps
git checkout main
git merge staging
git push origin main
# Deploy to production
`

### Fix Bug in Production
`ash
# Create hotfix from main
git checkout -b hotfix/login-bug main
# ... fix the bug ...
git push origin hotfix/login-bug

# Merge to main (production)
git checkout main
git merge hotfix/login-bug
git push origin main

# Merge back to staging and dev
git checkout staging
git merge hotfix/login-bug
git push origin staging

git checkout dev
git merge hotfix/login-bug
git push origin dev
`

## Status Check

`ash
# Current branch status
git status

# View all branches
git branch -a

# View commit history
git log --oneline -n 10

# View branches and their commits
git log --graph --oneline --all
`
