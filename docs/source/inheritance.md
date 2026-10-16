# Derived metadata

The four principles to follow are:

- All derived assets need an updated **Data Description**
- If all source data share the same group of subjects, inherit all **Subjects** and **Procedures** unchanged. Otherwise, drop these files.
- If a derived asset is related to a single acquisition, inherit the **Instrument** and **Acquisition** unchanged. Otherwise, drop these files.
- If a derived asset is related to a single acquisition, *accumulate* **Processing** and **Quality Control**. Otherwise, start these files from scratch in the new asset.

In practice these rules mean that single-subject and multi-subject assets that are analyzed in isolation inherit all the core files from asset to asset while analyses that combine multiple acquisitions from different subjects (or different groups of subjects) drop the initial core files.

Most users can rely on the `Metadata.from_metadata` function which implements all four of these rules for you. Load your core files and validate them as a `Metadata` object as well as any new `Processing` or `QualityControl` core data that was generated during your processing or analysis, then pass all three objects to the function. Call `metadata.write_standard_files()` to output your derived core files.

Note that relying on aggregated reference data (such as the CCF template) in your processing pipeline or analysis code does not make your asset multi-subject.

## Naming

Pass `name="<asset-name>"` to `Metadata.from_metadata` or any derivation helper to use any string as the asset name. If omitted, a single source generates:

`<source_name>_<process_label>_YYYYMMDDTHHMMSS`

When a derived asset is used as source data, the helper tries to recover the raw asset name from the standard pattern above. If that fails, it raises an error. For multiple input sources the default is:

`<project_name>_<process_label>_YYYYMMDDTHHMMSS`

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
