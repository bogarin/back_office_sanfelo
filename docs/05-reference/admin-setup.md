# Django Admin Configuration - Backoffice San Felipe

## Overview

This project uses Django Admin almost exclusively as the UI for the backoffice system. All CRUD operations, filtering, search, and management of tramites, catalogos, bitacora, and costos are handled through the Django Admin interface.

## Architecture

### Why Django Admin?

1. **Rapid Development**: No need to build custom views and templates
2. **Built-in Features**: Search, filtering, pagination, bulk actions
3. **Security**: Built-in authentication and permissions
4. **Customizable**: Actions, fieldsets, list displays, custom methods
5. **Maintainable**: Standard Django patterns, well-documented

### Access Points

- **Home**: `/` - Landing page with link to admin
- **Admin**: `/admin/` - Main Django Admin interface
- **Tramites**: `/admin/tramites/tramite/` - Tramite management
- **Catalogos**: `/admin/catalogos/` - All catalog tables
- **Costos**: `/admin/costos/` - Costos and UMA management
- **Bitacora**: `/admin/bitacora/bitacora/` - Audit log (read-only)

## Configuration Files

### 1. Settings (`sanfelipe/settings.py`)

```python
INSTALLED_APPS = [
    # Django Admin
    "django.contrib.admin",
    # ... other apps
]
```

The `django.contrib.admin` app is included in `INSTALLED_APPS`.

### 2. URLs (`sanfelipe/urls.py`)

```python
urlpatterns = [
    path("", home, name="home"),
    path("health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
]
```

The admin is available at `/admin/`.

### 3. Static Files

Custom CSS: `static/admin/css/custom.css`

Features:
- Custom header gradient (#667eea to #764ba2)
- Improved table styling
- Better form inputs with focus states
- Responsive adjustments
- Custom badge styles

### 4. Templates

Custom admin template: `templates/admin/index.html`

Features:
- Dashboard with statistics
- Tramites count, urgent, paid, pending payment
- Status distribution chart
- Visual cards for metrics

## Admin Configurations by App

### Core (`core/admin.py`)

**Base Classes:**

- `BaseModelAdmin` - Common configuration for all admins
- `ReadOnlyModelAdmin` - For read-only models (bitacora)
- `CatalogBaseAdmin` - For catalog tables with common features
- `AuditTrailMixin` - Automatically logs changes to bitacora

**Global Settings:**

```python
admin.site.site_header = "Backoffice San Felipe"
admin.site.site_title = "Backoffice San Felipe"
admin.site.index_title = "Panel de Administración"
```

**Custom Actions:**

- `mark_as_active` - Mark selected items as active
- `mark_as_inactive` - Mark selected items as inactive
- `mark_urgent` - Mark tramites as urgent
- `mark_not_urgent` - Mark tramites as not urgent
- `mark_as_paid` - Mark tramites as paid
- `mark_as_unpaid` - Mark tramites as unpaid

### Tramites (`tramites/admin.py`)

**TramiteAdmin:**

```python
@admin.register(Tramite)
class TramiteAdmin(AuditTrailMixin, BaseModelAdmin):
    list_display = (
        "folio",
        "tramite_nombre",
        "estatus_display",
        "solicitante_nombre",
        "importe_total",
        "pagado_badge",
        "urgente_badge",
        "creado",
    )
    list_filter = (
        "id_cat_estatus",
        "pagado",
        "urgente",
        "es_propietario",
        "creado",
        "modificado",
    )
    search_fields = (
        "folio",
        "nom_sol",
        "tel_sol",
        "correo_sol",
        "clave_catastral",
        "observacion",
    )
    list_editable = ("pagado", "urgente")
    actions = [mark_urgent, mark_not_urgent, mark_as_paid, mark_as_unpaid]
```

**Features:**

- Custom display methods with color-coded badges
- Fieldsets for organized form layout
- Dynamic widget choices from catalog tables
- Audit trail integration
- Dashboard statistics in changelist_view

### Catalogos (`catalogos/admin.py`)

**Registered Models:**

1. `CatTramite` - Tramite types catalog
2. `CatEstatus` - Status catalog (with group display)
3. `CatUsuario` - User catalog
4. `CatPerito` - Perito catalog (with nombre_completo)
5. `CatActividad` - Activities catalog
6. `CatCategoria` - Categories catalog
7. `CatInciso` - Budget items catalog
8. `CatRequisito` - Requirements catalog
9. `CatTipo` - Types catalog

**Relationship Tables:**

1. `RelTmtCateReq` - Tramite-Requisito-Categoría
2. `RelTmtCategoria` - Tramite-Categoría
3. `RelTmtInciso` - Inciso-Trámite
4. `RelTmtTipoReq` - Tipo-Trámite-Requisito
5. `RelTmtActividad` - Trámite-Actividad

**Additional Tables:**

1. `Actividades` - Activity records for tramites
2. `Cobro` - Payment records for tramites

**Features:**

- Badge displays for status fields
- Inline editing for quick changes
- Dynamic choices from related tables
- Audit trail integration

### Bitacora (`bitacora/admin.py`)

**BitacoraAdmin:**

```python
@admin.register(Bitacora)
class BitacoraAdmin(ReadOnlyModelAdmin, BaseModelAdmin):
    """Read-only admin for audit log."""
```

**Features:**

- Read-only (no add, change, delete permissions)
- Color-coded movement types (INSERT, UPDATE, DELETE)
- Date hierarchy for easy navigation
- Statistics in changelist_view

### Costos (`costos/admin.py`)

**CostoAdmin:**

```python
@admin.register(Costo)
class CostoAdmin(AuditTrailMixin, BaseModelAdmin):
    """Admin for costos."""
```

**Features:**

- Calculated importe display based on UMA value
- Inline editing for status fields
- Dynamic widget choices
- Auto-populated usuario and fecha_actualiza on save

**UmaAdmin:**

```python
@admin.register(Uma)
class UmaAdmin(BaseModelAdmin):
    """Admin for UMA value - single record."""
```

**Features:**

- Only one record allowed (id=1)
- Calls stored procedure on update
- Displays last update date

## Customization Examples

### 1. Custom Display Methods

```python
def pagado_badge(self, obj):
    """Display pagado status as badge."""
    if obj.pagado:
        return format_html(
            '<span style="background-color: #28a745; color: white; '
            'padding: 2px 8px; border-radius: 4px;">Pagado</span>'
        )
    return format_html(
        '<span style="background-color: #dc3545; color: white; '
        'padding: 2px 8px; border-radius: 4px;">No Pagado</span>'
    )
```

### 2. Custom Actions

```python
def mark_as_paid(modeladmin, request, queryset):
    """Admin action to mark tramites as paid."""
    rows_updated = queryset.update(pagado=True)
    modeladmin.message_user(
        request,
        f"{rows_updated} trámites marcados como pagados.",
    )

mark_as_paid.short_description = "Marcar como pagados"
```

### 3. Fieldsets

```python
fieldsets = (
    (
        "Información del Trámite",
        {
            "fields": (
                "folio",
                "id_cat_tramite",
                "id_cat_estatus",
                "id_cat_perito",
                "tipo",
            ),
            "classes": ("wide",),
        },
    ),
    # ... more fieldsets
)
```

### 4. Audit Trail

```python
class AuditTrailMixin:
    """Mixin to add audit trail functionality."""
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        if change:
            Bitacora.objects.create(
                usuario_sis=request.user.username,
                tipo_mov="UPDATE",
                usuario_pc=request.META.get("REMOTE_ADDR", ""),
                fecha=date.today(),
                observaciones=f"Actualizado {self.model._meta.verbose_name}: {obj}",
            )
```

## Security

### Authentication

The admin uses Django's built-in authentication. Only authenticated users with `is_staff=True` can access the admin.

### Permissions

- **Superuser**: Full access to all admin features
- **Staff**: Can access admin features based on permissions
- **Regular Users**: Cannot access admin

The `is_staff` and `is_superuser` flags are managed through Django admin.

## Deployment

### Production Considerations

1. **HTTPS**: Admin should only be accessible over HTTPS
2. **Restrict IP**: Limit access to admin by IP address (intranet)
3. **Strong Passwords**: Django manages user authentication
4. **Logging**: All admin actions are logged to bitacora
5. **Backup**: Regular backups of database

### Monitoring

- **Health Check**: `/health/` endpoint for monitoring
- **Logs**: Check `/logs/django.log` for errors
- **Debug Toolbar**: Available in DEBUG mode only

## Usage Examples

### Creating a New Tramite

1. Navigate to `/admin/tramites/tramite/`
2. Click "Añadir Trámite"
3. Fill in the form (folio is auto-generated)
4. Click "Guardar"

### Updating Tramite Status

1. Go to `/admin/tramites/tramite/`
2. Find the tramite in the list
3. Click on the tramite
4. Change the status
5. Click "Guardar"
6. Change is automatically logged to bitacora

### Bulk Actions

1. Go to `/admin/tramites/tramite/`
2. Select multiple tramites
3. Choose action from dropdown (e.g., "Marcar como pagados")
4. Click "Ejecutar"
5. Confirm action

### Searching and Filtering

1. Use the search box to find by folio, name, phone, etc.
2. Use the filters on the right to narrow results
3. Combine search and filters for precise results

## Future Enhancements

1. **Custom Admin Actions**: Add more bulk operations
2. **Custom Filters**: Create date range filters, custom choices
3. **Export**: Add CSV/Excel export functionality
4. **Charts**: Integrate Chart.js for dashboard
5. **Reports**: Add custom report views linked from admin
6. **API**: Add API endpoints for mobile apps/external systems

## Troubleshooting

### Admin Not Loading

- Check `INSTALLED_APPS` includes `django.contrib.admin`
- Check URL patterns include `admin.site.urls`
- Check static files are being served

### Permissions Issues

- Verify user has `is_staff` flag
- Check permissions in Django admin

### Static Files Not Loading

- Run `python manage.py collectstatic`
- Check `STATIC_URL` and `STATIC_ROOT` settings
- Verify static files directory exists

## References

- [Django Admin Documentation](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)
- [Django Admin Cookbook](https://books.agiliq.com/projects/django-admin-cookbook/en/latest/)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)
