# Justfile - Development commands only
# Run with: just <command>

set dotenv-load
SHORT_SHA := `git rev-parse --short HEAD`

[private]
default:
    @just --list

alias install := setup
# Setup development environment
[group('Development')]
setup:
    uv sync
    uv run prek install --install-hooks --hook-type pre-commit --hook-type pre-push
    uv run prek update

# Launch django development server
[group('Development')]
run:
    uv run manage.py runserver

# Create/update database migrations
[group('Development')]
migrate:
    uv run manage.py migrate

# Setup roles (create Administrador and Operador groups)
[group('Development')]
setup_roles:
    uv run manage.py setup_roles

# Run every prek hook across the whole repo (manual safety net / CI parity).
[group('Quality')]
pre-commit:
    uv run prek run --all-files --show-diff-on-failure

# Run linter (readonly)
[group('Quality')]
lint *ARGS:
    uv run ruff check {{ARGS}}

# Linter autofix + format.
[group('Quality')]
format *ARGS:
    uv run ruff check --fix {{ARGS}}
    uv run ruff format {{ARGS}}

# Type checker.
[group('Quality')]
typecheck *ARGS:
    uv run ty check {{ARGS}}

# Django template formatter.
[group('Quality')]
djlint *ARGS = '.':
    uv run djangofmt {{ARGS}}

# Run test suite
[group('Quality')]
test *ARGS:
    uv run pytest {{ ARGS }}

# AST audit of the test suite (skill rules: no class-based tests).
[group('Quality')]
audit-tests:
    uv run python apps/core/scripts/check_tests.py

# Test nginx configuration
[group('Deployment')]
check-nginx:
    nginx -t -c {{justfile_directory()}}/nginx/nginx.conf


# Build docker container
[group('Deployment')]
container-build:
    @echo "\033[36m▶ Building Docker image...\033[0m"
    docker build -t sanfelipe-backoffice:dev-{{SHORT_SHA}} .
    docker tag sanfelipe-backoffice:dev-{{SHORT_SHA}} sanfelipe-backoffice:latest
    mkdir -p .docker-images
    rm -f .docker-images/sanfelipe-backoffice-dev-{{SHORT_SHA}}.*
    docker save -o .docker-images/sanfelipe-backoffice-dev-{{SHORT_SHA}}.raw "sanfelipe-backoffice:dev-{{SHORT_SHA}}"
    zstd -19 -o .docker-images/sanfelipe-backoffice-dev-{{SHORT_SHA}}.tar.zst .docker-images/sanfelipe-backoffice-dev-{{SHORT_SHA}}.raw

# Push latest docker container to staging
[group('Deployment')]
container-push:
    @echo "\033[36m▶ Pushing Docker image to sanfelo.stage \033[0m"
    scp .docker-images/sanfelipe-backoffice-dev-{{SHORT_SHA}}.tar.zst sanfelo.stage:/tmp/
    ssh sanfelo.stage "\
      zstd -d -c /tmp/sanfelipe-backoffice-dev-{{SHORT_SHA}}.tar.zst | docker load && \
      docker tag localhost/sanfelipe-backoffice:dev-{{SHORT_SHA}} sanfelipe-backoffice:dev-{{SHORT_SHA}} && \
      docker tag sanfelipe-backoffice:dev-{{SHORT_SHA}} sanfelipe-backoffice:latest && \
      docker rmi localhost/sanfelipe-backoffice:dev-{{SHORT_SHA}} && \
      rm -f /tmp/sanfelipe-backoffice-dev-{{SHORT_SHA}}.tar.zst"

# Run the container image locally
[group('Deployment')]
container-run:
    @docker rm -f backoffice 2>/dev/null || true
    podman run --name backoffice \
    -p 8090:8080 \
    --env-file .env \
    sanfelipe-backoffice:latest

[group('Deployment')]
[arg('bump', pattern='patch|minor|major|none')]
deploy bump='patch':
    #!/bin/bash
    set -e
    if [ -n "$(git status --porcelain)" ]; then
        echo "Error: working tree not clean. Commit or stash first." >&2
        exit 1
    fi
    if [ "{{ bump }}" != "none" ]; then
        uv version --bump {{ bump }}
        VERSION=$(uv version --short)
        git add pyproject.toml uv.lock
        git commit -m "release: v${VERSION}"
        git tag "v${VERSION}"
        git push --follow-tags
        echo "Released v${VERSION}"
    fi
    just container-build
    just container-push
    echo "TODO: tag new image"
