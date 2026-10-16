# Data description

[Link to code](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/src/biodata_schema/core/data_description.py)

The `data_description.json` file tracks administrative information about a data asset, including affiliated researchers/organizations, projects, data modalities, dates of collection, and more.

## Uniqueness

`DataDescription.name` is required and can be any string. It is not generated automatically.

We recommend using the pattern `<subject_name>_<acquisition-start-time>` for single-subject raw data or `<label>_<acquisition-start-time>` for multi-subject raw data. We recommend using ISO format datetimes in the *local time zone* of the acquisition, e.g. `123456_20260101T123500` or `group-5_20260101T123500`.

You can group data assets together using `DataDescription.tags: List[str]`. Tags should be shared across assets within experiments. **Do not repeat information in the tags that already exists elsewhere in the metadata**, for example modalities should never be included in tags.

## Example

```{literalinclude} ../../examples/data_description.py
:language: python
:linenos:
```
