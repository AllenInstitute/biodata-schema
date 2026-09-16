"""Classes to define device positions, orientations, and coordinates"""

from enum import Enum
from typing import List, Optional

from biodata_models.atlas import AtlasName
from biodata_models.coordinates import AxisName, Direction, Origin
from biodata_models.mouse_anatomy import MouseAnatomyModel
from biodata_models.units import AngleUnit, SizeUnit
from pydantic import Field, field_validator

from biodata_schema.base import DataModel, DiscriminatedList
from biodata_schema.components.wrappers import AssetPath


class ReferenceCoordinateSystem(str, Enum):
    """Reference coordinate system for applying transforms"""

    GLOBAL = "global"
    LOCAL = "local"


class RotationDirection(str, Enum):
    """Rotation direction convention"""

    RIGHT_HAND = "right_hand"
    LEFT_HAND = "left_hand"


class Handedness(str, Enum):
    """Coordinate system handedness"""

    RIGHT = "right"
    LEFT = "left"


class Axis(DataModel):
    """Linked direction and axis"""

    name: AxisName = Field(..., title="Axis name", description="Note: axis names do not influence order or orientation")
    direction: Direction = Field(
        ...,
        title="Direction",
        description="Direction of positive values along the axis",
    )


class Scale(DataModel):
    """Scale"""

    scale: List[float] = Field(..., title="Scale parameters")
    pivot: ReferenceCoordinateSystem = Field(
        default=ReferenceCoordinateSystem.GLOBAL,
        title="Scale pivot",
        description="Whether to scale around the global or local coordinate system origin",
    )


class Translation(DataModel):
    """Translation"""

    translation: List[float] = Field(..., title="Translation parameters")
    reference_coordinate_system: ReferenceCoordinateSystem = Field(
        default=ReferenceCoordinateSystem.GLOBAL,
        title="Reference coordinate system",
        description="Whether to translate on the global or local coordinate system axes",
    )


class Rotation(DataModel):
    """Rotation

    Rotations should be applied as Euler angles in the specified axis order.
    """

    angles: List[float] = Field(..., title="Angles", description="Right-hand rule, positive angles rotate CCW")
    angles_unit: AngleUnit = Field(default=AngleUnit.DEG, title="Angle unit")
    axis_order: str = Field(
        default="xyz",
        title="Axis order",
        description="Order of rotation axes as a string (e.g. 'xyz', 'zyx'). Must match the length of angles.",
    )
    reference_coordinate_system: ReferenceCoordinateSystem = Field(
        default=ReferenceCoordinateSystem.GLOBAL,
        title="Reference coordinate system",
        description="Whether to rotate around the global or local coordinate system axes",
    )
    rotation_direction: RotationDirection = Field(
        default=RotationDirection.RIGHT_HAND,
        title="Rotation direction",
        description="Right-hand rule: positive angles rotate CCW when looking toward the origin from the positive axis",
    )
    pivot: ReferenceCoordinateSystem = Field(
        default=ReferenceCoordinateSystem.GLOBAL,
        title="Rotation pivot",
        description="Whether to rotate around the global or local coordinate system origin",
    )

    @field_validator("axis_order")
    @classmethod
    def validate_axis_order(cls, v: str) -> str:
        """Validate that axis_order only contains valid axis characters and is lowercase"""
        valid_chars = set("xyzXYZ")
        if not v or not all(c in valid_chars for c in v):
            raise ValueError(f"axis_order must only contain axis characters (x, y, z), got '{v}'")
        return v.lower()


class Affine(DataModel):
    """Definition of an NxN+1 affine transform matrix"""

    affine_transform: List[List[float]] = Field(
        ...,
        title="Affine transform matrix",
    )


class NonlinearTransform(DataModel):
    """Definition of a nonlinear transform"""

    path: AssetPath = Field(
        ..., title="Path to nonlinear transform file", description="Relative path from metadata json to file"
    )


TRANSFORM_TYPES = DiscriminatedList[Translation | Rotation | Scale | Affine]
TRANSFORM_TYPES_NONLINEAR = DiscriminatedList[Translation | Rotation | Scale | Affine | NonlinearTransform]


class CoordinateSystem(DataModel):
    """Definition of a coordinate system"""

    name: str = Field(
        ..., title="Name", description="Convention is to use <Origin>_<POS_X_DIR><POS_Y_DIR><POS_Z_DIR> etc"
    )

    origin: Origin | MouseAnatomyModel = Field(
        ..., title="Origin", description="Defines the position of (0,0,0) in the coordinate system"
    )
    axes: List[Axis] = Field(..., title="Axis names", description="Axis names and directions")
    axis_unit: SizeUnit = Field(..., title="Size unit")
    handedness: Optional[Handedness] = Field(
        default=None,
        title="Handedness",
        description="Whether the coordinate system is right-handed or left-handed",
    )


class Atlas(CoordinateSystem):
    """Definition an atlas"""

    name: AtlasName = Field(..., title="Atlas name")
    version: str = Field(..., title="Atlas version")
    size: List[float] = Field(..., title="Size")
    size_unit: SizeUnit = Field(default=SizeUnit.PX, title="Size unit")
    resolution: List[float] = Field(..., title="Resolution")
    resolution_unit: SizeUnit = Field(..., title="Resolution unit")


class AtlasCoordinate(Translation):
    """A point in an Atlas"""

    coordinate_system: Atlas = Field(..., title="Atlas")


class AtlasLibrary:
    """Library of common atlases"""

    CCFv3_10um = Atlas(
        name=AtlasName.CCF,
        version="3",
        origin=Origin.ORIGIN,
        axis_unit=SizeUnit.UM,
        axes=[
            Axis(name=AxisName.AP, direction=Direction.AP),
            Axis(name=AxisName.SI, direction=Direction.SI),
            Axis(name=AxisName.ML, direction=Direction.LR),
        ],
        size=[1320, 800, 1140],
        resolution=[10, 10, 10],
        resolution_unit=SizeUnit.UM,
    )

    CCFv3_25um = Atlas(
        name=AtlasName.CCF,
        version="3",
        origin=Origin.ORIGIN,
        axis_unit=SizeUnit.UM,
        axes=[
            Axis(name=AxisName.AP, direction=Direction.AP),
            Axis(name=AxisName.SI, direction=Direction.SI),
            Axis(name=AxisName.ML, direction=Direction.LR),
        ],
        size=[528, 320, 456],
        resolution=[25, 25, 25],
        resolution_unit=SizeUnit.UM,
    )
