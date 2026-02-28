# Justfile - Development commands only
# Run with: just <command>

set dotenv-load

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
    uv run manage.py makemigrations {{ APP }}

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
lint-fix:
    uv run ruff check --fix .

# Format code with ruff
format:
    uv run ruff format .

# Run all checks (lint + typecheck)
check: lint typecheck

# Django shell
shell:
    uv run manage.py shell

# Test runner (if tests exist)
test:
    uv run manage.py test

# Check Django system status
check-system:
    uv run manage.py check
