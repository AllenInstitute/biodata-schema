# Processing

[Link to code](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/src/biodata_schema/core/processing.py)

The `processing.json` file captures the data processing and analysis steps that have been carried out – mostly for derived data assets. This tracks what code was used for each step, when it was run, what the input and outputs where, what parameters were set. This includes things like spike sorting, image alignment, cell segmentation. It also includes manual annotation, quality control, and data analysis.

The processing file should be appended to with each subsequent stage of processing or analysis.

## Example

```{literalinclude} ../../examples/processing.py
:language: python
:linenos:
```

## Core file

### Processing

Description of all processes run on data

| Field | Type | Title (Description) |
|-------|------|-------------|
| `data_processes` | List[[DataProcess](processing.md#dataprocess)] | Data processing  |
| `pipelines` | Optional[List[[Code](components/identifiers.md#code)]] | Pipelines (For processing done with pipelines, list the repositories here. Pipelines must use the name field ,and be referenced in the pipeline_name field of a DataProcess.) |
| `notes` | `Optional[str]` | Notes  |
| `dependency_graph` | `Optional[Dict[str, List[str]]]` | Dependency graph (Directed graph of processing step dependencies. Each key is a process name, and the value is a list of process names that are inputs to that process.) |


## Model definitions

### ProcessName

Supported processing operations

| Name | Value |
|------|-------|
| `ANALYSIS` | `Analysis` |
| `COMPRESSION` | `Compression` |
| `DENOISING` | `Denoising` |
| `EPHYS_CURATION` | `Ephys curation` |
| `EPHYS_POSTPROCESSING` | `Ephys postprocessing` |
| `EPHYS_PREPROCESSING` | `Ephys preprocessing` |
| `EPHYS_VISUALIZATION` | `Ephys visualization` |
| `FIDUCIAL_SEGMENTATION` | `Fiducial segmentation` |
| `FILE_FORMAT_CONVERSION` | `File format conversion` |
| `FIX_COLOR_RANGE` | `Fix color range` |
| `FLUORESCENCE_EVENT_DETECTION` | `Fluorescence event detection` |
| `IMAGE_ATLAS_ALIGNMENT` | `Image atlas alignment` |
| `IMAGE_BACKGROUND_SUBTRACTION` | `Image background subtraction` |
| `IMAGE_CELL_CLASSIFICATION` | `Image cell classification` |
| `IMAGE_CELL_QUANTIFICATION` | `Image cell quantification` |
| `IMAGE_CELL_SEGMENTATION` | `Image cell segmentation` |
| `IMAGE_CROSS_IMAGE_ALIGNMENT` | `Image cross-image alignment` |
| `IMAGE_DESTRIPING` | `Image destriping` |
| `IMAGE_FLAT_FIELD_CORRECTION` | `Image flat-field correction` |
| `IMAGE_IMPORTING` | `Image importing` |
| `IMAGE_MIP_VISUALIZATION` | `Image mip visualization` |
| `IMAGE_MULTISCALING` | `Image multiscaling` |
| `IMAGE_RADIAL_CORRECTION` | `Image radial correction` |
| `IMAGE_SPOT_DETECTION` | `Image spot detection` |
| `IMAGE_SPOT_SPECTRAL_UNMIXING` | `Image spot spectral unmixing` |
| `IMAGE_THRESHOLDING` | `Image thresholding` |
| `IMAGE_TILE_ALIGNMENT` | `Image tile alignment` |
| `IMAGE_TILE_FUSING` | `Image tile fusing` |
| `IMAGE_TILE_PROJECTION` | `Image tile projection` |
| `MANUAL_CURATION` | `Manual curation` |
| `MODEL_EVALUATION` | `Model evaluation` |
| `MODEL_TRAINING` | `Model training` |
| `NEURON_SKELETON_PROCESSING` | `Neuron skeleton processing` |
| `NEUROPIL_SUBTRACTION` | `Neuropil subtraction` |
| `OTHER` | `Other` |
| `PIPELINE` | `Pipeline` |
| `SIMULATION` | `Simulation` |
| `SKULL_STRIPPING` | `Skull stripping` |
| `SPATIAL_TIMESERIES_DEMIXING` | `Spatial timeseries demixing` |
| `SPIKE_SORTING` | `Spike sorting` |
| `VIDEO_ROI_CLASSIFICATION` | `Video ROI classification` |
| `VIDEO_ROI_CROSS_SESSION_MATCHING` | `Video ROI cross session matching` |
| `VIDEO_ROI_SEGMENTATION` | `Video ROI segmentation` |
| `VIDEO_ROI_TIMESERIES_EXTRACTION` | `Video ROI timeseries extraction` |
| `VIDEO_MOTION_CORRECTION` | `Video motion correction` |
| `VIDEO_PLANE_DECROSSTALK` | `Video plane decrosstalk` |
| `DF_F_ESTIMATION` | `dF/F estimation` |


### DataProcess

Description of a single processing step

| Field | Type | Title (Description) |
|-------|------|-------------|
| `process_type` | [ProcessName](processing.md#processname) | Process type  |
| `name` | `str` | Name (Unique name of the processing step. If not provided, the type will be used as the name.) |
| `stage` | [ProcessStage](processing.md#processstage) | Processing stage  |
| `code` | [Code](components/identifiers.md#code) | Code (Code used for processing) |
| `experimenters` | `List[str]` | Experimenters (People responsible for processing) |
| `pipeline_name` | `Optional[str]` | Pipeline name (Pipeline names must exist in Processing.pipelines) |
| `start_date_time` | `datetime (timezone-aware)` | Start date time  |
| `end_date_time` | `Optional[datetime (timezone-aware)]` | End date time  |
| `output_path` | `Optional[AssetPath]` | Output path (Path to processing outputs, if stored.) |
| `output_parameters` | `Optional[dict]` | Outputs (Output parameters) |
| `notes` | `Optional[str]` | Notes  |
| `resources` | Optional[[ResourceUsage](processing.md#resourceusage)] | Process resource usage  |


### ProcessStage

Stages of processing

| Name | Value |
|------|-------|
| `PROCESSING` | `Processing` |
| `ANALYSIS` | `Analysis` |


### ResourceTimestamped

Description of resource usage at a moment in time

| Field | Type | Title (Description) |
|-------|------|-------------|
| `timestamp` | `datetime (timezone-aware)` | Timestamp  |
| `usage` | `float` | Usage  |


### ResourceUsage

Description of resources used by a process

| Field | Type | Title (Description) |
|-------|------|-------------|
| `os` | `str` | Operating system  |
| `architecture` | `str` | Architecture  |
| `cpu` | `Optional[str]` | CPU name  |
| `cpu_cores` | `Optional[int]` | CPU cores  |
| `gpu` | `Optional[str]` | GPU name  |
| `system_memory` | `Optional[float]` | System memory  |
| `system_memory_unit` | Optional[[MemoryUnit](biodata_models/units.md#memoryunit)] | System memory unit  |
| `ram` | `Optional[float]` | System RAM  |
| `ram_unit` | Optional[[MemoryUnit](biodata_models/units.md#memoryunit)] | Ram unit  |
| `cpu_usage` | Optional[List[[ResourceTimestamped](processing.md#resourcetimestamped)]] | CPU usage  |
| `gpu_usage` | Optional[List[[ResourceTimestamped](processing.md#resourcetimestamped)]] | GPU usage  |
| `ram_usage` | Optional[List[[ResourceTimestamped](processing.md#resourcetimestamped)]] | RAM usage  |
| `usage_unit` | `str` | Usage unit  |
