"""Tests metadata module"""

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from biodata_models.data_name_patterns import DataLevel
from biodata_models.modalities import Modality
from biodata_models.organizations import Organization
from biodata_models.species import Strain
from pydantic import ValidationError

from biodata_schema.components.connections import Connection
from biodata_schema.components.devices import EphysAssembly, EphysProbe, Laser, Manipulator
from biodata_schema.components.identifiers import Code, Database, Person
from biodata_schema.components.subject_procedures import TrainingProtocol
from biodata_schema.components.subjects import BreedingInfo, CalibrationObject, Housing, MouseSubject, Sex, Species
from biodata_schema.components.surgery_procedures import BrainInjection
from biodata_schema.core.acquisition import Acquisition, AcquisitionSubjectDetails, DataStream, StimulusEpoch
from biodata_schema.core.data_description import DataDescription, Funding
from biodata_schema.core.instrument import Instrument
from biodata_schema.core.metadata import Metadata, create_metadata_json
from biodata_schema.core.procedures import Procedures, Surgery
from biodata_schema.core.processing import DataProcess, Processing, ProcessName, ProcessStage
from biodata_schema.core.subject import Subject
from examples.aibs_smartspim_instrument import inst as spim_inst
from examples.barseq_acquisition import acquisition as barseq_acquisition
from examples.data_description import d as data_description
from examples.ephys_instrument import inst as ephys_inst
from examples.model import m as model_example
from examples.processing import p as processing_example
from examples.quality_control import q as quality_control_example
from examples.subject import s as subject

ephys_assembly = EphysAssembly(
    probes=[EphysProbe(probe_model="Neuropixels 1.0", name="Probe A")],
    manipulator=Manipulator(
        name="Probe manipulator",
        manufacturer=Organization.NEW_SCALE_TECHNOLOGIES,
        serial_number="4321",
    ),
    name="Ephys_assemblyA",
)

laser = Laser(
    manufacturer=Organization.HAMAMATSU,
    serial_number="1234",
    name="Laser A",
    wavelength=488,
)

t = datetime.fromisoformat("2024-09-13T14:00:00")


class TestMetadata:
    """Class to test Metadata model"""

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test class."""
        cls.spim_instrument = spim_inst

        subject = Subject(
            subject_id="123456",
            subject_details=MouseSubject(
                species=Species.HOUSE_MOUSE,
                strain=Strain.C57BL_6J,
                sex=Sex.MALE,
                date_of_birth=datetime(2022, 11, 22, 8, 43, 00, tzinfo=timezone.utc).date(),
                source=Organization.AI,
                breeding_info=BreedingInfo(
                    maternal_id="546543",
                    maternal_genotype="Emx1-IRES-Cre/wt; Camk2a-tTa/Camk2a-tTA",
                    paternal_id="232323",
                    paternal_genotype="Ai93(TITL-GCaMP6f)/wt",
                ),
                genotype="Emx1-IRES-Cre/wt;Camk2a-tTA/wt;Ai93(TITL-GCaMP6f)/wt",
                housing=Housing(home_cage_enrichment=["Running wheel"], cage_id="123"),
            ),
        )
        dd = DataDescription(
            modalities=[Modality.ECEPHYS],
            subject_id="123456",
            data_level="raw",
            creation_time=datetime(2022, 11, 22, 8, 43, 00, tzinfo=timezone.utc),
            institution=Organization.AIND,
            funding_source=[Funding(funder=Organization.NINDS, grant_number="grant001")],
            investigators=[Person(name="Jane Smith")],
            project_name="Test",
        )
        procedures = Procedures(
            subject_id="12345",
            global_coordinate_system="NotApplicable",
        )
        processing = Processing.create_with_sequential_process_graph(
            data_processes=[
                DataProcess(
                    experimenters=["Dr. Dan"],
                    name="My Analysis",
                    process_type=ProcessName.ANALYSIS,
                    stage=ProcessStage.ANALYSIS,
                    output_path="path/to/outputs",
                    start_date_time=t,
                    end_date_time=t,
                    code=Code(
                        url="https://url/for/pipeline",
                        version="0.1.1",
                    ),
                ),
            ]
        )

        cls.sample_name = "655019_2023-04-03T181709"
        cls.sample_location = "s3://bucket/655019_2023-04-03T181709"
        cls.subject = subject
        cls.dd = dd
        cls.procedures = procedures
        cls.processing = processing

        cls.subject_json = json.loads(subject.model_dump_json())
        cls.dd_json = json.loads(dd.model_dump_json())
        cls.procedures_json = json.loads(procedures.model_dump_json())
        cls.processing_json = json.loads(processing.model_dump_json())

    def test_default_file_extension(self):
        """Tests that the default file extension used is as expected."""
        assert ".nd.json" == Metadata._FILE_EXTENSION.default

    def test_injection_material_validator_spim(self):
        """Tests that the injection validator works for SPIM"""
        nano_inj = BrainInjection.model_construct()

        # Tests missing injection materials
        surgery2 = Surgery.model_construct(procedures=[nano_inj])
        with pytest.raises(ValidationError) as context:
            Metadata(
                name="655019_2023-04-03T181709",
                location="bucket",
                data_description=DataDescription.model_construct(
                    creation_time=datetime(2020, 12, 12, 12, 12, 12),
                    modalities=[Modality.SPIM],
                    subject_id="655019",
                    data_level="raw",
                ),
                subject=subject,
                procedures=Procedures.model_construct(subject_procedures=[surgery2]),
                acquisition=Acquisition.model_construct(
                    acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
                    subject_details=AcquisitionSubjectDetails.model_construct(),
                ),
                instrument=self.spim_instrument,
                processing=Processing.model_construct(),
            )
        assert "Injection is missing injection_materials." in str(context.value)

    def test_injection_material_validator_ephys(self):
        """Test that the injection validator works for ephys"""
        nano_inj = BrainInjection.model_construct()

        # Tests missing injection materials
        surgery2 = Surgery.model_construct(procedures=[nano_inj])
        modalities = [Modality.ECEPHYS]
        with pytest.raises(ValidationError) as context:
            Metadata(
                name="655019_2023-04-03T181709",
                location="bucket",
                data_description=DataDescription.model_construct(
                    creation_time=datetime(2020, 12, 12, 12, 12, 12),
                    modalities=modalities,
                    subject_id="655019",
                    data_level="raw",
                ),
                subject=subject,
                procedures=Procedures.model_construct(subject_procedures=[surgery2]),
                instrument=ephys_inst,
                processing=Processing.model_construct(),
                acquisition=Acquisition.model_construct(
                    instrument_id="323_EPHYS1_20231003",
                    acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
                    subject_details=AcquisitionSubjectDetails.model_construct(),
                ),
            )
        assert "Injection is missing injection_materials." in str(context.value)

    def test_validate_instrument_acquisition_compatibility(self):
        """Tests that instrument/acquisition compatibility validator works as expected"""

        modalities = [Modality.ECEPHYS]
        inst = Instrument.model_construct(
            instrument_id="123_EPHYS1_20220101",
            modalities=modalities,
            components=[ephys_assembly],
            global_coordinate_system="NotApplicable",
        )
        with pytest.raises(ValidationError) as context:
            Metadata(
                name="655019_2023-04-03T181709",
                location="bucket",
                data_description=DataDescription.model_construct(
                    creation_time=datetime(2020, 12, 12, 12, 12, 12),
                    modalities=modalities,
                    subject_id="655019",
                    data_level="raw",
                ),
                subject=subject,
                procedures=Procedures.model_construct(),
                instrument=inst,
                processing=Processing.model_construct(),
                acquisition=Acquisition.model_construct(
                    instrument_id="123_EPHYS2_20230101",
                    acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
                    subject_details=AcquisitionSubjectDetails.model_construct(mouse_platform_name="platform1"),
                    data_streams=[],
                ),
            )
        assert (
            "Instrument ID in acquisition 123_EPHYS2_20230101 does not match the instrument's 123_EPHYS1_20220101."
        ) in str(context.value)

    def test_validate_old_schema_version(self):
        """Tests that old schema versions are ignored during validation"""
        m = Metadata.model_construct(
            name="name",
            location="location",
            id="1",
            subject=subject,
        )

        m_dict = m.model_dump()

        m_dict["schema_version"] = "0.0.0"

        m2 = Metadata(**m_dict)

        assert m2 is not None

    def test_create_from_core_jsons(self):
        """Tests metadata json can be created with valid inputs"""
        core_jsons = {
            "subject": self.subject_json,
            "data_description": self.dd_json,
            "procedures": self.procedures_json,
            "instrument": None,
            "processing": self.processing_json,
            "acquisition": None,
            "quality_control": None,
        }
        expected_md = Metadata(
            name=self.sample_name,
            location=self.sample_location,
            data_description=self.dd,
            subject=self.subject,
            procedures=self.procedures,
            processing=self.processing,
        )
        expected_result = json.loads(expected_md.model_dump_json(by_alias=True))
        result = create_metadata_json(
            name=self.sample_name,
            location=self.sample_location,
            core_jsons=core_jsons,
        )
        # check that metadata was created with expected values
        assert self.sample_name == result["name"]
        assert self.sample_location == result["location"]
        assert self.subject_json == result["subject"]
        assert self.procedures_json == result["procedures"]
        assert self.processing_json == result["processing"]
        assert result["acquisition"] is None
        # also check the other fields
        assert expected_result == result

    def test_create_from_core_jsons_invalid(self):
        """Tests metadata json creation with invalid inputs"""
        core_jsons = {
            "subject": self.subject_json,
            "data_description": None,
            "procedures": self.procedures_json,
            "instrument": Instrument.model_construct().model_dump(),
            "processing": Processing.model_construct().model_dump(),
            "acquisition": None,
            "quality_control": None,
        }
        # invalid core_jsons
        metadata = create_metadata_json(
            name=self.sample_name,
            location=self.sample_location,
            core_jsons=core_jsons,
        )
        assert metadata is not None

    def test_create_from_core_jsons_optional_overwrite(self):
        """Tests metadata json creation with created and external links"""
        other_identifiers = {
            Database.CODEOCEAN.value: ["123", "abc"],
        }
        result = create_metadata_json(
            name=self.sample_name,
            location=self.sample_location,
            core_jsons={
                "subject": self.subject_json,
            },
            other_identifiers=other_identifiers,
        )
        assert self.sample_name == result["name"]
        assert self.sample_location == result["location"]
        assert other_identifiers == result["other_identifiers"]

    def test_validate_expected_files_by_modality(self):
        """Tests that warnings are issued when metadata is missing required files"""
        # Test case where required files are missing for 'subject'
        with pytest.warns(UserWarning) as w:
            Metadata(
                name="655019_2023-04-03T181709",
                location="bucket",
                subject=self.subject,
                # Missing required files: data_description, procedures, instrument, acquisition
            )

        warning_messages = [str(warning.message) for warning in w]
        assert "Metadata missing required file: data_description" in warning_messages
        assert "Metadata missing required file: procedures" in warning_messages
        assert "Metadata missing required file: instrument" in warning_messages
        assert "Metadata missing required file: acquisition" in warning_messages

        # Test case where ALL required file set keys are missing (subject, processing, model)
        with pytest.raises(ValueError) as context:
            Metadata(
                name="655019_2023-04-03T181709",
                location="bucket",
                # No subject, processing, or model - should trigger validation error
            )
        assert "Metadata must contain at least one of the following files: subject, processing, model" in str(
            context.value
        )

    def test_external_data_stream_no_instrument_warning(self):
        """Test that ExternalDataStream-only acquisitions do not warn about missing instrument"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Metadata(
                name="655019_2023-04-03T181709",
                location="bucket",
                subject=subject,
                acquisition=barseq_acquisition,
            )
        instrument_warnings = [str(warning.message) for warning in w if "instrument" in str(warning.message)]
        assert [] == instrument_warnings

    def test_validate_acquisition_connections(self):
        """Tests that acquisition connections are validated correctly."""
        # Case where all connection devices are present in instrument components
        instrument = Instrument.model_construct(
            instrument_id="Test",
            components=[
                EphysProbe.model_construct(name="Probe A"),
                Laser.model_construct(name="Laser A"),
            ],
            modalities=[],
        )
        acquisition = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            data_streams=[
                DataStream.model_construct(active_devices=["Probe A", "Laser A"], modalities=[], configurations=[]),
            ],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )
        metadata = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            instrument=instrument,
            acquisition=acquisition,
        )
        assert metadata is not None

        # Case where connection devices are missing
        acquisition = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            data_streams=[
                DataStream.model_construct(
                    active_devices=["Probe A", "Laser A"],
                    modalities=[],
                    configurations=[],
                    connections=[Connection(source_device="Probe A", target_device="Missing Device")],
                ),
            ],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )
        with pytest.raises(ValueError) as context:
            Metadata(
                name="Test Metadata",
                location="Test Location",
                subject=subject,
                instrument=instrument,
                acquisition=acquisition,
            )
        assert "Missing Device" in str(context.value)

        # Case where source device is missing
        acquisition_missing_source = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            data_streams=[
                DataStream.model_construct(
                    active_devices=["Probe A", "Laser A"],
                    modalities=[],
                    configurations=[],
                    connections=[Connection(source_device="Missing Source", target_device="Laser A")],
                ),
            ],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )
        with pytest.raises(ValueError) as context:
            Metadata(
                name="Test Metadata",
                location="Test Location",
                subject=subject,
                instrument=instrument,
                acquisition=acquisition_missing_source,
            )
        assert "Missing Source" in str(context.value)

    def test_validate_acquisition_active_devices(self):
        """Tests that acquisition active devices are validated correctly."""
        # Case where all active devices are present in instrument components
        instrument = Instrument.model_construct(
            instrument_id="Test",
            components=[
                EphysProbe.model_construct(name="Probe A"),
                Laser.model_construct(name="Laser A"),
            ],
            modalities=[],
        )
        acquisition = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            data_streams=[
                DataStream.model_construct(active_devices=["Probe A", "Laser A"], modalities=[], configurations=[]),
            ],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )
        metadata = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            instrument=instrument,
            acquisition=acquisition,
        )
        assert metadata is not None

        # Case where active devices are missing from both instrument and procedures
        acquisition = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            data_streams=[
                DataStream.model_construct(
                    active_devices=["Probe A", "Missing Device"], modalities=[], configurations=[]
                ),
            ],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )
        with pytest.raises(ValueError) as context:
            Metadata(
                name="Test Metadata",
                location="Test Location",
                subject=subject,
                instrument=instrument,
                acquisition=acquisition,
            )
        assert (
            "Active devices '{'Missing Device'}' were not found in either the Instrument.components or "
            "in an individual procedure's implanted_device field."
        ) in str(context.value)

    def test_validate_training_protocol_references(self):
        """Tests that training protocol references are validated correctly."""

        # Case where training protocol references match
        training_protocol = TrainingProtocol.model_construct(training_name="Protocol A")
        procedures = Procedures.model_construct(subject_procedures=[training_protocol])
        stimulus_epoch = StimulusEpoch.model_construct(training_protocol_name="Protocol A")
        acquisition = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            stimulus_epochs=[stimulus_epoch],
            data_streams=[],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )

        metadata = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            procedures=procedures,
            acquisition=acquisition,
        )
        assert metadata is not None

        # Case where training protocol reference doesn't match
        stimulus_epoch_invalid = StimulusEpoch.model_construct(training_protocol_name="Missing Protocol")
        acquisition_invalid = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            stimulus_epochs=[stimulus_epoch_invalid],
            data_streams=[],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )

        with pytest.warns(UserWarning) as w:
            metadata = Metadata(
                name="Test Metadata",
                location="Test Location",
                subject=subject,
                procedures=procedures,
                acquisition=acquisition_invalid,
            )

        warning_messages = [str(warning.message) for warning in w]
        assert (
            "Training protocol 'Missing Protocol' in StimulusEpoch not found in Procedures."
            " Available protocols: ['Protocol A']"
        ) in warning_messages
        assert metadata is not None

        # Case where no training protocols exist in procedures
        procedures_empty = Procedures.model_construct(subject_procedures=[])
        with pytest.warns(UserWarning) as w:
            metadata = Metadata(
                name="Test Metadata",
                location="Test Location",
                subject=subject,
                procedures=procedures_empty,
                acquisition=acquisition_invalid,
            )

        warning_messages = [str(warning.message) for warning in w]
        assert (
            "Training protocol 'Missing Protocol' in StimulusEpoch not found in Procedures. Available protocols: []"
        ) in warning_messages
        assert metadata is not None

        # Case where stimulus epoch has no training protocol name (should pass)
        stimulus_epoch_none = StimulusEpoch.model_construct(training_protocol_name=None)
        acquisition_none = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            data_streams=[],
            stimulus_epochs=[stimulus_epoch_none],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )

        metadata_none = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            procedures=procedures,
            acquisition=acquisition_none,
        )
        assert metadata_none is not None

        # Case where acquisition is None (should pass)
        metadata_no_acquisition = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            procedures=procedures,
        )
        assert metadata_no_acquisition is not None

        # Case where procedures is None (should pass)
        metadata_no_procedures = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            acquisition=acquisition,
        )
        assert metadata_no_procedures is not None

    def test_validate_data_description_name_time_consistency(self):
        """Tests that data_description.name creation_time is on or after midnight
        on the same day as acquisition.acquisition_end_time"""

        # Create a specific datetime for testing
        test_datetime = datetime(2023, 4, 3, 18, 17, 9, tzinfo=timezone.utc)

        # Create a data description with a name that should match the acquisition end time
        data_description = DataDescription(
            creation_time=test_datetime,
            modalities=[Modality.ECEPHYS],
            subject_id="655019",
            data_level=DataLevel.RAW,
            institution=Organization.AIND,
            funding_source=[Funding(funder=Organization.NINDS)],
            investigators=[Person(name="Test Person")],
            project_name="Test Project",
        )

        # Create acquisition with matching end time using model_construct
        acquisition = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 4, 3, 18, 0, 0, tzinfo=timezone.utc),
            acquisition_end_time=test_datetime,
            data_streams=[],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )

        # This should pass - creation time is exactly at acquisition end time
        metadata_matching = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            data_description=data_description,
            acquisition=acquisition,
        )
        assert metadata_matching is not None

        # Test with creation time later on the same day - should pass
        later_same_day = datetime(2023, 4, 3, 23, 59, 59, tzinfo=timezone.utc)
        data_description_later = DataDescription(
            creation_time=later_same_day,
            modalities=[Modality.ECEPHYS],
            subject_id="655019",
            data_level=DataLevel.RAW,
            institution=Organization.AIND,
            funding_source=[Funding(funder=Organization.NINDS)],
            investigators=[Person(name="Test Person")],
            project_name="Test Project",
        )

        metadata_later_same_day = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            data_description=data_description_later,
            acquisition=acquisition,
        )
        assert metadata_later_same_day is not None

        # Test with creation time on the next day - should pass
        next_day = datetime(2023, 4, 4, 0, 0, 1, tzinfo=timezone.utc)
        data_description_next_day = DataDescription(
            creation_time=next_day,
            modalities=[Modality.ECEPHYS],
            subject_id="655019",
            data_level=DataLevel.RAW,
            institution=Organization.AIND,
            funding_source=[Funding(funder=Organization.NINDS)],
            investigators=[Person(name="Test Person")],
            project_name="Test Project",
        )

        metadata_next_day = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            data_description=data_description_next_day,
            acquisition=acquisition,
        )
        assert metadata_next_day is not None

        # Test with creation time before midnight of acquisition day - should fail
        before_midnight = datetime(2023, 4, 2, 23, 59, 59, tzinfo=timezone.utc)
        data_description_before = DataDescription(
            creation_time=before_midnight,
            modalities=[Modality.ECEPHYS],
            subject_id="655019",
            data_level=DataLevel.RAW,
            institution=Organization.AIND,
            funding_source=[Funding(funder=Organization.NINDS)],
            investigators=[Person(name="Test Person")],
            project_name="Test Project",
        )

        # This should issue a warning - creation time is before the acquisition day
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")
            metadata_with_warning = Metadata(
                name="Test Metadata",
                location="Test Location",
                subject=subject,
                data_description=data_description_before,
                acquisition=acquisition,
            )
            # Should have successfully created the metadata object
            assert metadata_with_warning is not None
            # Should have issued a warning
            print(warning_list)
            # Filter to only the time consistency warning
            time_warnings = [w for w in warning_list if "Creation time from data_description" in str(w.message)]
            assert len(time_warnings) == 1
            assert "Creation time from data_description" in str(time_warnings[0].message)
            assert "should be close to the acquisition end time" in str(time_warnings[0].message)

        # Test case where data_description is None (should pass)
        metadata_no_data_desc = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            acquisition=acquisition,
        )
        assert metadata_no_data_desc is not None

        # Test case where acquisition is None (should pass)
        metadata_no_acquisition = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            data_description=data_description,
        )
        assert metadata_no_acquisition is not None

    def test_validate_time_constraints_subject(self):
        """Tests that time constraints are validated for subject with date_of_birth"""

        # Create acquisition with specific times
        acquisition_start = datetime(2023, 4, 3, 18, 0, 0, tzinfo=timezone.utc)
        acquisition_end = datetime(2023, 4, 3, 19, 0, 0, tzinfo=timezone.utc)

        acquisition = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=acquisition_start,
            acquisition_end_time=acquisition_end,
            data_streams=[],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )

        # Test case where subject's date_of_birth is before acquisition (should pass)
        valid_birth_date = datetime(2022, 1, 1, tzinfo=timezone.utc).date()
        valid_subject = Subject(
            subject_id="123456",
            subject_details=MouseSubject(
                species=Species.HOUSE_MOUSE,
                strain=Strain.C57BL_6J,
                sex=Sex.MALE,
                date_of_birth=valid_birth_date,
                source=Organization.AI,
                genotype="wt",
                breeding_info=BreedingInfo(
                    maternal_id="123",
                    maternal_genotype="wt",
                    paternal_id="456",
                    paternal_genotype="wt",
                ),
                housing=Housing(cage_id="123"),
            ),
        )

        # This should pass - birth date is before acquisition
        metadata_valid_birth = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=valid_subject,
            acquisition=acquisition,
        )
        assert metadata_valid_birth is not None

        # Test case where subject's date_of_birth is after acquisition end (should fail)
        invalid_birth_date = datetime(2023, 4, 4, tzinfo=timezone.utc).date()  # After acquisition
        invalid_subject = Subject(
            subject_id="123456",
            subject_details=MouseSubject(
                species=Species.HOUSE_MOUSE,
                strain=Strain.C57BL_6J,
                sex=Sex.MALE,
                date_of_birth=invalid_birth_date,
                source=Organization.AI,
                genotype="wt",
                breeding_info=BreedingInfo(
                    maternal_id="123",
                    maternal_genotype="wt",
                    paternal_id="456",
                    paternal_genotype="wt",
                ),
                housing=Housing(cage_id="123"),
            ),
        )

        # This should fail - birth date is after acquisition end
        with pytest.raises(ValueError) as context:
            Metadata(
                name="Test Metadata",
                location="Test Location",
                subject=invalid_subject,
                acquisition=acquisition,
            )
        assert "must be before" in str(context.value)
        assert "date_of_birth" in str(context.value)

    def test_validate_time_constraints_processing(self):
        """Tests that time constraints are validated for processing with start_date_time and end_date_time"""

        # Create acquisition with specific times
        acquisition_start = datetime(2023, 4, 3, 18, 0, 0, tzinfo=timezone.utc)
        acquisition_end = datetime(2023, 4, 3, 19, 0, 0, tzinfo=timezone.utc)

        acquisition = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=acquisition_start,
            acquisition_end_time=acquisition_end,
            data_streams=[],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )

        # Test case where processing times are after acquisition (should pass)
        valid_processing = Processing.create_with_sequential_process_graph(
            data_processes=[
                DataProcess(
                    experimenters=["Dr. Dan"],
                    name="My Analysis",
                    process_type=ProcessName.ANALYSIS,
                    stage=ProcessStage.ANALYSIS,
                    output_path="path/to/outputs",
                    start_date_time=datetime(2023, 4, 3, 20, 0, 0, tzinfo=timezone.utc),  # After acquisition
                    end_date_time=datetime(2023, 4, 3, 21, 0, 0, tzinfo=timezone.utc),
                    code=Code(
                        url="https://url/for/pipeline",
                        version="0.1.1",
                    ),
                ),
            ]
        )

        # This should pass - processing times are after acquisition
        metadata_valid_processing = Metadata(
            name="Test Metadata",
            location="Test Location",
            processing=valid_processing,
            acquisition=acquisition,
        )
        assert metadata_valid_processing is not None

        # Test case where processing start time is before acquisition start (should fail)
        invalid_processing = Processing.create_with_sequential_process_graph(
            data_processes=[
                DataProcess(
                    experimenters=["Dr. Dan"],
                    name="My Analysis",
                    process_type=ProcessName.ANALYSIS,
                    stage=ProcessStage.ANALYSIS,
                    output_path="path/to/outputs",
                    start_date_time=datetime(2023, 4, 3, 17, 0, 0, tzinfo=timezone.utc),  # Before acquisition start
                    end_date_time=datetime(2023, 4, 3, 21, 0, 0, tzinfo=timezone.utc),
                    code=Code(
                        url="https://url/for/pipeline",
                        version="0.1.1",
                    ),
                ),
            ]
        )

        # This should fail - processing start time is before acquisition start
        with pytest.raises(ValueError) as context:
            Metadata(
                name="Test Metadata",
                location="Test Location",
                processing=invalid_processing,
                acquisition=acquisition,
            )
        assert "must be after" in str(context.value)
        assert "start_date_time" in str(context.value)

    def test_validate_calibration_object_tags(self):
        """Tests that CalibrationObject subjects use the calibration subject ID"""

        # Create a subject with CalibrationObject
        calibration_subject = Subject(
            subject_id="calibration_object_001",
            subject_details=CalibrationObject(
                description="Test calibration object",
            ),
        )

        with pytest.raises(ValueError, match="CalibrationObject subject_id must be 'calibration'"):
            Metadata(
                name="Test Metadata",
                location="Test Location",
                subject=calibration_subject,
                data_description=data_description,
            )

        calibration_subject.subject_id = "calibration"
        metadata = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=calibration_subject,
            data_description=data_description,
        )
        assert metadata is not None

    def test_validate_subject_details_if_not_specimen(self):
        """Tests that subject details are required if acquisition.specimen_id is not provided"""

        # Case where specimen_id is provided - should pass without subject_details
        acquisition_with_specimen = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            subject_id="123456",
            specimen_id="123456-001",
            data_streams=[],
        )
        metadata_with_specimen = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            acquisition=acquisition_with_specimen,
        )
        assert metadata_with_specimen is not None

        # Case where specimen_id is not provided and subject_details is provided - should pass
        acquisition_with_details = Acquisition.model_construct(
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            subject_id="123456",
            data_streams=[],
            subject_details=AcquisitionSubjectDetails.model_construct(),
        )
        metadata_with_details = Metadata(
            name="Test Metadata",
            location="Test Location",
            subject=subject,
            acquisition=acquisition_with_details,
        )
        assert metadata_with_details is not None

        # Case where neither specimen_id nor subject_details is provided - should fail
        acquisition_missing_both = Acquisition.model_construct(
            subject_id="123456",
            instrument_id="Test",
            acquisition_start_time=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            data_streams=[],
        )
        with pytest.raises(ValueError) as context:
            Metadata(
                name="Test Metadata",
                location="Test Location",
                subject=subject,
                acquisition=acquisition_missing_both,
            )
        assert "Acquisition.subject_details are required for in vivo experiments" in str(context.value)


class TestWriteStandardFiles:
    """Tests for Metadata.write_standard_files"""

    @patch.object(Path, "open", autospec=True)
    @patch("biodata_schema.utils.validators.recursive_check_paths")
    def test_writes_each_present_core_file(self, mock_rcp, mock_open_fn):
        """write_standard_files calls write_standard_file for each non-None core field"""
        m = Metadata.model_construct(
            name="test",
            location="s3://bucket/test",
            subject=subject,
            data_description=data_description,
            processing=processing_example,
            quality_control=quality_control_example,
        )
        m.write_standard_files()

        opened_files = [call_args[0][0].name for call_args in mock_open_fn.call_args_list]
        assert "subject.json" in opened_files
        assert "data_description.json" in opened_files
        assert "processing.json" in opened_files
        assert "quality_control.json" in opened_files
        assert 4 == mock_open_fn.call_count

    @patch.object(Path, "open", autospec=True)
    @patch("biodata_schema.utils.validators.recursive_check_paths")
    def test_skips_none_fields(self, mock_rcp, mock_open_fn):
        """Fields that are None produce no file writes"""
        m = Metadata.model_construct(
            name="test",
            location="s3://bucket/test",
            processing=processing_example,
        )
        m.write_standard_files()

        assert 1 == mock_open_fn.call_count
        opened_files = [call_args[0][0].name for call_args in mock_open_fn.call_args_list]
        assert "processing.json" in opened_files

    @patch.object(Path, "open", autospec=True)
    @patch("biodata_schema.utils.validators.recursive_check_paths")
    def test_output_directory_forwarded(self, mock_rcp, mock_open_fn):
        """output_directory is forwarded to each write_standard_file call"""
        m = Metadata.model_construct(
            name="test",
            location="s3://bucket/test",
            subject=subject,
            model=model_example,
        )
        m.write_standard_files(output_directory=Path("output_dir"))

        opened_files = [call_args[0][0] for call_args in mock_open_fn.call_args_list]
        assert Path("output_dir/subject.json") in opened_files
        assert Path("output_dir/model.json") in opened_files
