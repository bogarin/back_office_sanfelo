# Scripts Directory

This directory contains utility scripts for managing the Docker deployment.

## Available Scripts

### configure-keycloak.sh

Automated script to configure Keycloak for the backoffice application.

**Features:**
- Creates a realm for the backoffice application
- Creates an OpenID Connect client
- Creates default roles (admin, operator, viewer)
- Optionally creates demo users with assigned roles
- Automatically saves the client secret to `.env` file

**Requirements:**
- `jq` - Command-line JSON processor
- `curl` - For making HTTP requests to Keycloak API

**Installation of jq:**

```bash
# Debian/Ubuntu
apt-get update && apt-get install -y jq

# macOS
brew install jq

# Fedora/RHEL
dnf install jq
```

**Usage:**

```bash
# Basic usage (uses default values from .env or defaults)
./scripts/configure-keycloak.sh

# With custom values
KEYCLOAK_URL=http://localhost:8080 \
KEYCLOAK_ADMIN=admin \
KEYCLOAK_ADMIN_PASSWORD=admin123 \
./scripts/configure-keycloak.sh

# Create demo users
CREATE_DEMO_USERS=true ./scripts/configure-keycloak.sh
```

**Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `KEYCLOAK_URL` | Keycloak server URL | `http://localhost:8080` |
| `KEYCLOAK_ADMIN` | Keycloak admin username | `admin` |
| `KEYCLOAK_ADMIN_PASSWORD` | Keycloak admin password | `admin123` |
| `KEYCLOAK_REALM` | Realm name to create | `backoffice` |
| `KEYCLOAK_CLIENT_ID` | Client ID to create | `backoffice-client` |
| `BACKOFFICE_URL` | Backoffice application URL | `http://localhost:8090` |
| `CREATE_DEMO_USERS` | Create demo users | `false` |

**Demo Users (if CREATE_DEMO_USERS=true):**

| Username | Email | Password | Roles |
|----------|-------|----------|-------|
| admin | admin@backoffice.local | admin123 | admin |
| operator | operator@backoffice.local | operator123 | operator |
| viewer | viewer@backoffice.local | viewer123 | viewer |

**What the script does:**

1. **Waits for Keycloak** to be healthy and ready
2. **Gets admin token** using the admin credentials
3. **Creates a realm** named according to `KEYCLOAK_REALM`
4. **Creates an OIDC client** with the ID `KEYCLOAK_CLIENT_ID`
5. **Creates roles**: admin, operator, viewer
6. **Gets the client secret** and saves it to `.env` file
7. **Optionally creates demo users** with assigned roles

**Output Example:**

```
[INFO] Starting Keycloak configuration...
[INFO] Keycloak URL: http://localhost:8080
[INFO] Waiting for Keycloak to be ready...
[INFO] Keycloak is ready!
[INFO] Getting admin token...
[INFO] Admin token obtained successfully
[INFO] Creating realm: backoffice
[INFO] Realm 'backoffice' created successfully
[INFO] Creating client: backoffice-client
[INFO] Client 'backoffice-client' created successfully
[INFO] Client Secret: abc123def456ghi789...
[INFO] Client secret saved to .env file
[INFO] Creating roles...
[INFO] Role 'admin' created successfully
[INFO] Role 'operator' created successfully
[INFO] Role 'viewer' created successfully
[INFO] Creating demo users...
[INFO] Creating user: admin
[INFO] Role 'admin' assigned to admin
[INFO] User 'admin' created successfully
[INFO] Keycloak configuration completed successfully!
===========================================
Keycloak Admin Console: http://localhost:8080/admin
Username: admin
Password: admin123
Realm: backoffice
Client ID: backoffice-client
===========================================
```

**Integration with Docker Compose:**

You can run this script after starting the services:

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready
sleep 30

# Configure Keycloak
./scripts/configure-keycloak.sh

# Or create demo users
CREATE_DEMO_USERS=true ./scripts/configure-keycloak.sh

# Run migrations
docker-compose exec backoffice python manage.py migrate
```

**Troubleshooting:**

**Script fails with "jq is not installed":**
```bash
# Install jq
sudo apt-get install jq  # Debian/Ubuntu
# or
brew install jq  # macOS
```

**Script fails with "Keycloak did not become ready in time":**
```bash
# Check Keycloak logs
docker-compose logs keycloak

# Verify Keycloak is running
curl http://localhost:8080/health/ready
```

**Script fails with "Failed to get admin token":**
```bash
# Verify admin credentials
docker-compose exec keycloak env | grep KEYCLOAK_ADMIN

# Check .env file values
cat .env | grep KEYCLOAK_ADMIN
```

**Manual Configuration:**

If the script fails, you can configure Keycloak manually:

1. Go to `http://localhost:8080/admin`
2. Login with admin credentials
3. Create a new realm
4. Create a new OpenID Connect client
5. Get the client secret and add it to `.env`

**Best Practices:**

1. **Never commit** the `.env` file with real secrets
2. **Change default passwords** in production
3. **Use HTTPS** for production deployments
4. **Review and customize** roles according to your application needs
5. **Backup your realm** configuration regularly
6. **Test the configuration** before deploying to production

**Advanced Usage:**

**Custom realm configuration:**

You can modify the script to customize the realm creation parameters:

```bash
# Edit the create_realm function in the script
# Add additional parameters like:
# - password policies
# - user federation
# - themes
# - email settings
```

**Custom client configuration:**

You can modify the client creation to add more features:

```bash
# Edit the create_client function in the script
# Add additional parameters like:
# - specific scopes
# - advanced consent settings
# - service account roles
# - protocol mappers
```

**Integration with CI/CD:**

You can integrate this script into your CI/CD pipeline:

```yaml
# Example GitLab CI
configure-keycloak:
  stage: deploy
  script:
    - docker-compose up -d
    - ./scripts/configure-keycloak.sh
    - docker-compose exec backoffice python manage.py migrate
  only:
    - main
```

**Related Documentation:**

- [Keycloak Administration Guide](https://www.keycloak.org/docs/latest/server_admin/)
- [Keycloak REST API](https://www.keycloak.org/docs/latest/server_admin/#_rest_api)
- [OpenID Connect with Keycloak](https://www.keycloak.org/docs/latest/securing_apps/)
