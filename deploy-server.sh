#!/bin/bash

# Deployment script for server 10.231.7.8
# Run this on the production server after SSH in

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Legal CLM - Production Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# Find the app directory
APP_DIR=$(find ~ -name docker-compose.prod.yml 2>/dev/null | head -1 | xargs dirname)

if [ -z "$APP_DIR" ]; then
    echo "ERROR: Could not find app directory with docker-compose.prod.yml"
    echo "Please manually specify the path:"
    exit 1
fi

echo -e "${GREEN}Found app directory: $APP_DIR${NC}"
cd "$APP_DIR" || exit 1

# Pull latest changes
echo -e "${BLUE}Pulling latest changes from GitHub...${NC}"
git pull origin main || exit 1

# Run migrations
echo -e "${BLUE}Running database migrations...${NC}"
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput || exit 1

# Collect static files
echo -e "${BLUE}Collecting static files...${NC}"
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput || exit 1

# Restart web container
echo -e "${BLUE}Restarting web container...${NC}"
docker compose -f docker-compose.prod.yml restart web || exit 1

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Check status at: http://10.231.7.8/admin/"
echo "View logs: docker compose -f docker-compose.prod.yml logs -f"
