# Role-Based Access Control Implementation

This document explains the implementation of role-based access control in the San Felipe Backoffice project.

## Overview

The implementation provides two main user roles:
- **Operador**: Read-only access to catalogos, costos, and bitacora modules
- **Administrador**: Full access to all modules including user and group management

## Implementation Details

### 1. Custom Admin Site

A custom `BackofficeAdminSite` has been created in `core/admin.py` with:
- Custom headers and titles
- Role-based permission checking
- App list ordering

### 2. Permission Mixins

Three permission mixins have been created:

- `OperatorPermissionMixin`: Provides read-only access for Operador users
- `AdministradorPermissionMixin`: Provides full access for Administrador users  
- `ReadOnlyBitacoraMixin`: Ensures bitacora remains read-only for all users

### 3. Admin Class Updates

All admin classes in `catalogos/admin.py`, `costos/admin.py`, and `bitacora/admin.py` have been updated to use the appropriate permission mixins.

### 4. Group Configuration

Groups and permissions are configured in `sanfelipe/settings.py`:
- `OPERADOR_GROUP_NAME`: "Operador"
- `ADMINISTRADOR_GROUP_NAME`: "Administrador"
- `OPERADOR_PERMISSIONS`: Read-only access to catalogos, costos, and bitacora
- `ADMINISTRADOR_PERMISSIONS`: Full access to all modules

### 5. Management Command

A management command `setup_roles` has been created in `core/management/commands/setup_roles.py` to:
- Create the "Operador" and "Administrador" groups
- Assign appropriate permissions to each group
- Clear existing permissions before assignment

### 6. Automatic Setup

The `setup_roles` command is automatically executed after database migrations via a signal handler in `core/signals.py`.

## Usage

### Creating Users and Assigning Roles

1. Create users through the Django admin interface
2. Assign users to either the "Operador" or "Administrador" group
3. The permissions will be automatically applied

### Running the Setup Command Manually

If you need to reset the groups and permissions:

```bash
python manage.py setup_roles
```

### Database Considerations

The system maintains the multi-database configuration:
- SQLite for auth data (users, groups, permissions)
- PostgreSQL for business data (catalogos, costos, bitacora)

## Security Features

- Operador users cannot modify or delete any data
- Operador users have no access to user/group management
- All audit log entries (bitacora) remain read-only
- Custom permission mixins ensure consistent access control

## Files Modified

- `sanfelipe/settings.py`: Added role configuration
- `core/admin.py`: Added permission mixins and custom admin site
- `catalogos/admin.py`: Applied OperatorPermissionMixin to all admin classes
- `costos/admin.py`: Applied OperatorPermissionMixin to CostoAdmin
- `bitacora/admin.py`: Applied ReadOnlyBitacoraMixin to BitacoraAdmin  
- `sanfelipe/urls.py`: Updated to use custom admin site
- `core/management/commands/setup_roles.py`: Created management command
- `core/signals.py`: Created signal handler
- `core/apps.py`: Registered signals

## Testing

To verify the implementation:

1. Create an Operador user and log in - should only see read-only access
2. Create an Administrador user and log in - should have full access
3. Verify that Operador users cannot modify or delete any data
4. Verify that bitacora remains read-only for all users

## Notes

- The system respects models with `managed=False` as specified
- Permissions are dynamically assigned based on app configuration
- The implementation follows Django best practices for security and maintainability
- The custom admin site provides a consistent user experience across all modules