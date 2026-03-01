#!/bin/bash

# Production Deployment Script for Legal CLM
# This script automates the deployment process

set -e

echo "=========================================="
echo "Legal CLM - Production Deployment"
echo "=========================================="

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "ERROR: .env.prod file not found!"
    echo "Please copy .env.prod.example to .env.prod and configure it."
    exit 1
fi

# Backup database
echo "Creating database backup..."
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Pull latest changes (if using git)
if [ -d .git ]; then
    echo "Pulling latest changes from git..."
    git pull
fi

# Build and start containers
echo "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo "Starting containers..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Wait for database
echo "Waiting for database to be ready..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Create superuser if needed
echo "Checking for superuser..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print("No superuser found. Please create one manually:")
    print("docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser")
END

echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  Restart: docker-compose -f docker-compose.prod.yml restart"
echo ""
