# Procedures

[Link to code](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/src/biodata_schema/core/procedures.py)

The `procedures.json` file contains a JSON array of procedure records, one for each subject. These records describe anything done to a subject or specimen prior to data collection, including surgeries, injections, tissue processing, sectioning, and immunolabeling. They also contain implanted devices and their configurations, for example for chronic insertions.

Each `Procedures` object belongs to one subject. `Metadata.procedures` is a list with exactly one object per subject in `Metadata.subjects`. `Metadata.write_standard_files()` writes the whole list to one `procedures.json` file, including for single-subject assets.

## Subject procedure vs. specimen procedure

**Subject** procedures are performed on a live subject (e.g. injections, surgeries, implants, perfusions, etc.) whereas **specimen** procedures are performed on tissue extracted after perfusion (e.g. tissue processing, immunolabeling, sectioning, etc.).

### SpecimenProcedure.specimen_names

After perfusion or death, `specimen_names` lists the specimens used in a procedure. It is a nonempty set of names, written as an array in JSON. Whole-tissue specimens can use the subject name. Sectioned specimens should have a unique suffix, such as `<subject_name>_<###>`. Every specimen name must include the owning subject's name.

## Examples

- [Generic procedures](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/examples/procedures.py)
- [SmartSPIM procedures](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/examples/aibs_smartspim_procedures.py)
- [Ophys procedures](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/examples/ophys_procedures.py)

## Core file

### Procedures

Description of all procedures performed on a subject, including surgeries, injections, and tissue processing

| Field | Type | Title (Description) |
|-------|------|-------------|
| `subject_name` | `str` | Subject name (Unique name for the subject associated with these procedures) |
| `subject_procedures` | List[[Surgery](components/subject_procedures.md#surgery) or [NonSurgicalInjection](components/subject_procedures.md#nonsurgicalinjection) or [TrainingProtocol](components/subject_procedures.md#trainingprotocol) or [WaterRestriction](components/subject_procedures.md#waterrestriction) or [GenericSubjectProcedure](components/subject_procedures.md#genericsubjectprocedure)] | Subject Procedures (Procedures performed on a live subject) |
| `specimen_procedures` | List[[SpecimenProcedure](components/specimen_procedures.md#specimenprocedure)] | Specimen Procedures (Procedures performed on tissue extracted after perfusion) |
| `global_coordinate_system` | Optional[[CoordinateSystem](components/coordinates.md#coordinatesystem)] | Global Coordinate System (Origin and axis definitions for determining the configured position of devices implanted during procedures. Required when coordinates are provided within the Procedures) |
| `notes` | `Optional[str]` | Notes  |
