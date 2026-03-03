"""
Tests for catalogos models.

This module contains tests for:
- All catalog models (CatTramite, CatEstatus, etc.)
- Model string representations
- Model properties and methods
- Model constraints
"""

from django.test import TestCase

from tests.factories import (
    CatActividadFactory,
    CatCategoriaFactory,
    CatEstatusFactory,
    CatIncisoFactory,
    CatPeritoFactory,
    CatRequisitoFactory,
    CatTipoFactory,
    CatTramiteFactory,
)


class TestCatTramite(TestCase):
    """Test suite for CatTramite model."""

    def setUp(self):
        """Set up test fixtures."""
        self.tramite = CatTramiteFactory()

    def test_str_representation(self):
        """Test string representation of CatTramite."""
        self.assertEqual(str(self.tramite), self.tramite.nombre)

    def test_model_fields(self):
        """Test CatTramite model fields."""
        self.assertIsNotNone(self.tramite.nombre)
        self.assertIsNotNone(self.tramite.descripcion)
        self.assertIsNotNone(self.tramite.area)
        self.assertIsNotNone(self.tramite.respuesta_dias)
        self.assertIsNotNone(self.tramite.pago_inicial)
        self.assertIsNotNone(self.tramite.url)
        self.assertIsNotNone(self.tramite.activo)


class TestCatPerito(TestCase):
    """Test suite for CatPerito model."""

    def setUp(self):
        """Set up test fixtures."""
        self.perito = CatPeritoFactory()

    def test_str_representation(self):
        """Test string representation of CatPerito."""
        expected = f'{self.perito.paterno} {self.perito.materno} {self.perito.nombre}'
        self.assertEqual(str(self.perito), expected)

    def test_nombre_completo_property(self):
        """Test nombre_completo property."""
        nombre_completo = self.perito.nombre_completo
        self.assertIn(self.perito.nombre, nombre_completo)
        self.assertIn(self.perito.paterno, nombre_completo)


class TestCatActividad(TestCase):
    """Test suite for CatActividad model."""

    def setUp(self):
        """Set up test fixtures."""
        self.actividad = CatActividadFactory()

    def test_str_representation(self):
        """Test string representation of CatActividad."""
        self.assertEqual(str(self.actividad), self.actividad.actividad)


class TestCatCategoria(TestCase):
    """Test suite for CatCategoria model."""

    def setUp(self):
        """Set up test fixtures."""
        self.categoria = CatCategoriaFactory()

    def test_str_representation(self):
        """Test string representation of CatCategoria."""
        self.assertEqual(str(self.categoria), self.categoria.categoria)


class TestCatInciso(TestCase):
    """Test suite for CatInciso model."""

    def setUp(self):
        """Set up test fixtures."""
        self.inciso = CatIncisoFactory()

    def test_str_representation(self):
        """Test string representation of CatInciso."""
        expected = f'{self.inciso.inciso} - {self.inciso.descripcion}'
        self.assertEqual(str(self.inciso), expected)


class TestCatRequisito(TestCase):
    """Test suite for CatRequisito model."""

    def setUp(self):
        """Set up test fixtures."""
        self.requisito = CatRequisitoFactory()

    def test_str_representation(self):
        """Test string representation of CatRequisito."""
        self.assertEqual(str(self.requisito), self.requisito.requisito)


class TestCatTipo(TestCase):
    """Test suite for CatTipo model."""

    def setUp(self):
        """Set up test fixtures."""
        self.tipo = CatTipoFactory()

    def test_str_representation(self):
        """Test string representation of CatTipo."""
        self.assertEqual(str(self.tipo), self.tipo.tipo)
