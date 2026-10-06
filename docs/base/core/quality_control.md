# Quality control

[Link to code](https://github.com/AllenNeuralDynamics/biodata-schema/blob/dev/src/biodata_schema/core/quality_control.py)

Quality control is a collection of **metrics** evaluated on a data asset.

[QCMetric](#qcmetric) objects should be generated during pipelines: from raw data, during processing, and during analysis by researchers.

Every [QCMetric](#qcmetric) has a `Status` which takes the value of the metric and compares it to some rule. Metrics can only pass or fail. Metrics that require manual evaluation are set to pending.

## Details

The metrics defined during quality control should define whether or not an asset can be used for analysis and the properties of an asset that could influence how an analysis is performed. There are two levels of QC:

- Quality control metrics that are **not allowed to fail** are metrics that at `stage:raw` would prevent an asset from being processed or that at `stage:processing` would prevent an asset from being analyzed. This is a very high bar. Another way of saying this is that if the goals of the data acquisition were met, then all metrics that are 'not allowed to fail' should be passing.
- Quality control metrics that are **allowed to fail** are metrics that will influence the analysis of data, for example by indicating that one element of an asset cannot be used. These assets do not invalidate further analysis but they change how analysis should be performed.

The second kind of metrics are identified by the `QualityControl.allow_tag_failures` field, details below.

### Metrics

Each [QCMetric](#qcmetric) is a single value or array of values that can be computed, or observed, about one modality in a data asset. These can have any type. Metrics should be significant: i.e. whether they pass or fail should matter for the modality. Metrics need to be human understandable. If you find yourself generating more metrics than a human can reasonably parse for a modality you should group them together (i.e. make the value a dictionary combining similar metrics).

Each [QCMetric](#qcmetric) has a [Status](#status). The [Status](#status) should depend directly on the `QCMetric.value`, either by a simple function: "value>5", or by a qualitative rule: "Field of view includes visual areas". The `QCMetric.description` field should describe the rule used to set the status. The status of a metric should be appended the `QCMetric.status_history`.

Each [QCMetric](#qcmetric) is annotated with three pieces of additional metadata: the [Stage](#stage) during which it was evaluated, the [Modality](biodata_models/modalities.md#modality) of the evaluated data, and [tags](#tags).

### Tags

`tags` are groups of descriptors that define how metrics are grouped hierarchically, making it easier to visualize metrics. Good tag keys (groups) are things like "probe" and good tag values (group members) are things like "Probe A" or just "A".

```python
# For an electrophysiology metric
tags = {
    "probe": "A",
    "shank": "0",
}

# For a behavioral video metric
tags = {
    "video": "left body",
}
```

When multiple QC stages are selected, they split at the top of the hierarchy. Multiple modalities split at the next level, or at the top when only one stage is selected. These fixed levels are followed by the tag levels in `QualityControl.default_grouping`. For example, `["stage", "modality", ("probe", "video"), "shank"]` groups first by stage, then by modality, then by probe or video at the same level, and finally by shank.

Use the builder to define tag keys and values, drag tag keys into level buckets, and preview the resulting hierarchy:

```{raw} html
<link rel="stylesheet" href="_static/qc-tree-app/qc-tree-app.css">
<div class="qc-tree-app"></div>
<script type="module" src="_static/qc-tree-app/qc-tree-app.js"></script>
```

### Curations

If you find yourself computing a value for something that is smaller than an entire modality of data and is repeated (e.g. neurons) in an asset you are performing *curation*, i.e. you are determining the status of a subset of a modality in the data asset. We provide the [CurationMetric](#curationmetric) for this purpose. You should put a dictionary in the `CurationMetric.value` field that contains a mapping between the subsets (usually neurons, ROIs, channels, etc) and their values.

### QualityControl.evaluate_status()

You can evaluate the state of a set of metrics filtered by any combination of modalities, stages, and tags on a specific date (by default, today). When evaluating the [Status](#status) of a group of metrics the following rules apply:

First, any metric that has a tag *value* in the `QualityControl.allow_tag_failures` list is ignored. This allows you to specify that certain metrics are not critical to a data asset.

Then, given the status of all the remaining metrics in the group:

1. If any metric is still failing, the evaluation fails
2. If any metric is pending and the rest pass the evaluation is pending
3. If all metrics pass the evaluation passes

### QualityControl.status

The `QualityControl.status` field is a dictionary that maps individual tag `key:value` pairs to their status. For example a typical status dictionary might look like this:

```
{
    "modality:behavior": "PASS",
}
```

**Q: What is a metric reference?**

Each [QCMetric](#qcmetric) should include a `QCMetric.reference`. References should be publicly accessible images, figures, multi-panel figures, and videos that support the metric value/status or provide the information necessary for manual annotation.

It's good practice to share a single multi-panel figure across multiple references to simplify viewing the quality control.

**Q: What are the status options for metrics?**

In our quality control a metric's status is always `PASS`, `PENDING` (waiting for manual annotation), or `FAIL`.

We enforce this minimal set of states to prevent ambiguity and make it easier to build tools that can interpret the status of a data asset.

## Multi-asset QC

During analysis there are many situations where multiple data assets need to be pulled together, often for comparison. For example, FOVs across imaging sessions or recording sessions from a chronic probe might need to get matched up across days. When a [QCMetric](#qcmetric) is being calculated from multiple assets it should be tagged with `Stage:MULTI_ASSET` and each of its metrics needs to track the assets that were used to generate that metric in the `evaluated_assets` list.

## Example

```{literalinclude} ../../examples/quality_control.py
:language: python
:linenos:
```
