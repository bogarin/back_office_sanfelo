"""Django management command to create Operator and Administrator groups with appropriate permissions."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    """Create Operator and Administrator groups with appropriate permissions."""

    help = 'Create Operator and Administrator groups with appropriate permissions'

    def handle(self, *args, **options):
        # Crear grupo Administrador
        admin_group, created = Group.objects.get_or_create(name='Administrador')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Administrador group'))

        # Asignar todos los permisos al grupo Administrador
        for permission in Permission.objects.all():
            admin_group.permissions.add(permission)
        self.stdout.write(self.style.SUCCESS('Added all permissions to Administrador group'))

        # Crear grupo Operador
        operator_group, created = Group.objects.get_or_create(name='Operador')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Operador group'))

        # Obtener todos los modelos de los módulos especificados
        apps = ['catalogos', 'costos', 'bitacora']

        for app in apps:
            content_types = ContentType.objects.filter(app_label=app)
            for content_type in content_types:
                try:
                    view_permission = Permission.objects.get(
                        codename=f'view_{content_type.model}', content_type=content_type
                    )
                    operator_group.permissions.add(view_permission)
                except Permission.DoesNotExist:
                    pass

        self.stdout.write(
            self.style.SUCCESS(f'Added view permissions for {apps} to Operador group')
        )
        self.stdout.write(self.style.SUCCESS('Roles setup completed successfully'))
