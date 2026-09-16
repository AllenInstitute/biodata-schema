# Coordinates

## Model definitions

### Affine

Definition of an NxN+1 affine transform matrix

| Field | Type | Title (Description) |
|-------|------|-------------|
| `affine_transform` | `List[List[float]]` | Affine transform matrix  |


### Atlas

Definition an atlas

| Field | Type | Title (Description) |
|-------|------|-------------|
| `name` | [AtlasName](../biodata_models/atlas.md#atlasname) | Atlas name  |
| `version` | `str` | Atlas version  |
| `size` | `List[float]` | Size  |
| `size_unit` | [SizeUnit](../biodata_models/units.md#sizeunit) | Size unit  |
| `resolution` | `List[float]` | Resolution  |
| `resolution_unit` | [SizeUnit](../biodata_models/units.md#sizeunit) | Resolution unit  |
| `origin` | [MouseAnatomyModel](../biodata_models/external.md#mouseanatomymodel) | Origin (Defines the position of (0,0,0) in the coordinate system) |
| `axes` | List[[Axis](#axis)] | Axis names (Axis names and directions) |
| `axis_unit` | [SizeUnit](../biodata_models/units.md#sizeunit) | Size unit  |
| `handedness` | Optional[[Handedness](#handedness)] | Handedness (Whether the coordinate system is right-handed or left-handed) |


### AtlasCoordinate

A point in an Atlas

| Field | Type | Title (Description) |
|-------|------|-------------|
| `coordinate_system` | [Atlas](#atlas) | Atlas  |
| `translation` | `List[float]` | Translation parameters  |
| `reference_coordinate_system` | [ReferenceCoordinateSystem](#referencecoordinatesystem) | Reference coordinate system (Whether to translate on the global or local coordinate system axes) |


### Axis

Linked direction and axis

| Field | Type | Title (Description) |
|-------|------|-------------|
| `name` | [AxisName](../biodata_models/coordinates.md#axisname) | Axis name (Note: axis names do not influence order or orientation) |
| `direction` | [Direction](../biodata_models/coordinates.md#direction) | Direction (Direction of positive values along the axis) |


### CoordinateSystem

Definition of a coordinate system

| Field | Type | Title (Description) |
|-------|------|-------------|
| `name` | `str` | Name (Convention is to use <Origin>_<POS_X_DIR><POS_Y_DIR><POS_Z_DIR> etc) |
| `origin` | [MouseAnatomyModel](../biodata_models/external.md#mouseanatomymodel) | Origin (Defines the position of (0,0,0) in the coordinate system) |
| `axes` | List[[Axis](#axis)] | Axis names (Axis names and directions) |
| `axis_unit` | [SizeUnit](../biodata_models/units.md#sizeunit) | Size unit  |
| `handedness` | Optional[[Handedness](#handedness)] | Handedness (Whether the coordinate system is right-handed or left-handed) |


### Handedness

Coordinate system handedness

| Name | Value |
|------|-------|
| `RIGHT` | `right` |
| `LEFT` | `left` |


### NonlinearTransform

Definition of a nonlinear transform

| Field | Type | Title (Description) |
|-------|------|-------------|
| `path` | `AssetPath` | Path to nonlinear transform file (Relative path from metadata json to file) |


### ReferenceCoordinateSystem

Reference coordinate system for applying transforms

| Name | Value |
|------|-------|
| `GLOBAL` | `global` |
| `LOCAL` | `local` |


### Rotation

Rotation

Rotations should be applied as Euler angles in the specified axis order.

| Field | Type | Title (Description) |
|-------|------|-------------|
| `angles` | `List[float]` | Angles (Right-hand rule, positive angles rotate CCW) |
| `angles_unit` | [AngleUnit](../biodata_models/units.md#angleunit) | Angle unit  |
| `axis_order` | `str` | Axis order (Order of rotation axes as a string (e.g. 'xyz', 'zyx'). Must match the length of angles.) |
| `reference_coordinate_system` | [ReferenceCoordinateSystem](#referencecoordinatesystem) | Reference coordinate system (Whether to rotate around the global or local coordinate system axes) |
| `rotation_direction` | [RotationDirection](#rotationdirection) | Rotation direction (Right-hand rule: positive angles rotate CCW when looking toward the origin from the positive axis) |
| `pivot` | [ReferenceCoordinateSystem](#referencecoordinatesystem) | Rotation pivot (Whether to rotate around the global or local coordinate system origin) |


### RotationDirection

Rotation direction convention

| Name | Value |
|------|-------|
| `RIGHT_HAND` | `right_hand` |
| `LEFT_HAND` | `left_hand` |


### Scale

Scale

| Field | Type | Title (Description) |
|-------|------|-------------|
| `scale` | `List[float]` | Scale parameters  |
| `pivot` | [ReferenceCoordinateSystem](#referencecoordinatesystem) | Scale pivot (Whether to scale around the global or local coordinate system origin) |


### Translation

Translation

| Field | Type | Title (Description) |
|-------|------|-------------|
| `translation` | `List[float]` | Translation parameters  |
| `reference_coordinate_system` | [ReferenceCoordinateSystem](#referencecoordinatesystem) | Reference coordinate system (Whether to translate on the global or local coordinate system axes) |


