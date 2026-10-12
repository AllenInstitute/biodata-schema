# Metadata

[Link to code](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/src/biodata_schema/core/metadata.py)

The `metadata.nd.json` file gathers together the other metadata files and adds information about where the data asset is stored.

`subjects` and `procedures` are lists, including for single-subject assets. Every subject needs exactly one matching `Procedures` object. Use an empty procedures object when no procedures were performed.
