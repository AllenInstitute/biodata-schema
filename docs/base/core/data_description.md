# Data description

[Link to code](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/src/biodata_schema/core/data_description.py)

The `data_description.json` file tracks administrative information about a data asset, including affiliated researchers/organizations, projects, data modalities, dates of collection, and more.

## Uniqueness

Every data asset is identified by its `DataDescription.name`. New names combine an asset label with `creation_time`. For single-subject raw data, the label defaults to the subject name. Raw assets with multiple subjects require an explicit name, such as a batch label followed by the timestamp. The subjects are listed in `subject_names`; they are not inferred from the label.

You can group data assets together using `DataDescription.tags: List[str]`. Tags should be shared across assets within experiments. **Do not repeat information in the tags that already exists elsewhere in the metadata**, for example modalities should never be included in tags.

## Example

```{literalinclude} ../../examples/data_description.py
:language: python
:linenos:
```
