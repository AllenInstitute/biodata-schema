"""Generic metadata class for Data Asset Records."""

import warnings
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import (
    ConfigDict,
    Field,
    PrivateAttr,
    SkipValidation,
    TypeAdapter,
    field_validator,
    model_validator,
)

from biodata_schema.base import DataCoreModel, DraftRequirement
from biodata_schema.components.identifiers import DatabaseIdentifiers
from biodata_schema.components.subject_procedures import TrainingProtocol
from biodata_schema.components.subjects import CalibrationObject
from biodata_schema.core.acquisition import Acquisition, DataStream
from biodata_schema.core.data_description import DataDescription
from biodata_schema.core.instrument import Instrument
from biodata_schema.core.model import Model
from biodata_schema.core.procedures import Procedures
from biodata_schema.core.processing import Processing
from biodata_schema.core.quality_control import QualityControl
from biodata_schema.core.subject import Subject
from biodata_schema.utils.compatibility_check import InstrumentAcquisitionCompatibility
from biodata_schema.utils.validators import (
    recursive_time_validation_check,
    validate_creation_time_after_midnight,
)

CORE_FILES = [
    "subjects",
    "data_description",
    "procedures",
    "instrument",
    "processing",
    "acquisition",
    "quality_control",
    "model",
]

# Files present must include at least one of these "file set" keys,
# and all files listed in any of the matched sets
REQUIRED_FILE_SETS = {
    "subjects": [
        "data_description",
        "procedures",
    ],
    "processing": ["data_description"],
    "model": ["data_description"],
}


class Metadata(DataCoreModel):
    """The records in the Data Asset Collection needs to contain certain fields
    to easily query and index the data."""

    model_config = ConfigDict(extra="ignore", revalidate_instances="always")

    # Special file name extension to distinguish this json file from others
    # The models base on this schema will be saved to metadata.nd.json as
    # default
    _FILE_EXTENSION = PrivateAttr(default=".nd.json")

    _DESCRIBED_BY_URL = DataCoreModel._DESCRIBED_BY_BASE_URL.default + "biodata_schema/core/metadata.py"
    describedBy: str = Field(default=_DESCRIBED_BY_URL, json_schema_extra={"const": _DESCRIBED_BY_URL})
    schema_version: SkipValidation[Literal["3.0.4"]] = Field(default="3.0.4")
    name: str = Field(
        ...,
        description="Name of the data asset.",
        title="Data Asset Name",
    )
    location: Annotated[str, DraftRequirement] = Field(
        ...,
        title="Location",
        description="Current location of the data asset.",
    )
    other_identifiers: Optional[DatabaseIdentifiers] = Field(
        default=None, title="Other identifiers", description="Links to the data asset on secondary platforms."
    )
    # We can make the DataCoreModel fields optional for now and do more
    # granular validations using validators. We may have some older data
    # assets in S3 that don't have metadata attached. We'd still like to
    # index that data, but we can flag those instances as MISSING or UNKNOWN
    subjects: Optional[List[Subject]] = Field(
        default=None,
        title="Subjects",
        description="Subject(s) of data collection.",
        min_length=1,
    )
    data_description: Optional[DataDescription] = Field(
        default=None, title="Data Description", description="A logical collection of data files."
    )
    procedures: Optional[List[Procedures]] = Field(
        default=None, title="Procedures", description="Procedures performed on each subject in this asset."
    )
    instrument: Optional[Instrument] = Field(
        default=None, title="Instrument", description="Devices used to acquire data."
    )
    processing: Optional[Processing] = Field(default=None, title="Processing", description="All processes run on data.")
    acquisition: Optional[Acquisition] = Field(default=None, title="Acquisition", description="Data acquisition")
    quality_control: Optional[QualityControl] = Field(
        default=None, title="Quality Control", description="Description of quality metrics for a data asset"
    )
    model: Optional[Model] = Field(
        default=None, title="Model", description="Description of a machine learning model trained on data."
    )

    @field_validator(*CORE_FILES, mode="before")
    @classmethod
    def serialize_core_models(cls, value: Any) -> Any:
        """Revalidate model instances and nested records through their serialized fields."""
        return TypeAdapter(Any).dump_python(value)

    @model_validator(mode="after")
    def validate_unique_subjects(self):
        """Ensure subject names are unique within the roster."""
        if self.subjects:
            names = [subject.subject_name for subject in self.subjects]
            if len(names) != len(set(names)):
                raise ValueError("subjects must have unique subject_name values")
        return self

    @model_validator(mode="after")
    def validate_subject_details_if_not_specimen(self):
        """Check that subject details are present if an in vivo experiment"""

        if self.acquisition and not self.acquisition.specimen_names:
            if not self.acquisition.subject_details:
                raise ValueError("Acquisition.subject_details are required for in vivo experiments")
            expected = self.acquisition.subject_names
            detail_names = {details.subject_name for details in self.acquisition.subject_details}
            missing = expected - detail_names
            if missing:
                raise ValueError(f"Acquisition.subject_details missing for subjects: {', '.join(sorted(missing))}")

        return self

    @model_validator(mode="after")
    def validate_expected_files_by_modality(self):
        """Validator warns users if required files are missing"""

        for file in REQUIRED_FILE_SETS.keys():
            if getattr(self, file):
                for required_file in REQUIRED_FILE_SETS[file]:
                    if not getattr(self, required_file):
                        warnings.warn(f"Metadata missing required file: {required_file}")

        return self

    @model_validator(mode="after")
    def validate_required_files(self):
        """Validator to ensure that one of the key files from the file sets is present."""

        one_of_required = REQUIRED_FILE_SETS.keys()

        if not any(getattr(self, file) for file in one_of_required):
            raise ValueError(f"Metadata must contain at least one of the following files: {', '.join(one_of_required)}")

        return self

    @model_validator(mode="after")
    def validate_unique_device_names(self):
        """Ensure implanted device names are unique across subjects and the instrument."""
        seen = set(self.instrument.get_component_names()) if self.instrument else set()
        duplicates = set()
        for procedures in self.procedures or []:
            names = set(procedures.get_device_names())
            duplicates.update(seen & names)
            seen.update(names)
        if duplicates:
            raise ValueError(
                f"Duplicate device names found across instrument and subject procedures: {sorted(duplicates)}. "
                "Prefix implanted device names with subject_name (e.g. '123456_Probe A') "
                "so they are unique across subjects and the instrument."
            )
        return self

    @model_validator(mode="after")
    def validate_instrument_acquisition_compatibility(self):
        """Validator for metadata"""
        if self.instrument and self.acquisition:
            check = InstrumentAcquisitionCompatibility(self.instrument, self.acquisition)
            check.run_compatibility_check()
        return self

    @model_validator(mode="after")
    def validate_acquisition_active_devices(self):
        """Ensure that all Acquisition.data_streams.active_devices exist in either the instrument or procedures."""

        active_devices = []

        if self.acquisition:
            for data_stream in self.acquisition.data_streams:
                if isinstance(data_stream, DataStream):
                    active_devices.extend(data_stream.active_devices)

        device_names = []

        if self.instrument:
            device_names.extend(self.instrument.get_component_names())
        for procedures in self.procedures or []:
            device_names.extend(procedures.get_device_names())

        # Check if all active devices are in the available devices
        if not all(device in device_names for device in active_devices):
            missing_devices = set(active_devices) - set(device_names)
            raise ValueError(
                f"Active devices '{missing_devices}' were not found in either the Instrument.components or "
                f"in an individual procedure's implanted_device field."
            )

        return self

    @model_validator(mode="after")
    def validate_calibration_object_tags(self):
        """Validator to ensure a CalibrationObject subject has the expected subject name"""

        if any(
            isinstance(getattr(subject, "subject_details", None), CalibrationObject)
            and subject.subject_name != "calibration"
            for subject in self.subjects or []
        ):
            raise ValueError("CalibrationObject subject_name must be 'calibration'.")

        return self

    @model_validator(mode="after")
    def validate_unique_procedure_per_subject(self):
        """Ensure there is exactly one Procedures object per subject"""
        subject_names = [subject.subject_name for subject in self.subjects] if self.subjects else []
        procedure_names = [procedures.subject_name for procedures in self.procedures] if self.procedures else []

        missing_procedures = set(subject_names) - set(procedure_names)
        if missing_procedures:
            raise ValueError(
                f"Each subject must have exactly one Procedures object. Missing for subjects: {', '.join(missing_procedures)}"
            )

        extra_procedures = set(procedure_names) - set(subject_names)
        if extra_procedures:
            raise ValueError(
                f"Each subject must have exactly one Procedures object. Extra procedures found for subjects: {', '.join(extra_procedures)}"
            )

        if len(procedure_names) != len(set(procedure_names)):
            raise ValueError("Each subject must have exactly one Procedures object. Duplicate procedures found.")

        return self

    @model_validator(mode="after")
    def validate_subject_name_consistency(self):
        """Ensure acquisition and data-description subject names match the subject roster.

        Note: procedures is covered by validate_unique_procedure_per_subject
        """

        if not self.subjects:
            return self

        expected = {subject.subject_name for subject in self.subjects}
        mismatches = []
        for field_name, core_model in (("acquisition", self.acquisition), ("data_description", self.data_description)):
            subject_names = core_model.subject_names if core_model else None
            if subject_names is not None and subject_names != expected:
                mismatches.append(f"{field_name}.subject_names={subject_names}")

        if mismatches:
            raise ValueError(f"subject_names mismatch with subjects.subject_name={expected}: {', '.join(mismatches)}")

        return self

    @model_validator(mode="after")
    def validate_training_protocol_references(self):
        """Validate that training_protocol_name in StimulusEpoch matches a TrainingProtocol in procedures"""

        if self.acquisition and self.procedures:
            # Get all training protocol names from procedures
            training_protocol_names = []
            for procedures in self.procedures:
                for procedure in procedures.subject_procedures:
                    if isinstance(procedure, TrainingProtocol):
                        training_protocol_names.append(procedure.training_name)

            # Check each stimulus epoch's training_protocol_name
            for stimulus_epoch in self.acquisition.stimulus_epochs:
                if stimulus_epoch.training_protocol_name:
                    if stimulus_epoch.training_protocol_name not in training_protocol_names:
                        warnings.warn(
                            f"Training protocol '{stimulus_epoch.training_protocol_name}' in StimulusEpoch "
                            f"not found in Procedures. Available protocols: {training_protocol_names}"
                        )

        return self

    @model_validator(mode="after")
    def validate_time_constraints(self):
        """Validate that all fields with TimeValidation annotations respect acquisition time bounds
        (if acquisition is present)"""
        if self.acquisition:
            acquisition_start_time = None
            acquisition_end_time = None
            if hasattr(self.acquisition, "acquisition_start_time") and hasattr(
                self.acquisition, "acquisition_end_time"
            ):
                acquisition_start_time = self.acquisition.acquisition_start_time
                acquisition_end_time = self.acquisition.acquisition_end_time

            recursive_time_validation_check(
                self.acquisition,
                acquisition_start_time=acquisition_start_time,
                acquisition_end_time=acquisition_end_time,
            )

            if self.processing:
                recursive_time_validation_check(
                    self.processing,
                    acquisition_start_time=acquisition_start_time,
                    acquisition_end_time=acquisition_end_time,
                )
            for subject in self.subjects or []:
                recursive_time_validation_check(
                    subject,
                    acquisition_start_time=acquisition_start_time,
                    acquisition_end_time=acquisition_end_time,
                )
            if self.instrument:
                recursive_time_validation_check(
                    self.instrument,
                    acquisition_start_time=acquisition_start_time,
                    acquisition_end_time=acquisition_end_time,
                )
            for procedures in self.procedures or []:
                recursive_time_validation_check(
                    procedures,
                    acquisition_start_time=acquisition_start_time,
                    acquisition_end_time=acquisition_end_time,
                )

        return self

    @model_validator(mode="after")
    def validate_data_description_time_consistency(self):
        """Check creation_time against the acquisition end date."""
        if self.data_description and self.acquisition:
            if hasattr(self.acquisition, "acquisition_end_time") and self.acquisition.acquisition_end_time is not None:
                creation_time = self.data_description.creation_time
                try:
                    validate_creation_time_after_midnight(creation_time, self.acquisition.acquisition_end_time)
                except ValueError:
                    warnings.warn(
                        f"Creation time from data_description.creation_time ({creation_time}) "
                        f"should be close to the acquisition end time "
                        f"({self.acquisition.acquisition_end_time})"
                    )

        return self

    def write_standard_files(self, output_directory: Optional[Path] = None, prefix: Optional[str] = None) -> None:
        """Write core files, with subjects and procedures stored as JSON arrays.

        Parameters
        ----------
        output_directory : Optional[Path]
            Optional directory to write files to. Defaults to current directory.
        prefix : Optional[str]
            Optional prefix for every filename, matching DataCoreModel.write_standard_file.
        """
        for field_name in CORE_FILES:
            value = getattr(self, field_name, None)
            if value is None:
                continue
            if field_name == "subjects":
                Subject.write_standard_file(value, output_directory=output_directory, prefix=prefix)
            elif field_name == "procedures":
                Procedures.write_standard_file(value, output_directory=output_directory, prefix=prefix)
            else:
                type(value).write_standard_file(value, output_directory=output_directory, prefix=prefix)

    @classmethod
    def from_metadata(
        cls,
        metadata: "Union[Metadata, List[Metadata]]",
        process_name: str = "processed",
        location: Optional[str] = "",
        new_processing: Optional[Processing] = None,
        new_quality_control: Optional[QualityControl] = None,
        **data_description_kwargs,
    ) -> "Metadata":
        """Create a derived Metadata object from one or more source Metadata objects.

        Applies four inheritance rules:
        1. All derived assets get an updated DataDescription (DERIVED level).
          2. Inherit Subjects and Procedures when all sources have the same subject roster.
              Otherwise, drop them and clear DataDescription.subject_names,
              including explicitly supplied subject-name overrides.
        3. If all sources share a single acquisition, inherit Instrument and Acquisition.
           Otherwise, drop them.
        4. If all sources share a single acquisition, accumulate Processing and
           QualityControl from the sources with the new ones. Otherwise, only use the
           new Processing/QualityControl.

        Note that the intent is to track the provenance/properties of data assets, using
        aggregated reference data (e.g. an atlas) does not make data multi-subject.

        Parameters
        ----------
        metadata : Metadata or List[Metadata]
            Source metadata object(s) to derive from.
        process_name : str
            Shortened name for the process or pipeline that was run -
            used in creating name of derived asset. Defaults to 'processed'.
        location : Optional[str]
            Location of the new derived data asset. Defaults to an empty string
            when unknown.
        new_processing : Optional[Processing]
            New processing performed to create this derived asset.
        new_quality_control : Optional[QualityControl]
            New quality control performed on this derived asset.
        **data_description_kwargs
            Additional keyword arguments passed to derive_data_description.
            An explicit name bypasses naming requirements. If source acquisition
            roots cannot be identified, treat them as unshared for inheritance.

        Returns
        -------
        Metadata
            A new Metadata object for the derived asset.
        """
        from biodata_schema.utils.inheritance import (
            _accumulate_processing,
            _accumulate_quality_control,
            _get_shared_subject_names,
            _inherit_instrument_and_acquisition,
            _inherit_subject_and_procedures,
            derive_data_description,
            derive_data_description_analyzed,
        )

        if isinstance(metadata, Metadata):
            metadata_list = [cls.model_validate(metadata)]
        else:
            metadata_list = [cls.model_validate(source) for source in metadata]

        if not metadata_list:
            raise ValueError("At least one source Metadata object is required.")

        first_dd = None
        for m in metadata_list:
            if m.data_description:
                first_dd = m.data_description
                break
        if first_dd is None:
            raise ValueError("At least one source Metadata must have a data_description.")

        source_names = [m.data_description.name for m in metadata_list if m.data_description]

        if len(metadata_list) > 1:
            derived_dd = derive_data_description_analyzed(
                first_dd,
                analysis_name=process_name,
                source_data=source_names,
                **data_description_kwargs,
            )
            derived_dd = derived_dd.model_copy(update={"subject_names": _get_shared_subject_names(metadata_list)})
        else:
            derived_dd = derive_data_description(
                first_dd,
                process_name=process_name,
                source_data=source_names if len(source_names) > 1 else None,
                **data_description_kwargs,
            )

        subject, procedures = _inherit_subject_and_procedures(metadata_list)
        allow_unknown_roots = data_description_kwargs.get("name") is not None
        instrument, acquisition = _inherit_instrument_and_acquisition(
            metadata_list, allow_unknown_roots=allow_unknown_roots
        )
        processing = _accumulate_processing(metadata_list, new_processing, allow_unknown_roots=allow_unknown_roots)
        quality_control = _accumulate_quality_control(
            metadata_list, new_quality_control, allow_unknown_roots=allow_unknown_roots
        )

        return cls(
            name=derived_dd.name,
            location="" if location is None else location,
            data_description=derived_dd,
            subjects=subject,
            procedures=procedures,
            instrument=instrument,
            acquisition=acquisition,
            processing=processing,
            quality_control=quality_control,
        )


def create_metadata_json(
    name: str,
    location: str,
    core_jsons: Dict[str, Optional[Union[dict, List[dict]]]],
    other_identifiers: Optional[dict] = None,
) -> dict:
    """Creates a Metadata dict from dictionary of core schema fields."""
    # Extract basic parameters and non-corrupt core schema fields

    params = {
        "name": name,
        "location": location,
    }
    if other_identifiers is not None:
        params["other_identifiers"] = other_identifiers
    core_fields = dict()
    for key, value in core_jsons.items():
        if key in CORE_FILES and value is not None:
            core_fields[key] = value
    metadata = Metadata.model_validate(params | core_fields)
    return metadata.model_dump(mode="json", by_alias=True)
