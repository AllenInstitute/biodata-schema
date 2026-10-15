# Data description

[Link to code](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/src/biodata_schema/core/data_description.py)

The `data_description.json` file tracks administrative information about a data asset, including affiliated researchers/organizations, projects, data modalities, dates of collection, and more.

## Uniqueness

`DataDescription.name` can be any string. If omitted for single-subject raw data, it is generated as `<subject_name>_<creation_time>`. For multi-subject raw data, supply a name; we suggest `<label>_<acquisition-start-time>`, for example `batch-17_20221012T232311+0000`.

You can group data assets together using `DataDescription.tags: List[str]`. Tags should be shared across assets within experiments. **Do not repeat information in the tags that already exists elsewhere in the metadata**, for example modalities should never be included in tags.

## Example

```{literalinclude} ../../examples/data_description.py
:language: python
:linenos:
```
