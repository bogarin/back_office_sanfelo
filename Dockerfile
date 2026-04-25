# Multi-stage Dockerfile for Django application using uv

# Stage 0: Obtener el binario uv
FROM ghcr.io/astral-sh/uv:latest AS uv

# Stage 1: Builder
FROM python:3.14 AS builder

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY uv.lock pyproject.toml ./

RUN uv sync --no-dev --frozen

# Stage 2: Runtime
FROM python:3.14-slim-trixie

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HTTP_PORT=8080 \
    DJANGO_SETTINGS_MODULE=sanfelipe.settings \
    GUNICORN_PORT=8081 \
    GUNICORN_WORKERS=4 \
    GUNICORN_TIMEOUT=60 \
    DJANGO_DEBUG=False \
    DJANGO_SECRET_KEY=abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ \
    DJANGO_ALLOWED_HOSTS=localhost \
    POSTGRESQL_DB_URL=postgresql://user:pass@localhost/db \
    BACKOFFICE_DB_SCHEMA=backoffice \
    BACKEND_DB_SCHEMA=public \
    SFTP_CACHE_DIR=/app/.sftp_cache

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 nginx && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs /app/.sftp_cache /app/staticfiles /app/media && \
    mkdir -p /tmp/nginx_client_body /tmp/nginx_proxy /tmp/nginx_fastcgi \
    /tmp/nginx_uwsgi /tmp/nginx_scgi /var/log/nginx && \
    chown -R appuser:appuser /app/logs /app/.sftp_cache /app/staticfiles /app/media && \
    chown -R www-data:www-data /var/log/nginx

COPY --from=builder /app/.venv /app/.venv

COPY nginx/nginx.conf /etc/nginx/nginx.conf

COPY . .

RUN chmod +x /app/docker/entrypoint.sh /app/docker/healthcheck.py && \
    /app/.venv/bin/python manage.py collectstatic --noinput --clear && \
    chown -R appuser:appuser /app/staticfiles

ENV DJANGO_SECRET_KEY= \
    DJANGO_ALLOWED_HOSTS= \
    POSTGRESQL_DB_URL=

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD /app/docker/healthcheck.py

CMD ["/app/docker/entrypoint.sh"]
