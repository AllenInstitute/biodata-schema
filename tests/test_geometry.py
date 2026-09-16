"""Tests for the geometry module"""

from biodata_models.units import SizeUnit

from biodata_schema.components.geometry import Circle, Rectangle


class TestRectangle:
    """Tests for the Rectangle class"""

    def test_create_rectangle(self):
        """Test creating a rectangle with specific dimensions and units"""
        rect = Rectangle(width=10.0, height=5.0, size_unit=SizeUnit.MM)
        assert rect.width == 10.0
        assert rect.height == 5.0
        assert rect.size_unit == SizeUnit.MM

    def test_different_units(self):
        """Test creating a rectangle with different units"""
        rect = Rectangle(width=1.0, height=2.0, size_unit=SizeUnit.UM)
        assert rect.size_unit == SizeUnit.UM


class TestCircle:
    """Tests for the Circle class"""

    def test_create_circle(self):
        """Test creating a circle with specific radius and units"""
        circle = Circle(radius=3.0, radius_unit=SizeUnit.MM)
        assert circle.radius == 3.0
        assert circle.radius_unit == SizeUnit.MM

    def test_different_units(self):
        """Test creating a circle with different units"""
        circle = Circle(radius=500.0, radius_unit=SizeUnit.UM)
        assert circle.radius_unit == SizeUnit.UM
