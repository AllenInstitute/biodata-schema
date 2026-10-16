# Procedures

[Link to code](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/src/biodata_schema/core/procedures.py)

The `procedures.json` file contains a JSON array of procedure records, one array for each subject. These records describe anything done to a subject or specimen prior to data collection, including surgeries, injections, tissue processing, sectioning, and immunolabeling. They also contain implanted devices and their configurations, for example for chronic insertions.

Implanted device names must be unique across subjects and must not duplicate instrument component names. We recommend prefixing implanted device names with `subject_name`, such as `123456_Probe A`.

## Subject procedure vs. specimen procedure

**Subject** procedures are performed on a live subject (e.g. injections, surgeries, implants, perfusions, etc.) whereas **specimen** procedures are performed on tissue extracted after perfusion (e.g. tissue processing, immunolabeling, sectioning, etc.).

### SpecimenProcedure.specimen_names

`specimen_names` lists the specimens that were used in a procedure. Whole-tissue specimens can use the subject name. There are no specific rules about specimen naming, but we recommend using the `subject_name` as a prefix and adding a unique suffix, such as `<subject_name>_<###>`.

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
| `notes` | `Optional[str]` | Notes  |
