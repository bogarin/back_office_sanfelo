from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('tramites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cerrado',
            fields=[],
            options={
                'verbose_name': 'Trámites finalizados',
                'verbose_name_plural': 'Trámites finalizados',
                'ordering': ('-creado', '-urgente'),
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('tramites.tramite',),
        ),
    ]
