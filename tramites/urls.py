"""
URL configuration for tramites app.

NOTE: This project uses Django Admin almost exclusively for backoffice UI.
All tramite management is done through the Django Admin interface at /admin/.

No custom URL patterns are needed as the Django Admin provides:
- List and manage tramites at /admin/tramites/tramite/
- Create new tramites through the admin interface
- Edit existing tramites with full control
- Delete with confirmation

If custom URLs are needed in the future (e.g., API endpoints, public views),
they can be added here.
"""

app_name = 'tramites'

urlpatterns = [
    # No custom URL patterns - using Django Admin exclusively
    # Admin interface: /admin/tramites/tramite/
]
