"""Coordinate systems used by the test suite.

``CoordinateSystemLibrary`` was removed from ``biodata-schema`` in v3.0.0. Projects
are expected to define the coordinate systems they use, as shown here.
"""

from biodata_models.coordinates import AxisName, Direction, Origin
from biodata_models.units import SizeUnit

from biodata_schema.components.coordinates import Axis, CoordinateSystem

BREGMA_ARI = CoordinateSystem(
    name="BREGMA_ARI",
    origin=Origin.BREGMA,
    axis_unit=SizeUnit.MM,
    axes=[
        Axis(name=AxisName.AP, direction=Direction.PA),
        Axis(name=AxisName.ML, direction=Direction.LR),
        Axis(name=AxisName.SI, direction=Direction.SI),
    ],
)
BREGMA_RAS = CoordinateSystem(
    name="BREGMA_RAS",
    origin=Origin.BREGMA,
    axis_unit=SizeUnit.MM,
    axes=[
        Axis(name=AxisName.ML, direction=Direction.LR),
        Axis(name=AxisName.AP, direction=Direction.PA),
        Axis(name=AxisName.SI, direction=Direction.IS),
    ],
)
MPM_MANIP_RFB = CoordinateSystem(
    name="MPM_MANIP_RFB",
    origin=Origin.TIP,
    axis_unit=SizeUnit.MM,
    axes=[
        Axis(name=AxisName.X, direction=Direction.LR),
        Axis(name=AxisName.Y, direction=Direction.BF),
        Axis(name=AxisName.Z, direction=Direction.UD),
    ],
)
SIPE_MONITOR_RTF = CoordinateSystem(
    name="SIPE_MONITOR_RTF",
    origin=Origin.FRONT_CENTER,
    axis_unit=SizeUnit.MM,
    axes=[
        Axis(name=AxisName.X, direction=Direction.LR),
        Axis(name=AxisName.Y, direction=Direction.DU),
        Axis(name=AxisName.Z, direction=Direction.BF),
    ],
)
SPIM_RPI = CoordinateSystem(
    name="SPIM_RPI",
    origin=Origin.ORIGIN,
    axis_unit=SizeUnit.MM,
    axes=[
        Axis(name=AxisName.X, direction=Direction.LR),
        Axis(name=AxisName.Y, direction=Direction.AP),
        Axis(name=AxisName.Z, direction=Direction.SI),
    ],
)
SPIM_IJK = CoordinateSystem(
    name="SPIM_IJK",
    origin=Origin.ORIGIN,
    axis_unit=SizeUnit.PX,
    axes=[
        Axis(name=AxisName.X, direction=Direction.POS),
        Axis(name=AxisName.Y, direction=Direction.POS),
        Axis(name=AxisName.Z, direction=Direction.POS),
    ],
)
MRI_LPS = CoordinateSystem(
    name="MRI_LPS",
    origin=Origin.ORIGIN,
    axis_unit=SizeUnit.MM,
    axes=[
        Axis(name=AxisName.X, direction=Direction.RL),
        Axis(name=AxisName.Y, direction=Direction.AP),
        Axis(name=AxisName.Z, direction=Direction.IS),
    ],
)
IMAGE_XYZ = CoordinateSystem(
    name="IMAGE_XYZ",
    origin=Origin.ORIGIN,
    axis_unit=SizeUnit.PX,
    axes=[
        Axis(name=AxisName.X, direction=Direction.POS),
        Axis(name=AxisName.Y, direction=Direction.POS),
        Axis(name=AxisName.Z, direction=Direction.POS),
    ],
)
