# biodata-schema v4 migration guide

This guide records migration changes for version 4. For earlier changes, see
the [v3 migration guide](v3-migration-guide.md).

## Data Asset Naming

### Naming utilities moved into schema

Import `DataRegex`, `RegexParts`, `build_data_name`, `datetime_to_name_string`, and
`datetime_from_name_string` from `biodata_schema.utils.data_name_patterns`, not
`biodata_models.data_name_patterns`. `DataLevel` and `Group` remain in `biodata_models`.

Legacy regexes, the subject-specific `DataRegex.RAW`, and the unused
`DataRegex.NO_SPECIAL_CHARS` have been removed. Use `DataRegex.DATA`, whose
prefix is an asset label rather than a subject identifier.

### Folder-safe ISO timestamps

Generated asset timestamps now use folder-safe basic ISO 8601:
`YYYYMMDDTHHMMSS+HHMM` or `YYYYMMDDTHHMMSS-HHMM`. For example,
`1234_20221012T232311+0000` represents UTC, and
`batch-17_20221012T162311-0700` preserves a UTC-07:00 offset. Formatting retains
seconds but omits microseconds. Naive datetimes use the local timezone, matching
the schema's datetime handling. Parsing returns timezone-aware datetimes and no
longer accepts the old `YYYY-MM-DD_HH-MM-SS` timestamp format.

### Multi-subject asset labels

Single-subject raw assets still generate a name automatically when omitted.
Multi-subject raw assets require an explicit name; use a meaningful batch or
collection label followed by the timestamp. `subject_names` remains authoritative:
parsing an asset label does not infer its subjects. Existing explicitly supplied
names and source-data references are not automatically renamed.

### Historical source assets

`derive_data_description_from_derived` parses its source name and rejects
timestamps in the old format. For historical sources, construct the new
`DataDescription` explicitly and retain the actual source asset names in
`source_data`. Do not rename existing assets or storage locations merely to
change their timestamp format.
