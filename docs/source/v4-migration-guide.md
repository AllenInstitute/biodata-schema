# biodata-schema v4 migration guide

This guide records migration changes for version 4. For earlier changes, see
the [v3 migration guide](v3-migration-guide.md).

## Subjects and specimens

An asset can now contain data from more than one subject. Fields that list the
subjects or specimens in an asset use plural names and collections:

| Object | Before | Now |
| --- | --- | --- |
| `Acquisition` | `subject_name: str` | `subject_names: set[str]` |
| `Acquisition` | `specimen_name: str or List[str]` | `specimen_names: set[str]` |
| `DataDescription` | `subject_name: str` | `subject_names: set[str]` |
| `SpecimenProcedure` | `specimen_name: str or List[str]` | `specimen_names: set[str]` |
| `Metadata` | `subject: Subject` | `subjects: List[Subject]` |
| `Metadata` | `procedures: Procedures` | `procedures: List[Procedures]` |
| `Acquisition` | `subject_details: AcquisitionSubjectDetails` | `subject_details: List[AcquisitionSubjectDetails]` |

Use a collection even when there is only one name. In Python, write
`subject_names={"123456"}`. In JSON, write `"subject_names": ["123456"]`.
Sets remove duplicate names and have no meaningful order.

`Acquisition.subject_names` and `SpecimenProcedure.specimen_names` cannot be
empty. Acquisition specimen names remain optional except for in vitro modalities.

Each `Subject` and each `Procedures` object still belongs to one subject, so its
`subject_name` stays singular. Per-image `specimen_name` and a section's
`output_specimen_name` also stay singular.

### Metadata collections

Wrap the subject and procedures objects in lists, including for single-subject
assets. For example, `Metadata(subject=subject, procedures=procedures, ...)`
becomes `Metadata(subjects=[subject], procedures=[procedures], ...)`.

Each subject in `Metadata.subjects` must have exactly one matching `Procedures`
object. Use an empty `Procedures(subject_name="123456")` object when no procedures
were performed. Duplicate subjects, duplicate procedure records, missing
procedures, and procedures for a subject outside the roster are rejected.
Acquisition and data-description subject names must match the subject roster
when those names are present. Subject-free assets may omit procedures or use an
empty list.

Implanted device names must be unique across subjects and must not duplicate
instrument component names. `Metadata` rejects collisions. Prefix implanted
device names with `subject_name`, such as `123456_Probe A`, and update their
device-name references accordingly.

### Subject-specific acquisition records

Both `Manipulation` and `AcquisitionSubjectDetails` now require `subject_name`,
which must be a member of `Acquisition.subject_names`. Wrap acquisition subject
details in a list even for one subject. Duplicate details for a subject are
rejected, and in-vivo metadata requires one details record for every acquired
subject.

Every data stream (including `ExternalDataStream`) and stimulus epoch applies
to all subjects in `Acquisition.subject_names`, not a subset.

Old fields are not converted automatically. Rename them before validation.
In particular, the old `Metadata.subject` field is ignored, not moved into
`subjects`, and a single `Procedures` object is not converted into a list.

### Deriving and combining assets

`Metadata.from_metadata` compares the subject sets in its sources:

- **Same subjects in every source:** keep subjects and procedures, including
	multi-subject groups. Keep the shared set in `DataDescription.subject_names`.
	This applies even when the source assets come from different acquisitions.
- **Different subject sets:** drop subjects and procedures and clear
	`DataDescription.subject_names`. A subset is not a match: `{A, B}` combined
	with `{A}` drops the records. A caller-supplied subject-name override does not
	change this rule.

A single source keeps all its records. For multiple sources, subject order does
not matter, but every source needs a known roster, from its subject records or
data description. A source without subject information does not establish a
match. The helper keeps records from the first source that has them; it does not
merge conflicting subject or procedure records.

Combining different acquisitions also drops their instrument and acquisition
records and does not carry over their processing or QC. Supply the new
processing record for the combined asset. Its `source_data` lists the source
asset names.

### Writing core files

`Metadata.write_standard_files()` writes one `subjects.json` file and one
`procedures.json` file. Each contains a JSON array of its records, even when
there is only one subject. These are arrays directly, not objects containing
a `subjects` or `procedures` key. Subject names stay inside the records; they
are not used in filenames. Other core filenames stay the same.

To migrate existing files, rename `subject.json` to `subjects.json` and wrap its
object in an array. Wrap the existing `procedures.json` object in an array too.
Use `Metadata.write_standard_files()` to write these collection files rather
than writing each record separately.

The schema publishing action generates `subjects_schema.json` and
`procedures_schema.json` for these arrays. The Python `Subject` and `Procedures`
models still describe individual records.

#### Writer API

`write_standard_file` is now a class method on **all core models**, not an
instance method. Pass the record or collection as its first argument. This
also affects models whose files are still JSON objects, such as `Acquisition`
and `DataDescription`.

```python
# Before
subject.write_standard_file(output_directory=output_directory)
acquisition.write_standard_file(output_directory=output_directory)

# Now
Subject.write_standard_file([subject], output_directory=output_directory)
Acquisition.write_standard_file(acquisition, output_directory=output_directory)
```

`Subject.write_standard_file(subject, ...)` also accepts a single record, but
still writes a JSON array. The same applies to `Procedures`. Write all records
for a collection in one call; separate calls overwrite the same standard file.
An empty subject list is rejected. An empty procedures list writes `[]`.
Other core models accept a single record, not a list.

The `output_directory`, `prefix`, `filename_suffix`, and `suffix` options
remain available. `Metadata.write_standard_files()` is still an instance
method and writes all present core files; its calling convention is unchanged.

## Data Asset Naming

Asset names can now be any string; they no longer need to match a naming regex.
`DataDescription.name` is required and is no longer generated automatically.
Supply it explicitly, including for raw assets.

Passing `name` to `Metadata.from_metadata` or a derivation helper bypasses
name-generation requirements. When combining custom-named sources whose raw
acquisition roots cannot be identified, the helper treats acquisitions as
unshared: it drops instrument and acquisition records and uses only newly
supplied processing and QC. Identifiable shared roots retain their usual
inheritance behavior. Subject-roster checks and normal metadata validation
still apply.

### Naming helper imports

`biodata-models` version 3 removes `biodata_models.data_name_patterns`. Replace
imports from that module with:

```python
from biodata_models.data_levels import DataLevel
from biodata_schema.utils.data_name_patterns import (
    DataRegex,
    RegexParts,
    build_data_name,
    datetime_from_name_string,
    datetime_to_name_string,
)
```

`build_data_name` accepts a string `label` and a `creation_datetime`, for example
`build_data_name(label="group-5", creation_datetime=creation_time)`.
`Group` has no replacement enum; use a string label when constructing a name.

## Removed fields

`DataDescription.group` has been removed. Remove it from existing data
descriptions before validation; it is no longer copied by derivation helpers.
