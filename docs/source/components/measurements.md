# Measurements

## Model definitions

### Calibration

Generic calibration class

| Field | Type | Title (Description) |
|-------|------|-------------|
| `calibration_date` | `datetime (timezone-aware)` | Date and time of calibration  |
| `description` | `str` | Description (Brief description of what is being calibrated) |
| `measured_at` | `Optional[str]` | Measurement location  |
| `input` | `List[float or str]` | Inputs (Calibration input) |
| `input_unit` | [SizeUnit](../biodata_models/units.md#sizeunit) or [MassUnit](../biodata_models/units.md#massunit) or [FrequencyUnit](../biodata_models/units.md#frequencyunit) or [SpeedUnit](../biodata_models/units.md#speedunit) or [VolumeUnit](../biodata_models/units.md#volumeunit) or [AngleUnit](../biodata_models/units.md#angleunit) or [TimeUnit](../biodata_models/units.md#timeunit) or [PowerUnit](../biodata_models/units.md#powerunit) or [CurrentUnit](../biodata_models/units.md#currentunit) or [ConcentrationUnit](../biodata_models/units.md#concentrationunit) or [TemperatureUnit](../biodata_models/units.md#temperatureunit) or [SoundIntensityUnit](../biodata_models/units.md#soundintensityunit) or [VoltageUnit](../biodata_models/units.md#voltageunit) or [MemoryUnit](../biodata_models/units.md#memoryunit) or [UnitlessUnit](../biodata_models/units.md#unitlessunit) or [MagneticFieldUnit](../biodata_models/units.md#magneticfieldunit) or [PressureUnit](../biodata_models/units.md#pressureunit) or {TorqueUnit} | Input unit  |
| `repeats` | `Optional[int]` | Number of repeats (If each input was repeated multiple times, provide the number of repeats) |
| `output` | `List[float or str]` | Outputs (Calibration output (provide the average if repeated)) |
| `output_unit` | [SizeUnit](../biodata_models/units.md#sizeunit) or [MassUnit](../biodata_models/units.md#massunit) or [FrequencyUnit](../biodata_models/units.md#frequencyunit) or [SpeedUnit](../biodata_models/units.md#speedunit) or [VolumeUnit](../biodata_models/units.md#volumeunit) or [AngleUnit](../biodata_models/units.md#angleunit) or [TimeUnit](../biodata_models/units.md#timeunit) or [PowerUnit](../biodata_models/units.md#powerunit) or [CurrentUnit](../biodata_models/units.md#currentunit) or [ConcentrationUnit](../biodata_models/units.md#concentrationunit) or [TemperatureUnit](../biodata_models/units.md#temperatureunit) or [SoundIntensityUnit](../biodata_models/units.md#soundintensityunit) or [VoltageUnit](../biodata_models/units.md#voltageunit) or [MemoryUnit](../biodata_models/units.md#memoryunit) or [UnitlessUnit](../biodata_models/units.md#unitlessunit) or [MagneticFieldUnit](../biodata_models/units.md#magneticfieldunit) or [PressureUnit](../biodata_models/units.md#pressureunit) or {TorqueUnit} | Output unit  |
| `fit` | Optional[[CalibrationFit](#calibrationfit)] | Fit (Fit equation for the calibration data used during data acquisition) |
| `notes` | `Optional[str]` | Notes  |
| `protocol_id` | `Optional[str]` | Protocol ID (DOI for protocols.io) |
| `device_name` | `str` | Device name (Must match a device defined in the instrument.json) |


### CalibrationFit

Fit equation for calibration data

| Field | Type | Title (Description) |
|-------|------|-------------|
| `fit_type` | [FitType](#fittype) | Fit type  |
| `fit_parameters` | `Optional[dict]` | Fit parameters (Parameters of the fit equation, e.g. slope and intercept for linear fit) |


### FitType

Type of fit for calibration data

| Name | Value |
|------|-------|
| `LINEAR_INTERPOLATION` | `linear_interpolation` |
| `LINEAR` | `linear` |
| `OTHER` | `other` |


### Maintenance

Generic maintenance class

| Field | Type | Title (Description) |
|-------|------|-------------|
| `maintenance_date` | `datetime (timezone-aware)` | Date and time of maintenance  |
| `description` | `str` | Description (Description on maintenance procedure) |
| `reagents` | Optional[List[[Reagent](reagent.md#reagent)]] | Reagents  |
| `notes` | `Optional[str]` | Notes  |
| `protocol_id` | `Optional[str]` | Protocol ID (DOI for protocols.io) |
| `device_name` | `str` | Device name (Must match a device defined in the instrument.json) |


### PowerCalibration

Calibration of a device that outputs power based on input strength

| Field | Type | Title (Description) |
|-------|------|-------------|
| `input` | `List[float]` | Input (Power, voltage, or percentage input strength) |
| `input_unit` | `biodata_models.units.PowerUnit or biodata_models.units.VoltageUnit` | Input unit  |
| `output` | `List[float]` | Output (Power output (provide the average if repeated)) |
| `output_unit` | [PowerUnit](../biodata_models/units.md#powerunit) | Output unit  |
| `description` | `"Power measured for various power or percentage input strengths"` |   |
| `calibration_date` | `datetime (timezone-aware)` | Date and time of calibration  |
| `measured_at` | `Optional[str]` | Measurement location  |
| `repeats` | `Optional[int]` | Number of repeats (If each input was repeated multiple times, provide the number of repeats) |
| `fit` | Optional[[CalibrationFit](#calibrationfit)] | Fit (Fit equation for the calibration data used during data acquisition) |
| `notes` | `Optional[str]` | Notes  |
| `protocol_id` | `Optional[str]` | Protocol ID (DOI for protocols.io) |
| `device_name` | `str` | Device name (Must match a device defined in the instrument.json) |


### VolumeCalibration

Calibration of a liquid delivery device based on solenoid/valve opening times

| Field | Type | Title (Description) |
|-------|------|-------------|
| `input` | `List[float]` | Input times (Length of time solenoid/valve is open) |
| `input_unit` | [TimeUnit](../biodata_models/units.md#timeunit) | Input unit  |
| `repeats` | `Optional[int]` | Number of repeats (If each input was repeated multiple times, provide the number of repeats) |
| `output` | `List[float]` | Output (Volume output (provide the average if repeated)) |
| `output_unit` | [VolumeUnit](../biodata_models/units.md#volumeunit) | Output unit  |
| `description` | `"Volume measured for various solenoid opening times"` |   |
| `calibration_date` | `datetime (timezone-aware)` | Date and time of calibration  |
| `measured_at` | `Optional[str]` | Measurement location  |
| `fit` | Optional[[CalibrationFit](#calibrationfit)] | Fit (Fit equation for the calibration data used during data acquisition) |
| `notes` | `Optional[str]` | Notes  |
| `protocol_id` | `Optional[str]` | Protocol ID (DOI for protocols.io) |
| `device_name` | `str` | Device name (Must match a device defined in the instrument.json) |


