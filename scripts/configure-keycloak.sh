#!/bin/bash

# Keycloak Configuration Script
# This script helps automate the setup of Keycloak for the backoffice application

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - Load from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
KEYCLOAK_ADMIN="${KEYCLOAK_ADMIN:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-admin123}"
REALM_NAME="${KEYCLOAK_REALM:-backoffice}"
CLIENT_ID="${KEYCLOAK_CLIENT_ID:-backoffice-client}"
BACKOFFICE_URL="${BACKOFFICE_URL:-http://localhost:8090}"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for Keycloak to be ready
wait_for_keycloak() {
    print_info "Waiting for Keycloak to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "${KEYCLOAK_URL}/health/ready" > /dev/null 2>&1; then
            print_info "Keycloak is ready!"
            return 0
        fi
        
        print_warning "Keycloak not ready yet (attempt $attempt/$max_attempts)..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Keycloak did not become ready in time"
    exit 1
}

# Function to get admin token
get_admin_token() {
    local response=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${KEYCLOAK_ADMIN}" \
        -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
        -d "grant_type=password" \
        -d "client_id=admin-cli")
    
    if [ -z "$response" ]; then
        print_error "Failed to get admin token"
        exit 1
    fi
    
    echo "$response" | jq -r '.access_token'
}

# Function to create realm
create_realm() {
    local token=$1
    
    print_info "Creating realm: ${REALM_NAME}"
    
    local response=$(curl -s -X POST "${KEYCLOAK_URL}/admin/realms" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json" \
        -d "{
            \"realm\": \"${REALM_NAME}\",
            \"enabled\": true,
            \"sslRequired\": \"external\",
            \"registrationAllowed\": false,
            \"loginWithEmailAllowed\": true,
            \"duplicateEmailsAllowed\": false,
            \"resetPasswordAllowed\": true,
            \"editUsernameAllowed\": false,
            \"bruteForceProtected\": true
        }")
    
    if [ $? -eq 0 ]; then
        print_info "Realm '${REALM_NAME}' created successfully"
    else
        print_warning "Realm might already exist or there was an error"
    fi
}

# Function to create client
create_client() {
    local token=$1
    
    print_info "Creating client: ${CLIENT_ID}"
    
    # First, try to get existing client
    local existing_client=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/clients?clientId=${CLIENT_ID}" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json")
    
    local client_id_response=$(echo "$existing_client" | jq -r '.[0].id // empty')
    
    if [ -n "$client_id_response" ]; then
        print_warning "Client '${CLIENT_ID}' already exists"
        get_client_secret "$token" "$client_id_response"
        return 0
    fi
    
    # Create new client
    local response=$(curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/clients" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json" \
        -d "{
            \"clientId\": \"${CLIENT_ID}\",
            \"enabled\": true,
            \"clientAuthenticatorType\": \"client-secret\",
            \"secret\": \"\",
            \"redirectUris\": [\"${BACKOFFICE_URL}/*\"],
            \"webOrigins\": [\"${BACKOFFICE_URL}\"],
            \"bearerOnly\": false,
            \"consentRequired\": false,
            \"standardFlowEnabled\": true,
            \"implicitFlowEnabled\": false,
            \"directAccessGrantsEnabled\": true,
            \"serviceAccountsEnabled\": true,
            \"publicClient\": false,
            \"protocol\": \"openid-connect\",
            \"attributes\": {
                \"access.token.lifespan\": \"3600\"
            }
        }")
    
    if [ $? -eq 0 ]; then
        print_info "Client '${CLIENT_ID}' created successfully"
        sleep 2  # Wait for client to be fully created
        get_client_secret "$token"
    else
        print_error "Failed to create client"
        exit 1
    fi
}

# Function to get client secret
get_client_secret() {
    local token=$1
    local client_uuid=$2
    
    if [ -z "$client_uuid" ]; then
        # Get client UUID by clientId
        local client_response=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/clients?clientId=${CLIENT_ID}" \
            -H "Authorization: Bearer ${token}" \
            -H "Content-Type: application/json")
        
        client_uuid=$(echo "$client_response" | jq -r '.[0].id')
    fi
    
    local secret_response=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/clients/${client_uuid}/client-secret" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json")
    
    local client_secret=$(echo "$secret_response" | jq -r '.value')
    
    print_info "Client Secret: ${client_secret}"
    
    # Save to .env file
    if [ -f .env ]; then
        if grep -q "^KEYCLOAK_CLIENT_SECRET_KEY=" .env; then
            sed -i "s/^KEYCLOAK_CLIENT_SECRET_KEY=.*/KEYCLOAK_CLIENT_SECRET_KEY=${client_secret}/" .env
        else
            echo "KEYCLOAK_CLIENT_SECRET_KEY=${client_secret}" >> .env
        fi
    else
        echo "KEYCLOAK_CLIENT_SECRET_KEY=${client_secret}" > .env
    fi
    
    print_info "Client secret saved to .env file"
}

# Function to create roles
create_roles() {
    local token=$1
    
    print_info "Creating roles..."
    
    local roles=("admin" "operator" "viewer")
    
    for role in "${roles[@]}"; do
        curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/roles" \
            -H "Authorization: Bearer ${token}" \
            -H "Content-Type: application/json" \
            -d "{
                \"name\": \"${role}\",
                \"description\": \"${role} role for backoffice application\"
            }" > /dev/null
        
        if [ $? -eq 0 ]; then
            print_info "Role '${role}' created successfully"
        else
            print_warning "Role '${role}' might already exist"
        fi
    done
}

# Function to create user
create_user() {
    local token=$1
    local username=$2
    local email=$3
    local password=$4
    local roles=$5
    
    print_info "Creating user: ${username}"
    
    # Create user
    local response=$(curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/users" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"${username}\",
            \"email\": \"${email}\",
            \"firstName\": \"${username}\",
            \"lastName\": \"User\",
            \"enabled\": true,
            \"emailVerified\": true,
            \"credentials\": [{
                \"type\": \"password\",
                \"value\": \"${password}\",
                \"temporary\": false
            }]
        }")
    
    if [ $? -ne 0 ]; then
        print_warning "User '${username}' might already exist"
        return 0
    fi
    
    sleep 2  # Wait for user to be created
    
    # Get user ID
    local user_response=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/users?username=${username}" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json")
    
    local user_id=$(echo "$user_response" | jq -r '.[0].id')
    
    # Assign roles
    if [ -n "$roles" ]; then
        print_info "Assigning roles to ${username}..."
        
        for role in $roles; do
            # Get role representation
            local role_response=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/roles/${role}" \
                -H "Authorization: Bearer ${token}" \
                -H "Content-Type: application/json")
            
            # Assign role to user
            curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/users/${user_id}/role-mappings/realm" \
                -H "Authorization: Bearer ${token}" \
                -H "Content-Type: application/json" \
                -d "$role_response" > /dev/null
            
            print_info "Role '${role}' assigned to ${username}"
        done
    fi
    
    print_info "User '${username}' created successfully"
}

# Main execution
main() {
    print_info "Starting Keycloak configuration..."
    print_info "Keycloak URL: ${KEYCLOAK_URL}"
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_error "jq is not installed. Please install it: apt-get install jq or brew install jq"
        exit 1
    fi
    
    # Wait for Keycloak to be ready
    wait_for_keycloak
    
    # Get admin token
    print_info "Getting admin token..."
    local token=$(get_admin_token)
    
    if [ -z "$token" ] || [ "$token" == "null" ]; then
        print_error "Failed to get admin token"
        exit 1
    fi
    
    print_info "Admin token obtained successfully"
    
    # Create realm
    create_realm "$token"
    sleep 2
    
    # Create client
    create_client "$token"
    sleep 2
    
    # Create roles
    create_roles "$token"
    
    # Create demo users (optional)
    if [ "${CREATE_DEMO_USERS:-false}" == "true" ]; then
        print_info "Creating demo users..."
        create_user "$token" "admin" "admin@backoffice.local" "admin123" "admin"
        create_user "$token" "operator" "operator@backoffice.local" "operator123" "operator"
        create_user "$token" "viewer" "viewer@backoffice.local" "viewer123" "viewer"
    fi
    
    print_info "Keycloak configuration completed successfully!"
    print_info "==========================================="
    print_info "Keycloak Admin Console: ${KEYCLOAK_URL}/admin"
    print_info "Username: ${KEYCLOAK_ADMIN}"
    print_info "Password: ${KEYCLOAK_ADMIN_PASSWORD}"
    print_info "Realm: ${REALM_NAME}"
    print_info "Client ID: ${CLIENT_ID}"
    print_info "==========================================="
}

# Run main function
main "$@"
