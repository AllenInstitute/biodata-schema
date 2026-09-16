"""Tests for the coordinates module"""

import pytest
from biodata_models.atlas import AtlasName
from biodata_models.units import SizeUnit

from biodata_schema.components.coordinates import (
    Atlas,
    Axis,
    AxisName,
    CoordinateSystem,
    Direction,
    Handedness,
    Origin,
    ReferenceCoordinateSystem,
    Rotation,
    RotationDirection,
    Translation,
)


class TestTranslationFrame:
    """Tests for Translation frame field"""

    def test_default_frame_is_global(self):
        """Test that the default frame is global"""
        t = Translation(translation=[1, 2, 3])
        assert t.reference_coordinate_system == ReferenceCoordinateSystem.GLOBAL

    def test_local_frame(self):
        """Test that local frame is stored correctly"""
        t = Translation(translation=[1, 2, 3], reference_coordinate_system=ReferenceCoordinateSystem.LOCAL)
        assert t.reference_coordinate_system == ReferenceCoordinateSystem.LOCAL


class TestRotationNewFields:
    """Tests for new Rotation fields"""

    def test_default_fields(self):
        """Test that default field values are correct"""
        r = Rotation(angles=[45, 0, 0])
        assert r.reference_coordinate_system == ReferenceCoordinateSystem.GLOBAL
        assert r.rotation_direction == RotationDirection.RIGHT_HAND
        assert r.pivot == ReferenceCoordinateSystem.GLOBAL
        assert r.axis_order == "xyz"

    def test_axis_order_normalized_to_lowercase(self):
        """Test that axis_order is normalized to lowercase"""
        r = Rotation(angles=[45, 0, 0], axis_order="XYZ")
        assert r.axis_order == "xyz"

    def test_invalid_axis_order_raises(self):
        """Test that an invalid axis_order raises an exception"""
        with pytest.raises(Exception):
            Rotation(angles=[45, 0, 0], axis_order="abc")

    def test_pivot_field_stored(self):
        """Test that pivot field is stored correctly"""
        r = Rotation(angles=[0, 0, 90], pivot=ReferenceCoordinateSystem.LOCAL)
        assert r.pivot == ReferenceCoordinateSystem.LOCAL


class TestCoordinateSystemHandedness:
    """Tests for CoordinateSystem handedness field"""

    def test_default_handedness_is_none(self):
        """Test that handedness defaults to None"""
        cs = CoordinateSystem(
            name="TEST",
            origin=Origin.BREGMA,
            axis_unit=SizeUnit.MM,
            axes=[
                Axis(name=AxisName.AP, direction=Direction.PA),
                Axis(name=AxisName.ML, direction=Direction.LR),
                Axis(name=AxisName.SI, direction=Direction.SI),
            ],
        )
        assert cs.handedness is None

    def test_right_handedness(self):
        """Test setting right handedness"""
        cs = CoordinateSystem(
            name="TEST_R",
            origin=Origin.BREGMA,
            axis_unit=SizeUnit.MM,
            handedness=Handedness.RIGHT,
            axes=[
                Axis(name=AxisName.AP, direction=Direction.PA),
                Axis(name=AxisName.ML, direction=Direction.LR),
                Axis(name=AxisName.SI, direction=Direction.SI),
            ],
        )
        assert cs.handedness == Handedness.RIGHT

    def test_left_handedness(self):
        """Test setting left handedness"""
        cs = CoordinateSystem(
            name="TEST_L",
            origin=Origin.BREGMA,
            axis_unit=SizeUnit.MM,
            handedness=Handedness.LEFT,
            axes=[
                Axis(name=AxisName.AP, direction=Direction.PA),
                Axis(name=AxisName.ML, direction=Direction.LR),
                Axis(name=AxisName.SI, direction=Direction.SI),
            ],
        )
        assert cs.handedness == Handedness.LEFT


class TestAtlas:
    """Tests for the Atlas class"""

    def setup_method(self):
        """Set up pieces to use for testing"""
        self.axes = [
            Axis(name=AxisName.X, direction=Direction.LR),
            Axis(name=AxisName.Y, direction=Direction.AP),
            Axis(name=AxisName.Z, direction=Direction.SI),
        ]
        self.size = [10, 20, 30]
        self.resolution = [0.1, 0.1, 0.1]

    def test_validate_atlas_valid(self):
        """Test validate_atlas method with valid data"""

        axes = self.axes
        size = self.size
        resolution = self.resolution

        atlas = Atlas(
            name=AtlasName.CCF,
            version="1.0",
            axis_unit=SizeUnit.UM,
            size=size,
            size_unit=SizeUnit.MM,
            resolution=resolution,
            resolution_unit=SizeUnit.MM,
            axes=axes,
            origin=Origin.BREGMA,
        )
        assert atlas is not None


class TestCoordinateSystemMouseAnatomyOrigin:
    """Tests for CoordinateSystem with MouseAnatomyModel as origin"""

    @pytest.mark.online
    def test_mouse_anatomy_origin(self):  # pragma: no cover
        """Test that CoordinateSystem accepts a MouseAnatomyModel as origin"""
        from biodata_models.mouse_anatomy import MouseAnatomy

        cs = CoordinateSystem(
            name="TEST_MOUSE_ANATOMY",
            origin=MouseAnatomy.FRONTONASAL_SUTURE,
            axis_unit=SizeUnit.MM,
            axes=[
                Axis(name=AxisName.AP, direction=Direction.PA),
                Axis(name=AxisName.ML, direction=Direction.LR),
                Axis(name=AxisName.SI, direction=Direction.SI),
            ],
        )
        assert cs.origin == MouseAnatomy.FRONTONASAL_SUTURE

        cs_roundtrip = CoordinateSystem.model_validate(cs.model_dump())
        assert cs_roundtrip.origin == MouseAnatomy.FRONTONASAL_SUTURE
