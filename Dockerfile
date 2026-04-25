# Multi-stage Dockerfile for Django application using uv

# Stage 0: Obtener el binario uv
FROM ghcr.io/astral-sh/uv:latest AS uv

# Stage 1: Builder
FROM python:3.14 AS builder

# Copiar binario uv
COPY --from=uv /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update -y
RUN apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy uv lock and pyproject files
COPY uv.lock pyproject.toml ./

# Install dependencies in production mode (without dev dependencies)
RUN uv sync --no-dev --frozen

# Stage 2: Runtime
FROM python:3.14-slim-trixie

# Set Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HTTP_PORT=8080 \
    DJANGO_SETTINGS_MODULE=sanfelipe.settings

# Gunicorn configuration
ENV GUNICORN_PORT=8081 \
    GUNICORN_WORKERS=4 \
    GUNICORN_TIMEOUT=60

# Build-time dummy values for collectstatic (overridden at runtime)
# DEBUG=False + a valid SECRET_KEY avoids debug_toolbar (not installed with --no-dev)
# and passes SECRET_KEY validation.
ENV DJANGO_DEBUG=False \
    DJANGO_SECRET_KEY=abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ \
    DJANGO_ALLOWED_HOSTS=localhost \
    POSTGRESQL_DB_URL=postgresql://user:pass@localhost/db \
    BACKOFFICE_DB_SCHEMA=backoffice \
    BACKEND_DB_SCHEMA=public

# SFTP cache configuration
ENV SFTP_CACHE_DIR=/app/.sftp_cache

# Set working directory
WORKDIR /app

# Install runtime dependencies for PostgreSQL and nginx
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy only the .venv from builder stage to avoid copying build tools
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Create a non-root user for running gunicorn
RUN useradd -m -u 1000 appuser

# Create required directories and set ownership
RUN mkdir -p /app/logs /app/.sftp_cache /app/staticfiles /app/media && \
    chown -R appuser:appuser /app/logs /app/.sftp_cache /app/staticfiles /app/media

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Copy entrypoint and healthcheck scripts
COPY docker/entrypoint.sh /app/docker/entrypoint.sh
COPY docker/healthcheck.py /app/docker/healthcheck.py

# Make scripts executable
RUN chmod +x /app/docker/entrypoint.sh /app/docker/healthcheck.py

# Prepare nginx runtime directories writable by nginx user
RUN mkdir -p /tmp/nginx_client_body /tmp/nginx_proxy /tmp/nginx_fastcgi \
    /tmp/nginx_uwsgi /tmp/nginx_scgi /var/log/nginx && \
    chown -R www-data:www-data /var/log/nginx

# Collect static files (as root, using build-time env vars)
RUN /app/.venv/bin/python manage.py collectstatic --noinput --clear && \
    chown -R appuser:appuser /app/staticfiles

# Clear build-time env vars so they don't leak into runtime
ENV DJANGO_SECRET_KEY= \
    DJANGO_ALLOWED_HOSTS= \
    POSTGRESQL_DB_URL=

# Expose the HTTP port (nginx listens on 8080)
EXPOSE 8080

# Health check (checks both nginx and Django)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD /app/docker/healthcheck.py

# Container runs as root so nginx master can start.
# The entrypoint starts gunicorn as appuser via runuser.
CMD ["/app/docker/entrypoint.sh"]
