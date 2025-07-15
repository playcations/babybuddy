#!/bin/sh

# Exit on any error
set -e

echo "Starting Baby Buddy container..."

# Handle PUID/PGID for LinuxServer compatibility
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Update user/group IDs if they differ from defaults
if [ "$PUID" != "1000" ] || [ "$PGID" != "1000" ]; then
    echo "Setting user babybuddy to UID:$PUID and GID:$PGID"
    deluser babybuddy 2>/dev/null || true
    delgroup babybuddy 2>/dev/null || true
    addgroup -g "$PGID" -S babybuddy
    adduser -u "$PUID" -S babybuddy -G babybuddy
fi

# Generate secret key if not provided
if [ -z "$SECRET_KEY" ]; then
    echo "Generating SECRET_KEY..."
    export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
fi

# Wait for database to be ready (if using external database)
if [ -n "$DATABASE_URL" ] || [ -n "$DB_HOST" ]; then
    echo "Waiting for database to be ready..."
    python manage.py wait_for_db --timeout 30 || true
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create default admin user (LinuxServer compatibility)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating custom superuser..."
    python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" || echo "Superuser already exists"
else
    echo "Creating default admin user (admin/admin)..."
    python manage.py createsuperuser --noinput --username "admin" --password "admin" --email "admin@example.com" || echo "Default admin user already exists"
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Set proper permissions for config directory
chown -R babybuddy:babybuddy /config /app

echo "Starting services..."

# Start nginx in background
nginx -g 'daemon off;' &

# Wait a moment for nginx to start
sleep 2

# Start gunicorn as babybuddy user with proper environment
exec su-exec babybuddy sh -c "cd /app && DJANGO_SETTINGS_MODULE=babybuddy.settings.docker gunicorn --bind 127.0.0.1:8001 --workers 2 --timeout 60 --log-level info --access-logfile - --error-logfile - babybuddy.wsgi:application"