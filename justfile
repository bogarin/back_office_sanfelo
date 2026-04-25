# Justfile - Development commands only
# Run with: just <command>

set dotenv-load
SHORT_SHA := `git rev-parse --short HEAD`

default:
    @just --list

install:
    uv sync

# Development server
run:
    uv run manage.py runserver

# Create/update database migrations
migrate:
    uv run manage.py migrate

# Show migration status
migrate-status:
    uv run manage.py showmigrations

# Create a new migration (after model changes)
makemigrations APP:
    uv run manage.py makemigrations --database=default {{ APP }}

# Create superuser for admin
createsuperuser:
    uv run manage.py createsuperuser

# Setup roles (create Administrador and Operador groups)
setup_roles:
    uv run manage.py setup_roles

# Validate schema against external PostgreSQL database
validate-schema:
    uv run manage.py validate_schema

# Type checking with pyright
typecheck:
    uv run pyright

# Linting with ruff
lint:
    uv run ruff check .

# Fix auto-fixable linting issues
lint-fix *ARGS:
    uv run ruff check --fix {{ if ARGS == "" { "." } else { ARGS } }}

# Format code with ruff
format *ARGS:
    uv run ruff format {{ if ARGS == "" { "." } else { ARGS } }}

# Run all checks (lint + typecheck)
check: lint typecheck

# Django shell
shell:
    uv run manage.py shell

# Test runner with pytest
test *ARGS:
    TESTING=1 uv run pytest {{ARGS}}

# Run tests for a specific app
test-app APP:
    TESTING=1 uv run pytest tests/{{APP}}/

# Run tests with coverage
test-cov *ARGS:
    TESTING=1 uv run pytest --cov=. --cov-report=html --cov-report=term {{ARGS}}

# Run tests skipping slow tests
test-fast *ARGS:
    TESTING=1 uv run pytest -m 'not slow' {{ARGS}}

# Run tests re-creating database
test-create-db *ARGS:
    TESTING=1 uv run pytest --create-db {{ARGS}}

# Check Django system status
check-system:
    uv run manage.py check

# Build docker container
container-build:
    @echo "\033[36m▶ Building Docker image...\033[0m"
    podman build -t sanfelipe-backoffice:{{SHORT_SHA}}-dev .
    podman tag sanfelipe-backoffice:{{SHORT_SHA}}-dev sanfelipe-backoffice:latest
    mkdir -p .docker-images
    rm -f .docker-images/sanfelipe-backoffice-{{SHORT_SHA}}-dev.*
    podman save -o .docker-images/sanfelipe-backoffice-{{SHORT_SHA}}-dev.raw "sanfelipe-backoffice:{{SHORT_SHA}}-dev"
    zstd -19 -o .docker-images/sanfelipe-backoffice-{{SHORT_SHA}}-dev.tar.zst .docker-images/sanfelipe-backoffice-{{SHORT_SHA}}-dev.raw

container-push:
    @echo "\033[36m▶ Pushing Docker image to sanfelo.stage \033[0m"
    scp .docker-images/sanfelipe-backoffice-{{SHORT_SHA}}-dev.tar.zst sanfelo.stage:/tmp/
    ssh sanfelo.stage "\
      zstd -d -c /tmp/sanfelipe-backoffice-{{SHORT_SHA}}-dev.tar.zst | docker load && \
      docker tag localhost/sanfelipe-backoffice:{{SHORT_SHA}}-dev sanfelipe-backoffice:{{SHORT_SHA}}-dev && \
      docker tag sanfelipe-backoffice:{{SHORT_SHA}}-dev sanfelipe-backoffice:latest && \
      docker rmi localhost/sanfelipe-backoffice:{{SHORT_SHA}}-dev && \
      rm -f /tmp/sanfelipe-backoffice-{{SHORT_SHA}}-dev.tar.zst"

container-run:
    @podman rm -f backoffice 2>/dev/null || true
    podman run --name backoffice \
    -p 8090:8080 \
    --env-file .env \
    sanfelipe-backoffice:latest
