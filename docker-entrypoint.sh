#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Apply database migrations
echo "Applying database migrations..."
python /app/manage.py migrate

# Collect static files
echo "Collecting static files..."
python /app/manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn --bind 0.0.0.0:8008 app.wsgi:application