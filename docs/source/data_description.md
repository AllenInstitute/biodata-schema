# Data description

[Link to code](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/src/biodata_schema/core/data_description.py)

The `data_description.json` file tracks administrative information about a data asset, including affiliated researchers/organizations, projects, data modalities, dates of collection, and more.

## Uniqueness

`DataDescription.name` can be any string. If omitted for single-subject raw data, it is generated as `<subject_name>_<creation_time>`. For multi-subject raw data, supply a name; we suggest `<label>_<acquisition-start-time>`, for example `batch-17_20221012T232311+0000`. Subjects are listed in `subject_names`, not inferred from the name.

You can group data assets together using `DataDescription.tags: List[str]`. Tags should be shared across assets within experiments. **Do not repeat information in the tags that already exists elsewhere in the metadata**, for example modalities should never be included in tags.

## Example

```{literalinclude} ../../examples/data_description.py
:language: python
:linenos:
```

## Core file

### DataDescription

Description of a logical collection of data files

| Field | Type | Title (Description) |
|-------|------|-------------|
| `license` | [License](biodata_models/licenses.md#license) | License  |
| `subject_names` | `Optional[set[typing.Annotated[str, StringConstraints(strip_whitespace=None, to_upper=None, to_lower=None, strict=None, min_length=None, max_length=None, pattern='^[^_]+$')]]]` | Subject names (Unique names for subjects associated with this data asset) |
| `creation_time` | `datetime (timezone-aware)` | Creation Time (Time that data files were created, used to uniquely identify the data) |
| `tags` | `Optional[List[str]]` | Tags (Descriptive strings to help categorize and search for data) |
| `name` | `Optional[str]` | Data asset name (Any string naming the data asset, conventionally also used as the data folder name. When omitted for single-subject raw data, generated from the subject name and creation time. Multi-subject raw data requires a name; consider `<label>_<acquisition-start-time>`, for example batch-17_20221012T232311+0000.) |
| `institution` | [Organization](biodata_models/organizations.md#organization) | Institution (An established society, corporation, foundation or other organization that collected this data) |
| `funding_source` | List[[Funding](data_description.md#funding)] | Funding source (Funding source. If internal funding, select 'Allen Institute') |
| `data_level` | [DataLevel](biodata_models/data_levels.md#datalevel) | Data Level (Level of processing that data has undergone) |
| `investigators` | List[[Person](components/identifiers.md#person)] | Investigators (Full name(s) of key investigators (e.g. PI, lead scientist, contact person)) |
| `project_name` | `str` | Project Name (A name for a set of coordinated activities intended to achieve one or more objectives.) |
| `restrictions` | `Optional[str]` | Restrictions (Detail any restrictions on publishing or sharing these data) |
| `modalities` | List[[Modality](biodata_models/modalities.md#modality)] | Modalities (A short name for the specific manner, characteristic, pattern of application, or the employment of any technology or formal procedure to generate data for a study) |
| `source_data` | `Optional[List[str]]` | Source data (For derived assets, list the source data asset names used to create this data) |
| `data_summary` | `Optional[str]` | Data summary (Semantic summary of experimental goal) |


## Model definitions

### Funding

Description of funding sources

| Field | Type | Title (Description) |
|-------|------|-------------|
| `funder` | [Organization](biodata_models/organizations.md#organization) | Funder  |
| `grant_number` | `Optional[str]` | Grant number  |
| `fundee` | Optional[List[[Person](components/identifiers.md#person)]] | Fundee (Person(s) funded by this mechanism) |
