#!/bin/bash
#
# Entrypoint script for San Felipe backoffice container.
#
# This script manages both nginx (port 8080) and gunicorn (localhost:8081)
# as a single-container deployment. It:
# 1. Runs as root so nginx master can bind port 8080
# 2. Starts nginx in the background
# 3. Starts gunicorn as appuser (non-root) via runuser
# 4. Handles signals (TERM, INT) to gracefully shutdown both services
# 5. Waits for child processes and reports exit codes

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
GUNICORN_PORT="${GUNICORN_PORT:-8081}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-60}"
GUNICORN_MAX_REQUESTS="${GUNICORN_MAX_REQUESTS:-1000}"
GUNICORN_MAX_REQUESTS_JITTER="${GUNICORN_MAX_REQUESTS_JITTER:-50}"

# Django settings module
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-sanfelipe.settings}"

# PIDs for process management
NGINX_PID=
GUNICORN_PID=

# Trap signals for graceful shutdown
trap 'shutdown' TERM INT

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# =============================================================================
# Django Management
# =============================================================================

collectstatic() {
    log_info "Collecting static files..."
    python manage.py collectstatic --no-input --clear || {
        log_error "Collectstatic failed!"
        exit 1
    }
    log_info "Static files collected successfully."
}

# =============================================================================
# Process Management
# =============================================================================

start_nginx() {
    log_info "Starting nginx (port 8080)..."

    # Test nginx configuration
    nginx -t || {
        log_error "Nginx configuration test failed!"
        exit 1
    }

    # Start nginx in background
    nginx -g 'daemon off;' 2>&1 &
    NGINX_PID=$!

    # Wait a moment for nginx to start
    sleep 1

    # Check if nginx is still running
    if ! kill -0 "$NGINX_PID" 2>/dev/null; then
        log_error "Nginx failed to start (PID: $NGINX_PID)!"
        exit 1
    fi

    log_info "Nginx started successfully (PID: $NGINX_PID)."
}

start_gunicorn() {
    log_info "Starting gunicorn as appuser (port $GUNICORN_PORT, $GUNICORN_WORKERS workers)..."

    # Build gunicorn command
    GUNICORN_CMD="gunicorn sanfelipe.wsgi:application"
    GUNICORN_CMD="$GUNICORN_CMD --bind 127.0.0.1:$GUNICORN_PORT"
    GUNICORN_CMD="$GUNICORN_CMD --workers $GUNICORN_WORKERS"
    GUNICORN_CMD="$GUNICORN_CMD --timeout $GUNICORN_TIMEOUT"
    GUNICORN_CMD="$GUNICORN_CMD --max-requests $GUNICORN_MAX_REQUESTS"
    GUNICORN_CMD="$GUNICORN_CMD --max-requests-jitter $GUNICORN_MAX_REQUESTS_JITTER"
    GUNICORN_CMD="$GUNICORN_CMD --access-logfile -"
    GUNICORN_CMD="$GUNICORN_CMD --error-logfile -"
    GUNICORN_CMD="$GUNICORN_CMD --log-level info"
    GUNICORN_CMD="$GUNICORN_CMD --capture-output"

    # Start gunicorn as appuser (non-root)
    runuser -u appuser -- $GUNICORN_CMD &
    GUNICORN_PID=$!

    # Wait a moment for gunicorn to start
    sleep 2

    # Check if gunicorn is still running
    if ! kill -0 "$GUNICORN_PID" 2>/dev/null; then
        log_error "Gunicorn failed to start (PID: $GUNICORN_PID)!"
        exit 1
    fi

    log_info "Gunicorn started successfully as appuser (PID: $GUNICORN_PID)."
}

shutdown() {
    log_warn "Received shutdown signal. Stopping services..."

    # Stop gunicorn
    if [ -n "$GUNICORN_PID" ]; then
        log_info "Stopping gunicorn (PID: $GUNICORN_PID)..."
        kill -TERM "$GUNICORN_PID" 2>/dev/null || true
        wait "$GUNICORN_PID" 2>/dev/null || true
        log_info "Gunicorn stopped."
    fi

    # Stop nginx
    if [ -n "$NGINX_PID" ]; then
        log_info "Stopping nginx (PID: $NGINX_PID)..."
        kill -TERM "$NGINX_PID" 2>/dev/null || true
        wait "$NGINX_PID" 2>/dev/null || true
        log_info "Nginx stopped."
    fi

    log_info "All services stopped. Exiting."
    exit 0
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    # Activate virtual environment (Django and gunicorn installed here)
    . /app/.venv/bin/activate

    log_info "=========================================="
    log_info "San Felipe Backoffice Container"
    log_info "=========================================="
    log_info "Running as: $(id -un) (uid=$(id -u))"
    log_info "Gunicorn port: $GUNICORN_PORT"
    log_info "Gunicorn workers: $GUNICORN_WORKERS"
    log_info "Gunicorn timeout: ${GUNICORN_TIMEOUT}s"
    log_info "Django settings: $DJANGO_SETTINGS_MODULE"
    log_info "=========================================="

    # Django setup
    collectstatic

    # Fix ownership of runtime-generated files (collectstatic runs as root)
    chown -R appuser:appuser /app/logs /app/staticfiles 2>/dev/null || true

    # Start services
    start_nginx
    start_gunicorn

    log_info "=========================================="
    log_info "All services started successfully!"
    log_info "Nginx: http://0.0.0.0:8080"
    log_info "Django: http://127.0.0.1:$GUNICORN_PORT (internal)"
    log_info "=========================================="

    # Wait for gunicorn process
    # If gunicorn exits, we should exit too
    wait "$GUNICORN_PID"
    GUNICORN_EXIT_CODE=$?

    # If we get here, gunicorn exited unexpectedly
    log_error "Gunicorn exited unexpectedly with code: $GUNICORN_EXIT_CODE"

    # Stop nginx
    if [ -n "$NGINX_PID" ]; then
        log_info "Stopping nginx..."
        kill -TERM "$NGINX_PID" 2>/dev/null || true
        wait "$NGINX_PID" 2>/dev/null || true
    fi

    exit "$GUNICORN_EXIT_CODE"
}

# Run main function
main "$@"
