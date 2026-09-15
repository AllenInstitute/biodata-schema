# biodata-schema v3.0.0 migration guide

Version 3 removes fields, classes, and methods that version 2 marked as deprecated. Version
2 accepted these values and issued warnings. Version 3 rejects them with Pydantic's
`ValidationError` (`extra_forbidden`) because schema models reject extra fields.

The `aind-metadata-upgrader` package handles automatic metadata upgrades separately.

## Contents

1. [`coordinate_system` renamed to `global_`/`local_coordinate_system`](#1-coordinate_system-renamed)
2. [`Section` coordinate fields moved to `PlanarSection`](#2-section-coordinate-fields)
3. [Device fields replaced by `shape`](#3-device-size-fields-replaced-by-shape)
4. [`DAQChannel.channel_index`](#4-daqchannelchannel_index)
5. [`BreedingInfo.breeding_group`](#5-breedinginfobreeding_group)
6. [Olfactory stimulus classes](#6-olfactory-stimulus-classes)
7. [`DataDescription.from_*` classmethods](#7-datadescriptionfrom_-classmethods)
8. [`QCMetric.tags` list form](#8-qcmetrictags-list-form)
9. [`CoordinateSystemLibrary` removed](#9-coordinatesystemlibrary-removed)
10. [Removed helper](#10-removed-helper)
11. [Warnings now raise errors](#11-warnings-promoted-to-errors)
12. [Warnings that remain](#12-validators-still-emitting-warnings)

---

## 1. `coordinate_system` renamed

Version 2 split `coordinate_system` into `global_coordinate_system` for top-level and
container models, and `local_coordinate_system` for device and config models. Version 3
removes the old field and the validators that copied its value forward.

Please see the [coordinate systems page on the documentation](https://biodata-schema.readthedocs.io/en/latest/coordinate_systems.html) for more details about coordinate systems specifically.

### Use `global_coordinate_system` for these models

| Model | Module |
| --- | --- |
| `Acquisition` | `core/acquisition.py` |
| `Procedures` | `core/procedures.py` |
| `Instrument` | `core/instrument.py` |
| `Surgery` | `components/subject_procedures.py` |
| `PlanarSectioning` | `components/specimen_procedures.py` |

### Use `local_coordinate_system` for these models

| Model | Module |
| --- | --- |
| `DevicePosition` and subclasses such as `Monitor` | `components/devices.py` |
| `ImagingConfig` | `components/configs.py` |
| `LickSpoutConfig` | `components/configs.py` |
| `AirPuffConfig` | `components/configs.py` |
| `ManipulatorConfig` | `components/configs.py` |
| `ProbeConfig` | `components/configs.py` |

**Before**

```python
Acquisition(..., coordinate_system=CoordinateSystemLibrary.BREGMA_ARI)
ProbeConfig(..., coordinate_system=CoordinateSystemLibrary.BREGMA_ARI)
```

**After**

```python
Acquisition(..., global_coordinate_system=CoordinateSystemLibrary.BREGMA_ARI)
ProbeConfig(..., local_coordinate_system=CoordinateSystemLibrary.BREGMA_ARI)
```

Keep `AtlasCoordinate.coordinate_system`. It stores an `Atlas` and does not use the renamed
fields.

Set `Instrument.global_coordinate_system`, `ManipulatorConfig.local_coordinate_system`, and
`ProbeConfig.local_coordinate_system` explicitly.

## 2. `Section` coordinate fields

Use `PlanarSection` for sections with coordinate data. Version 3 removes these fields from
`Section` (`components/specimen_procedures.py`):

- `coordinate_system_name`
- `start_coordinate`
- `end_coordinate`
- `thickness`
- `thickness_unit`
- `partial_slice`

Version 3 also removes the `deprecated_coordinate_fields` validator.

**Before**

```python
Section(output_specimen_id="123456_001", coordinate_system_name="BREGMA_ARI", thickness=0.1)
```

**After**

```python
PlanarSection(
    output_specimen_id="123456_001",
    coordinate_system_name="BREGMA_ARI",
    start_coordinate=Translation(translation=[0.3, 0, 0]),
    thickness=0.1,
)
```

`PlanarSection` requires `coordinate_system_name` and `start_coordinate`.

## 3. Device size fields replaced by `shape`

Use a geometry object instead of the `Scale`-based `size`/`size_unit` pair on `Enclosure` and
`Arena` (`components/devices.py`).

| Model | Remove | Use |
| --- | --- | --- |
| `Enclosure` | `size`, `size_unit` | `shape: Rectangle \| Circle` |
| `Arena` | `size`, `size_unit` | `shape: Circle \| Rectangle` |

Both models require `shape`.

**Before**

```python
Arena(..., size=Scale(scale=[30, 30, 20]), size_unit=SizeUnit.CM)
```

**After**

```python
Arena(..., shape=Rectangle(width=30, height=30, size_unit=SizeUnit.CM))
```

Keep the other `size_unit` fields in the schema, including those on `Monitor`, `Rectangle`,
and `Wheel`.

## 4. `DAQChannel.channel_index`

Remove `DAQChannel.channel_index` and its `deprecated_channel_index` validator from
`components/devices.py`. Use `DAQChannel.port` instead.

**Before**

```python
DAQChannel(channel_name="ch", channel_type=DaqChannelType.DI, channel_index=1)
```

**After**

```python
DAQChannel(channel_name="ch", channel_type=DaqChannelType.DI, port=1)
```

Keep `OlfactometerChannel.channel_index` and `OlfactometerChannelInfo.channel_index`.
Those fields serve different purposes.

## 5. `BreedingInfo.breeding_group`

Remove `BreedingInfo.breeding_group` and the `warn_breeding_group_deprecated` validator from
`components/subjects.py`.

## 6. Olfactory stimulus classes

Version 3 removes these classes from `components/stimulus.py`:

| Remove | Use |
| --- | --- |
| `OlfactometerChannelConfig` | `OlfactometerChannelInfo` in `components/configs.py` |
| `OlfactoryStimulation` | `StimulusEpoch.stimulus_name` and `OlfactometerConfig` in `components/configs.py` |

Remove uses of `OlfactoryStimulation.channels` and `OlfactoryStimulation.notes` too.

## 7. `DataDescription.from_*` classmethods

Replace the three `DataDescription` derivation classmethods from `core/data_description.py`
with the functions in `biodata_schema.utils.inheritance`:

| Remove | Use |
| --- | --- |
| `DataDescription.from_raw(...)` | `derive_data_description_from_raw(...)` |
| `DataDescription.from_derived(...)` | `derive_data_description_from_derived(...)` |
| `DataDescription.from_data_description(...)` | `derive_data_description(...)` |

The signatures stay the same. Change the import and function name:

```python
from biodata_schema.utils.inheritance import (
    derive_data_description,
    derive_data_description_from_derived,
    derive_data_description_from_raw,
)

derived = derive_data_description_from_raw(dd, "spikesort-ks25", creation_time=dt)
```

Or use the `Metadata.from_metadata` helpers.

## 8. `QCMetric.tags` list form

Use a dictionary for `QCMetric.tags`. Version 3 removes the `fix_tag_lists` validator from
`core/quality_control.py`, so list-valued `tags` now fail validation.

**Before (v2.2.x JSON)**

```json
{"tags": ["Probe A", "Drift"]}
```

**After**

```json
{"tags": {"probe": "Probe A", "issue": "Drift"}}
```

### Related removal: `fix_default_grouping_list`

Version 3 removes `QualityControl.fix_default_grouping_list`. Pass `default_grouping` as a
list of tuples of strings.

## 9. `CoordinateSystemLibrary` removed

Version 3 removes `biodata_schema.components.coordinates.CoordinateSystemLibrary` and its
fixed set of named `CoordinateSystem` constants, including `BREGMA_ARI`, `BREGMA_RAS`,
`BREGMA_ARID`, `BREGMA_RASD`, `ARENA_RBT`, `SIPE_CAMERA_RBF`, `SIPE_MONITOR_RTF`,
`SIPE_SPEAKER_LTF`, `MPM_MANIP_RFB`, `PINPOINT_PROBE_RSAB`, `SPIM_RPI`, `SPIM_IJK`,
`MRI_LPS`, and `IMAGE_XYZ`.

Define the coordinate systems for your rig or project in your own module. Import them where
you need them. `CoordinateSystem`, `Axis`, `Origin`, `AxisName`, and `Direction` still work.

**Before**

```python
from biodata_schema.components.coordinates import CoordinateSystemLibrary

Acquisition(..., global_coordinate_system=CoordinateSystemLibrary.BREGMA_ARI)
```

**After**

```python
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

Acquisition(..., global_coordinate_system=BREGMA_ARI)
```

For an old definition, see `components/coordinates.py` at the v2.9.0 tag. The examples in
`examples/` also define coordinate systems inline.

Keep using `AtlasLibrary`; version 3 still ships it.

## 10. Removed helper

Version 3 removes `biodata_schema.base.migrate_deprecated_coordinate_system`. No
replacement exists because the helper only copied the old coordinate field forward.

`recursive_get_all_names` in `utils/validators.py` now handles the fields directly and no
longer skips `coordinate_system`.

### The `transforms` extra is gone

Do not use `pip install biodata-schema[transforms]`. Version 3 removes that extra and its
`scipy` dependency.

## 11. Warnings now raise errors

Version 3 turns these five v2 warnings into validation errors.

### `Code` requires `commit_hash` or `version`

Set at least one of these fields. `Code._ensure_commit_hash_or_version` in
`components/identifiers.py` now enforces the requirement.

```python
Code(url="https://github.com/AllenNeuralDynamics/example")  # ValidationError
Code(url="https://github.com/AllenNeuralDynamics/example", version="0.0.1")  # ok
```

### Wrap `Injection` procedures

`Procedures.reject_injections` in `core/procedures.py` now rejects bare `Injection` objects.
Wrap each injection in a `Surgery` or `NonSurgicalInjection`:

```python
Procedures(subject_id="12345", subject_procedures=[Injection(...)])  # ValidationError
Procedures(subject_id="12345", subject_procedures=[Surgery(procedures=[Injection(...)])])  # ok
```

### Give `Instrument` components unique names

`Instrument.validate_unique_component_names` in `core/instrument.py` now raises an error.
Give unique names to:

- entries in `Instrument.components`
- different objects anywhere in the component tree

You can reference one shared object from multiple places. The validator compares object
values before it reports a duplicate name.

The validator only checks names on `Device` and `Assembly` objects and their subclasses.
Names on coordinate systems, software, and other non-device/non-assembly objects are
ignored. You can reuse a package across devices, and a software name can match a device
name. For example, this remains valid:

```python
Software(name="Bonsai", version="2.5")
```

Keep device names unique because `Connection.source_device` and `Connection.target_device`
find components by name.

#### Renamed devices in `multiplane_ophys_instrument`

Keep each `CameraAssembly` name and give its inner camera a distinct name:

| Assembly name | Inner camera name |
| --- | --- |
| `Behavior Camera` | `Behavior Camera Detector` |
| `Eye Camera` | `Eye Camera Detector` |
| `Face Camera` | `Face Camera Detector` |

Apply the same rule when an assembly and its inner camera share a name: keep the assembly
name because connections use it, and rename the inner device.

### Specify monitor units

Set `contrast_unit` or `brightness_unit` whenever you set the matching value. Version 3
removed `Monitor.add_units_if_needed`, which filled in `percent` automatically.

```python
Monitor(..., contrast=50)  # ValidationError
Monitor(..., contrast=50, contrast_unit=UnitlessUnit.PERCENT)  # ok
```

### Add the `calibration` tag yourself

When a `CalibrationObject` subject lacks the `"calibration"` tag,
`Metadata.validate_calibration_object_tags` still warns. It no longer adds the tag to
`data_description.tags`:

```python
DataDescription(..., tags=["calibration"])
```

## 12. Warnings that remain

Version 3 removes all `DeprecationWarning`s. The following validators and helpers still emit
warnings.

### `UserWarning`, visible through `warnings` and `pytest.warns`

| Location | Validator | Fires when | Reason |
| --- | --- | --- | --- |
| `core/metadata.py` | `Metadata.validate_expected_files_by_modality` | A required file is missing | Metadata can arrive in pieces. |
| `core/metadata.py` | `Metadata.validate_calibration_object_tags` | A `CalibrationObject` subject lacks the `"calibration"` tag | The check provides advice only. |
| `core/metadata.py` | `Metadata.validate_training_protocol_references` | `StimulusEpoch.training_protocol_name` has no match in `Procedures` | The reference matters only when both files exist. |
| `core/metadata.py` | `Metadata.validate_data_description_name_time_consistency` | The name's creation time differs greatly from `acquisition_end_time` | The check uses a heuristic. |
| `core/processing.py` | `Processing.__add__` | Merged objects share process names | The merge renames the processes. |
| `base.py` | `_GenericModel.validate_fieldnames` | A field name contains `.` or `$` | The check covers user-supplied `GenericModel` data. |

### `logger.warning`, log output only

| Location | Validator | Fires when | Reason |
| --- | --- | --- | --- |
| `core/metadata.py` | `Metadata.validate_core_fields` | A core field fails its own validation | The helper can wrap partially invalid cores. |
| `core/acquisition.py` | `DataStream.__add__` | Two merged data streams disagree | The message describes a merge condition. |
| `utils/validators.py` | `recursive_check_paths` | An `AssetPath` does not exist on disk | The working directory controls path resolution. |
| `base.py` | `DataCoreModel.write_standard_file` | A serialized file exceeds `MAX_FILE_SIZE` (500 KB) | The write path warns instead of discarding data. |

### `DEPTH` axes

Version 3 accepts `DEPTH` axes without warning. Projects can define their own coordinate
systems, and the package no longer supplies a `DEPTH`-based system through
`CoordinateSystemLibrary`.
