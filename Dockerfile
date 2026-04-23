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

# Dummy values for collectstatic (will be overridden at runtime)
ENV DJANGO_SECRET_KEY=dummy-build-time-secret \
    BACKEND_DB_URL=postgresql://user:pass@localhost/db

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

# Create a non-root user for running the application
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Create logs directory
RUN mkdir -p /app/logs && \
    chown appuser:appuser /app/logs

# Create SFTP cache directory
RUN mkdir -p /app/.sftp_cache && \
    chown appuser:appuser /app/.sftp_cache

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Copy entrypoint and healthcheck scripts
COPY docker/entrypoint.sh /app/docker/entrypoint.sh
COPY docker/healthcheck.py /app/docker/healthcheck.py

# Make scripts executable
RUN chmod +x /app/docker/entrypoint.sh /app/docker/healthcheck.py

# Collect static files (as root before switching to appuser)
RUN /app/.venv/bin/python manage.py collectstatic --noinput --clear

# Switch to non-root user
USER appuser

# Expose the HTTP port (nginx listens on 8080)
EXPOSE 8080

# Health check (checks both nginx and Django)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD /app/docker/healthcheck.py

# Use entrypoint script to manage both nginx and gunicorn
CMD ["/app/docker/entrypoint.sh"]
