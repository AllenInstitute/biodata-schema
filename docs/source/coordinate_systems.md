# Coordinate systems

The metadata schema supports flexible definitions of coordinate systems. This allows us to store the positions of devices, insertion coordinates, etc, within a standardized system.

Unlike many parts of the metadata schema where fields are just floats or strings, it is critical to understand **how coordinate systems are stored in the schema** to be able to use them properly. There are two rules to be aware of:

1. Each [Instrument](instrument.md), [Acquisition](acquisition.md), and [Procedures](procedures.md) has its own `.global_coordinate_system` field. In most assets, the global coordinate system is the same in all three files.
2. Local to global transforms (i.e. a [Translation](components/coordinates.md#translation), [Rotation](components/coordinates.md#rotation), or [Scale](components/coordinates.md#scale)) that position devices or configurations of devices **must be defined in it's core file's coordinate system**. To help you avoid mistakes, these transform fields are paired with a `.coordinate_system_name` field which must match the name of the global coordinate system defined in the core file.

The top-level coordinate systems in the instrument, acquisition, and procedures are generally defined in *in vivo* space, usually relative to an origin on an animal's skull. Often when targeting coordinates in the brain we plan our experiments in a **standardized atlas** like the mouse common coordinate framework. When you encounter a field that that requires an atlas transform (i.e. a point or vector in an atlas), you'll see that an [Atlas](components/coordinates.md#atlas) will have to be defined alongside that transform. An Atlas library is available in `biodata_schema.components.coordinates.AtlasLibrary` for your convenience.

## CoordinateSystem

A [CoordinateSystem](components/coordinates.md#coordinatesystem) is defined by an [Origin](biodata_models/coordinates.md#origin) and a list of [AxisName](biodata_models/coordinates.md#axisname) and [Direction](biodata_models/coordinates.md#direction) pairs. We recommend naming coordinate systems by combining the origin and positive directions of the axes. For example, `BREGMA_ARI` is a coordinate system with an origin at bregma and three axes pointing anterior, right, and inferior:

```{code} python
CoordinateSystem(
    name="BREGMA_ARI",
    origin=Origin.BREGMA,
    axis_unit=SizeUnit.UM,
    axes=[
        Axis(name=AxisName.AP, direction=Direction.PA),
        Axis(name=AxisName.ML, direction=Direction.LR),
        Axis(name=AxisName.SI, direction=Direction.SI),
    ],
)
```

### Origin

An [Origin](biodata_models/coordinates.md#origin) is a point in space, often relative to the mouse's anatomy but it can also be a point on a device. The Origin defines the (0, 0, 0) coordinate in a coordinate system. Standard anatomical references are positions like Bregma or Lambda

<div align="center">
    <img src="_static/bregma_and_lambda2.png" alt="BREGMA_ARI Coordinate System" width="50%">
</div>

### Axis

Each [Axis](components/coordinates.md#axis) is a combination of an [AxisName](biodata_models/coordinates.md#axisname) and [Direction](biodata_models/coordinates.md#direction).

### Units

Each [CoordinateSystem](components/coordinates.md#coordinatesystem) defines the active units. Units are inherited by the [Translation](components/coordinates.md#translation), [Rotation](components/coordinates.md#rotation), and [Scale](components/coordinates.md#scale) transforms that are applied. The only exception is for rotations, where we ask you to specify for each rotation the units (degrees or radians). 

## Global vs Local Coordinate Systems

The **Global Coordinate System** is the coordinate system in which an experiment is performed. For example, in an instrument these are the three axes and origin that define how devices are positioned while in a procedure these are the origin and axes used to position injections and chronic or acute implants.

We provide a coordinate system builder to help you develop your global coordinate systems, which comes with a variety of sensible defaults. You can export your Python code directly from the builder.

```{raw} html
<p style="margin-bottom:6px">
    <a href="_static/coordinate_system_builder.html?mode=global" target="_blank" rel="noopener">
    Open builder in full screen ↗
  </a>
</p>
<iframe
    src="_static/coordinate_system_builder.html?mode=global"
  style="width:100%; min-width:820px; height:780px; border:1px solid #ddd; border-radius:6px; overflow:auto;"
  scrolling="yes"
  title="AIND Coordinate System Builder">
</iframe>
```

The **Local Coordinate System** is the definition of how a device appears in the global coordinate system when no translation or rotation is applied. Again the builder can help you develop the local coordinate system. Note how in this mode an X, Y, and Z axis appear and need to be aligned to the global axes.

```{raw} html
<p style="margin-bottom:6px">
    <a href="_static/coordinate_system_builder.html?mode=device" target="_blank" rel="noopener">
    Open builder in full screen ↗
  </a>
</p>
<iframe
    src="_static/coordinate_system_builder.html?mode=device"
  style="width:100%; min-width:820px; height:780px; border:1px solid #ddd; border-radius:6px; overflow:auto;"
  scrolling="yes"
  title="AIND Coordinate System Builder">
</iframe>
```

Finally, the **Local to Global Transform(s)** define the actual rotation and position of the device during the experiment. The transforms are local to global because they tell you how a position on the device, e.g. the device origin (0, 0, 0) should be located in the scene. We encourage users to develop chains of transforms because they are more intuitive for humans. For example, the scene below chains together a local rotation to set the probe pitch, a global translation from bregma to the entry coordinate on the brain surface, and finally a local translation on the probe depth axis.

```{raw} html
<p style="margin-bottom:6px">
    <a href="_static/coordinate_system_builder.html?mode=transform&example=true" target="_blank" rel="noopener">
    Open builder in full screen ↗
  </a>
</p>
<iframe
    src="_static/coordinate_system_builder.html?mode=transform&example=true"
  style="width:100%; min-width:820px; height:780px; border:1px solid #ddd; border-radius:6px; overflow:auto;"
  scrolling="yes"
  title="AIND Coordinate System Builder">
</iframe>
```

### Relative Position

For devices where the exact position is not important or is unknown, simply tell us where the device is *roughly* relative to the origin. By combining several [AnatomicalRelative](biodata_models/coordinates.md#anatomicalrelative) directions in a list, for example `[AnatomicalRelative.ANTERIOR, AnatomicalRelative.SUPERIOR]`, etc.

## Measured Coordinates

During a [Surgery](components/subject_procedures.md#surgery) requiring stereotaxic coordinates the surgeon will typically reference the stereotax or insertion device to a known coordinate, almost always Bregma. It's useful at this time to also measure the relative position of other known landmarks, like Lambda. The `Surgery.measured_coordinates` field is intended to store this data, for example for a surgery in the BREGMA_ARI coordinate system and where Lambda is measured 4.1 mm posterior to Bregma you would include:

```{code} python
measured_coordinates = {
    Origin.LAMBDA: Translation(translation=[-4.1, 0, 0])
}
```

The position is *negative* because in BREGMA_ARI the AP axis points positive in the anterior direction and no units are included in the translation itself because they are implied by the coordinate system, see [units](#units) above.

## Interactive Coordinate System Builder

The builder below lets you set up your instrument coordinate system, add a probe (long rectangle) or monitor (very large rectangle), and construct the transform list interactively. The 3D viewport shows a semi-transparent brain mesh with the device rendered in its final position. When you are satisfied, copy the generated Python code from the Export panel.

```{raw} html
<p style="margin-bottom:6px">
    <a href="_static/coordinate_system_builder.html?mode=full" target="_blank" rel="noopener">
    Open builder in full screen ↗
  </a>
</p>
<iframe
    src="_static/coordinate_system_builder.html?mode=full"
  style="width:100%; min-width:820px; height:780px; border:1px solid #ddd; border-radius:6px; overflow:auto;"
  scrolling="yes"
  title="AIND Coordinate System Builder">
</iframe>
```
