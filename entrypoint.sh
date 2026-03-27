#!/bin/bash

set -e

CMD="$*"

echo "Waiting for PostgreSQL..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL started"

# Only run heavy setup on web/gunicorn container.
if [[ "$CMD" == *"gunicorn"* ]]; then
  # Run migrations
  python manage.py makemigrations --noinput
  python manage.py migrate --noinput

  # Collect static files (quiet mode to avoid noisy duplicate-path messages)
  python manage.py collectstatic --noinput --verbosity 0

  # Create superuser if it doesn't exist
  python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
END
fi

exec "$@"
