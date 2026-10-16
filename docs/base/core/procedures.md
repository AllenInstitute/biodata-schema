# Procedures

[Link to code](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/src/biodata_schema/core/procedures.py)

The `procedures.json` file contains a JSON array of procedure records, one array for each subject. These records describe anything done to a subject or specimen prior to data collection, including surgeries, injections, tissue processing, sectioning, and immunolabeling. They also contain implanted devices and their configurations, for example for chronic insertions.

## Subject procedure vs. specimen procedure

**Subject** procedures are performed on a live subject (e.g. injections, surgeries, implants, perfusions, etc.) whereas **specimen** procedures are performed on tissue extracted after perfusion (e.g. tissue processing, immunolabeling, sectioning, etc.).

### SpecimenProcedure.specimen_names

`specimen_names` lists the specimens that were used in a procedure. Whole-tissue specimens can use the subject name. There are no specific rules about specimen naming, but we recommend using the `subject_name` as a prefix and adding a unique suffix, such as `<subject_name>_<###>`.

## Examples

- [Generic procedures](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/examples/procedures.py)
- [SmartSPIM procedures](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/examples/aibs_smartspim_procedures.py)
- [Ophys procedures](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/examples/ophys_procedures.py)
