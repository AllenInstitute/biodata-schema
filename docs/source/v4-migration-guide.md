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

Use a collection even when there is only one name. In Python, write
`subject_names={"123456"}`. In JSON, write `"subject_names": ["123456"]`.
Sets remove duplicate names and have no meaningful order.

`Acquisition.subject_names` and `SpecimenProcedure.specimen_names` cannot be
empty. Acquisition specimen names remain optional except for in vitro modalities.
Raw data descriptions require subject names; derived data descriptions may omit
them. Data-description subject names still cannot contain underscores.

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

Old fields are not converted automatically. Rename them before validation.
In particular, the old `Metadata.subject` field is ignored, not moved into
`subjects`, and a single `Procedures` object is not converted into a list.

### Deriving and combining assets

`Metadata.from_metadata` compares the subject sets in its sources:

- **Same subjects in every source:** keep subjects and procedures, including
	multi-subject rosters. Keep the shared set in `DataDescription.subject_names`.
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

## Data Asset Naming

Asset names can now be any string; they no longer need to match a naming regex.
