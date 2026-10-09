"""Tests for the coordinates module"""

import pytest
from biodata_models.atlas import AtlasName
from biodata_models.units import SizeUnit
from pydantic import TypeAdapter, ValidationError

from biodata_schema.components.coordinates import (
    Atlas,
    Axis,
    AxisName,
    CoordinateSystem,
    CoordinateSystemOrNA,
    Direction,
    Handedness,
    Origin,
    ReferenceCoordinateSystem,
    Rotation,
    RotationDirection,
    Translation,
)
from biodata_schema.components.specimen_procedures import PlanarSectioning
from biodata_schema.components.subject_procedures import Surgery
from biodata_schema.core.acquisition import Acquisition
from biodata_schema.core.instrument import Instrument
from biodata_schema.core.procedures import Procedures
from biodata_schema.utils.merge import merge_coordinate_systems
from tests.coordinate_systems import BREGMA_ARI


@pytest.mark.parametrize("model", [Instrument, Acquisition, Procedures, Surgery, PlanarSectioning])
def test_not_applicable_global_coordinate_field(model):
    """Every global frame accepts and round-trips only the explicit sentinel."""
    adapter = TypeAdapter(model.model_fields["global_coordinate_system"].annotation)
    value = adapter.validate_python(CoordinateSystem.NotApplicable)
    assert value == "Not applicable"
    assert adapter.validate_json(adapter.dump_json(value)) == value
    with pytest.raises(ValidationError):
        adapter.validate_python("unknown")
    schema = model.model_json_schema()["properties"]["global_coordinate_system"]
    assert {"const": "Not applicable", "type": "string"} in schema["anyOf"]
    assert model.model_fields["global_coordinate_system"].is_required() == (model is Instrument)
    if model is not Instrument:
        assert adapter.validate_python(None) is None


def test_not_applicable_is_not_a_coordinate_model_field():
    """The class constant does not change real coordinate-system objects."""
    assert "NotApplicable" not in CoordinateSystem.model_fields
    assert "NotApplicable" not in BREGMA_ARI.model_dump()
    adapter = TypeAdapter(CoordinateSystemOrNA)
    assert adapter.validate_json(adapter.dump_json(BREGMA_ARI)) == BREGMA_ARI


@pytest.mark.parametrize(
    "first,second,expected",
    [
        (CoordinateSystem.NotApplicable, CoordinateSystem.NotApplicable, CoordinateSystem.NotApplicable),
        (CoordinateSystem.NotApplicable, None, CoordinateSystem.NotApplicable),
        (None, CoordinateSystem.NotApplicable, CoordinateSystem.NotApplicable),
    ],
)
def test_merge_not_applicable_coordinate_systems(first, second, expected):
    """Not-applicable frames merge like any other explicit frame."""
    assert merge_coordinate_systems(first, second) == expected


@pytest.mark.parametrize(
    "first,second", [(CoordinateSystem.NotApplicable, BREGMA_ARI), (BREGMA_ARI, CoordinateSystem.NotApplicable)]
)
def test_merge_not_applicable_with_real_frame(first, second):
    """A real frame overrides not-applicable in either operand order."""
    assert merge_coordinate_systems(first, second) == BREGMA_ARI


@pytest.mark.parametrize("model", [Instrument, Acquisition, Procedures])
@pytest.mark.parametrize("real_first", [True, False])
def test_core_merge_real_frame_overrides_not_applicable(model, real_first):
    """Core-model addition keeps the real frame and validates in both operand orders."""
    if model is Instrument:
        from examples.ephys_instrument import inst as spatial

        nonspatial = Instrument(
            instrument_name=spatial.instrument_name,
            modification_date=spatial.modification_date,
            location=spatial.location,
            temperature_control=spatial.temperature_control,
            modalities=[],
            components=[],
            global_coordinate_system=CoordinateSystem.NotApplicable,
        )
    elif model is Acquisition:
        from examples.ephys_acquisition import acquisition as spatial

        nonspatial = Acquisition(
            subject_name=spatial.subject_name,
            instrument_name=spatial.instrument_name,
            acquisition_start_time=spatial.acquisition_start_time,
            acquisition_end_time=spatial.acquisition_end_time,
            acquisition_type=spatial.acquisition_type,
            data_streams=[],
            global_coordinate_system=CoordinateSystem.NotApplicable,
        )
    else:
        from examples.thermistor_procedures import p as spatial

        nonspatial = Procedures(
            subject_name=spatial.subject_name,
            global_coordinate_system=CoordinateSystem.NotApplicable,
        )
    combined = spatial + nonspatial if real_first else nonspatial + spatial
    assert combined.global_coordinate_system == spatial.global_coordinate_system
    revalidated = model.model_validate_json(combined.model_dump_json())
    assert revalidated.global_coordinate_system == spatial.global_coordinate_system


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


class TestCoordinateSystemAnatomyModelOrigin:
    """Tests for CoordinateSystem with AnatomyModel as origin"""

    def test_anatomy_model_origin(self):
        """Test that CoordinateSystem accepts an AnatomyModel as origin"""
        from biodata_models.anatomy import AnatomyModel
        from biodata_models.registries import Registry

        frontonasal_suture = AnatomyModel(
            name="Frontonasal suture",
            registry=Registry.EMAPA,
            registry_identifier="EMAPA:TEST",
        )

        cs = CoordinateSystem(
            name="TEST_MOUSE_ANATOMY",
            origin=frontonasal_suture,
            axis_unit=SizeUnit.MM,
            axes=[
                Axis(name=AxisName.AP, direction=Direction.PA),
                Axis(name=AxisName.ML, direction=Direction.LR),
                Axis(name=AxisName.SI, direction=Direction.SI),
            ],
        )
        assert cs.origin == frontonasal_suture

        cs_roundtrip = CoordinateSystem.model_validate(cs.model_dump())
        assert cs_roundtrip.origin == frontonasal_suture
