"""Add catalog models and convert Tramite IntegerField to ForeignKey.

Consolidated migration that:
1. Creates all catalog models (TramiteCatalogo, TramiteEstatus, Perito,
   Actividad, Categoria, Requisito, Tipo) and pivot tables
2. Changes Tramite to managed=True (for test suite)
3. Replaces IntegerField FK columns with proper Django ForeignKeys
4. Drops obsolete indexes from migration 0001

In production (PostgreSQL), these tables exist externally with managed=False,
so this migration only runs during tests (SQLite with managed=True).
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('tramites', '0002_alter_tramite_options'),
    ]

    operations = [
        # ── Drop indexes that reference columns being renamed ──
        migrations.RemoveIndex(
            model_name='tramite',
            name='tramite_id_cat__f4374b_idx',
        ),
        migrations.RemoveIndex(
            model_name='tramite',
            name='idx_tramite_estatus_no_pagado',
        ),
        migrations.RemoveIndex(
            model_name='tramite',
            name='idx_tramite_urgente',
        ),
        migrations.RemoveIndex(
            model_name='tramite',
            name='idx_tramite_urgente_no_pagado',
        ),
        migrations.RemoveIndex(
            model_name='tramite',
            name='idx_tramite_prioridad',
        ),
        # ── Create catalog models ──
        migrations.CreateModel(
            name='Actividad',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('actividad', models.CharField(max_length=250, verbose_name='Actividad')),
            ],
            options={
                'verbose_name': 'Actividad',
                'verbose_name_plural': 'Actividades',
                'db_table': 'cat_actividad',
                'ordering': ['actividad'],
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                (
                    'categoria',
                    models.CharField(
                        blank=True, max_length=120, null=True, verbose_name='Categoría'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
                'db_table': 'cat_categoria',
                'ordering': ['categoria'],
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Perito',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                (
                    'paterno',
                    models.CharField(
                        blank=True, max_length=30, null=True, verbose_name='Apellido Paterno'
                    ),
                ),
                (
                    'materno',
                    models.CharField(
                        blank=True, max_length=30, null=True, verbose_name='Apellido Materno'
                    ),
                ),
                (
                    'nombre',
                    models.CharField(blank=True, max_length=90, null=True, verbose_name='Nombre'),
                ),
                (
                    'domicilio',
                    models.CharField(
                        blank=True, max_length=250, null=True, verbose_name='Domicilio'
                    ),
                ),
                (
                    'colonia',
                    models.CharField(blank=True, max_length=120, null=True, verbose_name='Colonia'),
                ),
                (
                    'telefono',
                    models.CharField(blank=True, max_length=16, null=True, verbose_name='Teléfono'),
                ),
                (
                    'celular',
                    models.CharField(blank=True, max_length=16, null=True, verbose_name='Celular'),
                ),
                (
                    'correo',
                    models.CharField(blank=True, max_length=255, null=True, verbose_name='Correo'),
                ),
                (
                    'revalidacion',
                    models.DateField(blank=True, null=True, verbose_name='Revalidación'),
                ),
                (
                    'fecha_registro',
                    models.DateField(blank=True, null=True, verbose_name='Fecha de Registro'),
                ),
                ('rfc', models.CharField(blank=True, max_length=17, null=True, verbose_name='RFC')),
                ('estatus', models.BooleanField(verbose_name='Estatus')),
                (
                    'cedula',
                    models.CharField(blank=True, max_length=19, null=True, verbose_name='Cédula'),
                ),
            ],
            options={
                'verbose_name': 'Perito',
                'verbose_name_plural': 'Peritos',
                'db_table': 'cat_perito',
                'ordering': ('paterno', 'materno', 'nombre'),
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Requisito',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('requisito', models.CharField(max_length=480, verbose_name='Requisito')),
            ],
            options={
                'verbose_name': 'Requisito',
                'verbose_name_plural': 'Requisitos',
                'db_table': 'cat_requisito',
                'ordering': ['requisito'],
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Tipo',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('tipo', models.CharField(max_length=120, verbose_name='Tipo')),
            ],
            options={
                'verbose_name': 'Tipo',
                'verbose_name_plural': 'Tipos',
                'db_table': 'cat_tipo',
                'ordering': ['tipo'],
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TramiteCatalogo',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=255, verbose_name='Nombre')),
                (
                    'descripcion',
                    models.CharField(
                        blank=True, max_length=600, null=True, verbose_name='Descripción'
                    ),
                ),
                (
                    'area',
                    models.CharField(blank=True, max_length=80, null=True, verbose_name='Área'),
                ),
                (
                    'respuesta_dias',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=5,
                        null=True,
                        verbose_name='Respuesta en Días',
                    ),
                ),
                (
                    'pago_inicial',
                    models.BooleanField(blank=True, null=True, verbose_name='Pago Inicial'),
                ),
                (
                    'url',
                    models.CharField(blank=True, max_length=512, null=True, verbose_name='URL'),
                ),
                ('activo', models.BooleanField(null=True, verbose_name='Activo')),
            ],
            options={
                'verbose_name': 'Catálogo Trámite',
                'verbose_name_plural': 'Catálogo Trámites',
                'db_table': 'cat_tramite',
                'ordering': ('nombre',),
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TramiteEstatus',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('estatus', models.CharField(max_length=30, verbose_name='Estatus')),
                (
                    'responsable',
                    models.CharField(
                        blank=True, max_length=64, null=True, verbose_name='Responsable'
                    ),
                ),
                (
                    'descripcion',
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name='Descripción'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Estatus de Trámite',
                'verbose_name_plural': 'Estatus de Trámites',
                'db_table': 'cat_estatus',
                'ordering': ('id',),
                'managed': True,
            },
        ),
        # ── Change Tramite to managed=True (test suite) ──
        migrations.AlterModelOptions(
            name='tramite',
            options={
                'managed': True,
                'ordering': ('-creado',),
                'verbose_name': 'Trámite',
                'verbose_name_plural': 'Trámites',
            },
        ),
        # ── Replace IntegerField with ForeignKey on Tramite ──
        # id_cat_tramite → tramite_catalogo
        migrations.RemoveField(
            model_name='tramite',
            name='id_cat_tramite',
        ),
        migrations.AddField(
            model_name='tramite',
            name='tramite_catalogo',
            field=models.ForeignKey(
                db_column='id_cat_tramite',
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='tramites',
                to='tramites.tramitecatalogo',
                verbose_name='Catálogo Trámite',
            ),
        ),
        # id_cat_estatus → estatus
        migrations.RemoveField(
            model_name='tramite',
            name='id_cat_estatus',
        ),
        migrations.AddField(
            model_name='tramite',
            name='estatus',
            field=models.ForeignKey(
                db_column='id_cat_estatus',
                default=101,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='tramites',
                to='tramites.tramiteestatus',
                verbose_name='Estatus',
            ),
        ),
        # id_cat_perito → perito
        migrations.RemoveField(
            model_name='tramite',
            name='id_cat_perito',
        ),
        migrations.AddField(
            model_name='tramite',
            name='perito',
            field=models.ForeignKey(
                db_column='id_cat_perito',
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='tramites',
                to='tramites.perito',
                verbose_name='Perito',
            ),
        ),
        # ── Drop remaining obsolete index ──
        migrations.RemoveIndex(
            model_name='tramite',
            name='tramite_folio_fb608e_idx',
        ),
        # ── Create pivot tables ──
        migrations.CreateModel(
            name='TramiteCatalogoActividad',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                (
                    'actividad',
                    models.ForeignKey(
                        db_column='id_cat_actividad',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='tramites_catalogo',
                        to='tramites.actividad',
                        verbose_name='Actividad',
                    ),
                ),
                (
                    'tramite_catalogo',
                    models.ForeignKey(
                        db_column='id_cat_tramite',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='actividades',
                        to='tramites.tramitecatalogo',
                        verbose_name='Catálogo Trámite',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Relación Trámite-Actividad',
                'verbose_name_plural': 'Relaciones Trámite-Actividad',
                'db_table': 'rel_tmt_actividad',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TramiteCatalogoCategoria',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                (
                    'categoria',
                    models.ForeignKey(
                        db_column='id_cat_categoria',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='tramites_catalogo',
                        to='tramites.categoria',
                        verbose_name='Categoría',
                    ),
                ),
                (
                    'tramite_catalogo',
                    models.ForeignKey(
                        db_column='id_cat_tramite',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='categorias',
                        to='tramites.tramitecatalogo',
                        verbose_name='Catálogo Trámite',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Relación Trámite-Categoría',
                'verbose_name_plural': 'Relaciones Trámite-Categoría',
                'db_table': 'rel_tmt_categoria',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TramiteCatalogoRequisito',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                (
                    'categoria',
                    models.ForeignKey(
                        blank=True,
                        db_column='id_cat_categoria',
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='requisitos_por_tramite',
                        to='tramites.categoria',
                        verbose_name='Categoría',
                    ),
                ),
                (
                    'requisito',
                    models.ForeignKey(
                        db_column='id_cat_requisito',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='tramites_catalogo',
                        to='tramites.requisito',
                        verbose_name='Requisito',
                    ),
                ),
                (
                    'tramite_catalogo',
                    models.ForeignKey(
                        db_column='id_cat_tramite',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='requisitos',
                        to='tramites.tramitecatalogo',
                        verbose_name='Catálogo Trámite',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Relación Trámite-Requisito-Categoría',
                'verbose_name_plural': 'Relaciones Trámite-Requisito-Categoría',
                'db_table': 'rel_tmt_cate_req',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TramiteCatalogoTipoRequisito',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                (
                    'requisito',
                    models.ForeignKey(
                        db_column='id_cat_requisito',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='tipos_por_tramite',
                        to='tramites.requisito',
                        verbose_name='Requisito',
                    ),
                ),
                (
                    'tipo',
                    models.ForeignKey(
                        db_column='id_cat_tipo',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='requisitos_por_tramite',
                        to='tramites.tipo',
                        verbose_name='Tipo',
                    ),
                ),
                (
                    'tramite_catalogo',
                    models.ForeignKey(
                        db_column='id_cat_tramite',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='tipos_requisito',
                        to='tramites.tramitecatalogo',
                        verbose_name='Catálogo Trámite',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Relación Tipo-Trámite-Requisito',
                'verbose_name_plural': 'Relaciones Tipo-Trámite-Requisito',
                'db_table': 'rel_tmt_tipo_req',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Actividades',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('id_cat_usuario', models.IntegerField(verbose_name='ID Usuario')),
                ('fecha_inicio', models.DateField(verbose_name='Fecha Inicio')),
                ('fecha_fin', models.DateField(verbose_name='Fecha Fin')),
                ('secuencia', models.IntegerField(verbose_name='Secuencia')),
                (
                    'observacion',
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name='Observación'
                    ),
                ),
                (
                    'actividad',
                    models.ForeignKey(
                        db_column='id_cat_actividad',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='registros',
                        to='tramites.actividad',
                        verbose_name='Actividad',
                    ),
                ),
                (
                    'tramite',
                    models.ForeignKey(
                        db_column='id_tramite',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='actividades',
                        to='tramites.tramite',
                        verbose_name='Trámite',
                    ),
                ),
                (
                    'estatus',
                    models.ForeignKey(
                        db_column='id_cat_estatus',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='actividades',
                        to='tramites.tramiteestatus',
                        verbose_name='Estatus',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Actividad de Trámite',
                'verbose_name_plural': 'Actividades de Trámite',
                'db_table': 'actividades',
                'ordering': ['-secuencia'],
                'managed': True,
            },
        ),
    ]
