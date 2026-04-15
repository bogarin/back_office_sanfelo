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

# Dummy values for collectstatic (will be overridden at runtime)
ENV DJANGO_SECRET_KEY=dummy-build-time-secret \
    BACKEND_DB_URL=postgresql://user:pass@localhost/db

# Set working directory
WORKDIR /app

# Install runtime dependencies for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
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

# Collect static files (as root before switching to appuser)
RUN /app/.venv/bin/python manage.py collectstatic --noinput --clear

# Switch to non-root user
USER appuser

# Expose the HTTP port (8090 by default, but configurable via HTTP_PORT env var)
EXPOSE ${HTTP_PORT}

# Use uv to run gunicorn with the specified HTTP_PORT
# gunicorn will bind to 0.0.0.0:8080
# We use --bind flag to specify the port dynamically
CMD /app/.venv/bin/gunicorn \
     --bind 0.0.0.0:8080 \
     --workers 4 \
     --threads 2 \
     --timeout 120 \
     --access-logfile - \
     --error-logfile - \
     sanfelipe.wsgi:application
