# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=app.settings \
    PORT=8008

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files from SingleCourseWebApp
COPY SingleCourseWebApp/ /app/

# Verify the files are copied
RUN ls -la /app && \
    ls -la /app/app && \
    ls -la /app/course

# Create and set permissions for entrypoint script
COPY docker-entrypoint.sh /app
RUN chmod +x /app/docker-entrypoint.sh

# Create a non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8008


ENTRYPOINT ["/app/docker-entrypoint.sh"] 