#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Apply database migrations
echo "Applying database migrations..."
python /app/manage.py migrate

# Collect static files (if not done in Dockerfile)
# echo "Collecting static files..."
# python /app/manage.py collectstatic --noinput

# Start Apache in the foreground
echo "Starting Apache..."
exec apache2ctl -D FOREGROUND 