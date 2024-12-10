#!/bin/bash

# Debug: Print current directory and contents
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn app.wsgi:application --bind 0.0.0.0:${PORT} 