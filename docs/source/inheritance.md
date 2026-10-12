# Derived metadata

Each `Subject` and `Procedures` object describes one subject. An asset stores its subject records in one `subjects.json` file and its procedure records in one `procedures.json` file, both as JSON arrays. `Metadata.from_metadata` keeps these records when the source assets describe the same set of subjects:

| Subject rosters | Subjects and procedures | Data-description subject names |
| --- | --- | --- |
| All sources have the same set, such as `{A, B}` and `{A, B}` | Keep the full roster | Keep the shared set |
| Sets differ, such as `{A, B}` and `{A}` | Drop | Clear, including explicit overrides |

The number of source assets and the order of subjects do not affect this comparison. A single source keeps its records. For multiple sources, every source must have a known, matching roster, from its subject records or data description. When rosters match, the helper uses the first source that has subject and procedure records; it does not merge conflicting versions of those records.

The four specific principles to follow are:

- All derived assets need an updated **Data Description**
- If the sources have the same subject roster, inherit all **Subjects** and **Procedures** unchanged. Otherwise, drop these files and clear **Data Description** subject names.
- If a derived asset is related to a single acquisition, inherit the **Instrument** and **Acquisition** unchanged. Otherwise, drop these files.
- If a derived asset is related to a single acquisition, *accumulate* **Processing** and **Quality Control**. Otherwise, start these files from scratch in the new asset.

In practice this means that multi-session assets (from one or more subjects) generate a new data description, processing, and quality control from scratch.

Most users can rely on the `Metadata.from_metadata` function which implements all four of these rules for you. Load your core files and validate them as a `Metadata` object as well as any new `Processing` or `QualityControl` core data that was generated during your processing or analysis, then pass all three objects to the function. Then, call `metadata.write_standard_files()` to output your derived core files.

Note that relying on aggregated reference data (such as the CCF template) in your processing pipeline or analysis code does not make your asset multi-subject.

## Naming

For derived assets created from processing pipelines (i.e. one raw asset that was processed) or from analysis on a single derived asset we retain the *original* raw asset name and the process label:

`<raw asset_name>_<process_label>_YYYYMMDDTHHMMSS+HHMM`

For assets created during analysis that aggregate across multiple acquisitions or subjects we switch to using the project name and process label:

`<project_name>_<process_label>_YYYYMMDDTHHMMSS+HHMM`

The timestamp includes a UTC offset without colons; negative offsets use `-HHMM`
instead of `+HHMM`. For example, `batch-17_20221012T162311-0700` uses an asset
label rather than a subject identifier.

## Example

```python
from datetime import datetime, timezone

from biodata_schema.core.metadata import Metadata
from biodata_schema.core.processing import DataProcess, Processing, ProcessStage
from biodata_schema.core.quality_control import QCMetric, QCStatus, QualityControl, Stage, Status
from biodata_schema.components.identifiers import Code
from biodata_models.modalities import Modality

# Load and validate source metadata (e.g. from a JSON file)
source = Metadata.model_validate_json(open("metadata.nd.json").read())

# Define the new processing you performed
new_processing = Processing.create_with_sequential_process_graph(
    data_processes=[
        DataProcess(
            process_type="Image tile fusing",
            name="Tile fusing",
            experimenters=["Dr. Dan"],
            stage=ProcessStage.PROCESSING,
            start_date_time=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            end_date_time=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            code=Code(url="https://github.com/my-org/my-pipeline", version="1.0.0"),
        ),
    ]
)

# Define any new QC metrics
new_qc = QualityControl(
    metrics=[
        QCMetric(
            name="Fused image SNR",
            modality=Modality.SPIM,
            stage=Stage.PROCESSING,
            value=42.5,
            status_history=[QCStatus(evaluator="Automated", status=Status.PASS, timestamp=datetime.now(timezone.utc))],
            tags={"step": "fusing"},
        ),
    ],
    default_grouping=["step"],
)

# Create the derived metadata -- this applies all four inheritance rules
derived = Metadata.from_metadata(
    source,
    process_name="fused",
    location="s3://my-bucket/derived-asset",
    new_processing=new_processing,
    new_quality_control=new_qc,
)

derived.write_standard_files(output_directory="path/to/output")
```
