"""Test for the acquisition.json"""

import inspect
from datetime import datetime, timedelta, timezone
from typing import get_args
from zoneinfo import ZoneInfo

import pydantic
import pytest
from biodata_models.modalities import Modality
from pydantic import ValidationError

from biodata_schema.components.configs import (
    DeviceConfig,
    EphysAssemblyConfig,
    ImagingConfig,
    Immersion,
    MRIScan,
    SampleChamberConfig,
)
from biodata_schema.components.connections import Connection
from biodata_schema.core.acquisition import (
    NON_IANA_TIMEZONES,
    Acquisition,
    AcquisitionSubjectDetails,
    DataStream,
    StimulusEpoch,
)
from examples.barseq_acquisition import acquisition as barseq_acquisition
from examples.ephys_acquisition import acquisition as ephys_acquisition
from examples.exaspim_acquisition import acq as exaspim_acquisition
from examples.mri_acquisition import acquisition as mri_acquisition
from examples.mri_acquisition import scan1


class TestAcquisition:
    """Group of tests for the Acquisition class"""

    def test_constructors(self):
        """Test constructing acquisition files"""

        with pytest.raises(pydantic.ValidationError):
            Acquisition()

        acq = ephys_acquisition.model_copy()
        assert Acquisition.model_validate_json(acq.model_dump_json()) is not None

        assert ephys_acquisition is not None
        assert exaspim_acquisition is not None
        assert mri_acquisition is not None

        scan1_dict = scan1.model_dump()

        with pytest.raises(ValidationError):
            # Ensure that MRIScan validator is properly enforcing pulse_sequence_type notes requirements
            scan1_dict["pulse_sequence_type"] = "Other"
            scan1_dict["notes"] = ""
            MRIScan.model_validate(scan1_dict)

    def test_external_data_stream(self):
        """Test ExternalDataStream: valid without instrument_id, and DataStream requires instrument_id"""
        # Happy path: BARseq example uses ExternalDataStream and has no instrument_id
        assert barseq_acquisition is not None
        assert barseq_acquisition.instrument_id is None

        # Guard: DataStream without instrument_id should fail
        start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValidationError) as context:
            Acquisition(
                subject_id="123456",
                acquisition_start_time=start,
                acquisition_end_time=end,
                acquisition_type="Test",
                data_streams=[
                    DataStream(
                        stream_start_time=start,
                        stream_end_time=end,
                        modalities=[Modality.BARSEQ],
                        active_devices=[],
                        configurations=[],
                    )
                ],
            )
        assert "instrument_id is required" in str(context.value)

    def test_check_subject_specimen_id(self):
        """Test that subject and specimen IDs match"""
        with pytest.raises(ValueError) as context:
            acq = exaspim_acquisition.model_copy()
            acq.specimen_id = "654321"

            Acquisition.model_validate_json(acq.model_dump_json())

        assert "Expected 123456 to appear in 654321" in str(context.value)

    def test_specimen_id_list_valid(self):
        """Test that specimen_id accepts a list of strings when all contain subject_id"""
        acq = exaspim_acquisition.model_copy()
        acq.specimen_id = ["123456_slide1", "123456_slide2"]
        validated = Acquisition.model_validate_json(acq.model_dump_json())
        assert validated.specimen_id == ["123456_slide1", "123456_slide2"]

    def test_specimen_id_list_invalid(self):
        """Test that specimen_id list raises ValueError if any entry does not contain subject_id"""
        with pytest.raises(ValueError) as context:
            acq = exaspim_acquisition.model_copy()
            acq.specimen_id = ["123456_slide1", "654321_slide2"]
            Acquisition.model_validate_json(acq.model_dump_json())
        assert "Expected 123456 to appear in 654321_slide2" in str(context.value)

    def test_specimen_required(self):
        """Test that specimen ID is required for in vitro imaging modalities"""
        acq = exaspim_acquisition.model_copy()
        acq.specimen_id = None
        with pytest.raises(ValidationError, match="Specimen ID is required for modalities"):
            Acquisition.model_validate_json(acq.model_dump_json())

    def test_check_modality_config_requirements(self):
        """Test that modality configuration requirements are enforced"""

        # Test missing required devices for ECEPHYS modality
        with pytest.raises(ValueError):
            DataStream(
                stream_start_time=datetime.now(),
                stream_end_time=datetime.now(),
                modalities=[Modality.ECEPHYS],
                active_devices=[],
                configurations=[],
            )

        # Test valid configuration for ECEPHYS modality
        stream = DataStream(
            stream_start_time=datetime.now(),
            stream_end_time=datetime.now(),
            modalities=[Modality.ECEPHYS],
            active_devices=["Stick_assembly", "Ephys_assemblyA"],
            configurations=[
                EphysAssemblyConfig.model_construct(),
            ],
        )
        assert stream is not None

    def test_specimen_required_for_in_vitro_modalities(self):
        """Test that specimen ID is required for in vitro imaging modalities"""

        # Test case where specimen ID is missing for in vitro modality
        with pytest.raises(ValueError) as context:
            Acquisition(
                experimenters=["Mam Moth"],
                acquisition_start_time=datetime.now(),
                acquisition_end_time=datetime.now(),
                subject_id="123456",
                acquisition_type="Test",
                instrument_id="1234",
                subject_details=AcquisitionSubjectDetails(
                    mouse_platform_name="Running wheel",
                ),
                data_streams=[
                    DataStream(
                        stream_start_time=datetime.now(),
                        stream_end_time=datetime.now(),
                        modalities=[Modality.SPIM],
                        active_devices=["Device1"],
                        configurations=[
                            ImagingConfig(
                                device_name="Device1",
                                channels=[],
                                images=[],
                            ),
                            SampleChamberConfig(
                                device_name="Sample chamber",
                                chamber_immersion=Immersion(
                                    medium="PBS",
                                    refractive_index=1.33,
                                ),
                            ),
                        ],
                    )
                ],
            )
        assert "Specimen ID is required for modalities" in str(context.value)

        # Test case where specimen ID is provided for in vitro modality
        acquisition = Acquisition(
            experimenters=["Mam Moth"],
            acquisition_start_time=datetime.now(),
            acquisition_end_time=datetime.now(),
            subject_id="123456",
            specimen_id="SP123456",
            acquisition_type="Test",
            instrument_id="1234",
            subject_details=AcquisitionSubjectDetails(
                mouse_platform_name="Running wheel",
            ),
            data_streams=[
                DataStream(
                    stream_start_time=datetime.now(),
                    stream_end_time=datetime.now(),
                    modalities=[Modality.SPIM],
                    active_devices=["Device1"],
                    configurations=[
                        ImagingConfig(
                            device_name="Device1",
                            channels=[],
                            images=[],
                        ),
                        SampleChamberConfig(
                            device_name="Sample chamber",
                            chamber_immersion=Immersion(
                                medium="PBS",
                                refractive_index=1.33,
                            ),
                        ),
                    ],
                )
            ],
        )
        assert acquisition is not None

    def test_check_connections(self):
        """Test that every device in a Connection is present in the active_devices list"""

        # Test valid connections
        stream = DataStream(
            stream_start_time=datetime.now(),
            stream_end_time=datetime.now(),
            modalities=[],
            active_devices=["DeviceA", "DeviceB", "SomeTarget"],
            configurations=[],
            connections=[
                Connection(source_device="DeviceA", target_device="SomeTarget"),
                Connection(source_device="DeviceB", target_device="SomeTarget"),
            ],
        )
        assert stream is not None

        # Test invalid connections
        with pytest.raises(ValueError) as context:
            DataStream(
                stream_start_time=datetime.now(),
                stream_end_time=datetime.now(),
                modalities=[],
                active_devices=["DeviceA"],
                configurations=[],
                connections=[
                    Connection(source_device="SomeTarget", target_device="DeviceA"),
                ],
            )
        assert "Missing devices in active_devices list for connection" in str(context.value)

        # Test invalid connections
        with pytest.raises(ValueError) as context:
            DataStream(
                stream_start_time=datetime.now(),
                stream_end_time=datetime.now(),
                modalities=[],
                active_devices=["DeviceA"],
                configurations=[],
                connections=[
                    Connection(source_device="DeviceA", target_device="SomeTarget"),
                ],
            )
        assert "Missing devices in active_devices list for connection" in str(context.value)

    def test_all_device_config_subclasses_covered(self):  # pragma: no cover
        """Test that all DeviceConfig subclasses are included in either DataStream or StimulusEpoch configurations

        No coverage on this test as it only does schema validation
        """

        # Import the calibration and maintenance base classes to exclude them
        from biodata_schema.components.measurements import Calibration, Maintenance

        # Get all subclasses of DeviceConfig using introspection
        def get_all_subclasses(cls):
            """Recursively get all subclasses of a class"""
            all_subclasses = set()
            for subclass in cls.__subclasses__():
                all_subclasses.add(subclass)
                all_subclasses.update(get_all_subclasses(subclass))
            return all_subclasses

        def extract_union_types(annotation):
            """Extract types from nested annotations like List[Annotated[Union[...], ...]]"""
            types = set()

            # Get the args from the List type
            list_args = get_args(annotation)
            if list_args:
                # Get the args from the Annotated type (first arg is the union)
                annotated_args = get_args(list_args[0])
                if annotated_args:
                    # Get the args from the Union type
                    union_args = get_args(annotated_args[0])
                    types.update(union_args)

            return types

        all_device_config_subclasses = get_all_subclasses(DeviceConfig)

        # Exclude calibration and maintenance classes as they're used elsewhere in Acquisition
        calibration_subclasses = get_all_subclasses(Calibration)
        maintenance_subclasses = get_all_subclasses(Maintenance)
        excluded_classes = calibration_subclasses | maintenance_subclasses | {Calibration, Maintenance}

        # Filter to only include config classes that should be in configurations
        config_subclasses = all_device_config_subclasses - excluded_classes

        # Extract the config types from DataStream configurations discriminated union
        datastream_annotation = DataStream.model_fields["configurations"].annotation
        datastream_config_types = extract_union_types(datastream_annotation)

        # Extract the config types from StimulusEpoch configurations discriminated union
        stimulus_annotation = StimulusEpoch.model_fields["configurations"].annotation
        stimulus_epoch_config_types = extract_union_types(stimulus_annotation)

        # Combine all configured types and filter to only include classes
        all_configured_types = datastream_config_types | stimulus_epoch_config_types
        all_configured_types = {t for t in all_configured_types if inspect.isclass(t)}

        # Check that all DeviceConfig subclasses are covered
        uncovered_configs = config_subclasses - all_configured_types

        # Create a helpful error message if there are uncovered configs
        if uncovered_configs:
            uncovered_names = [cls.__name__ for cls in uncovered_configs]
            configured_names = [
                cls.__name__ for cls in all_configured_types if inspect.isclass(cls) and issubclass(cls, DeviceConfig)
            ]

            error_msg = (
                f"The following DeviceConfig subclasses are not included in either "
                f"DataStream.configurations or StimulusEpoch.configurations: {uncovered_names}\n"
                f"Currently configured: {sorted(configured_names)}\n"
                f"Note: Calibration and Maintenance classes are excluded as they belong in "
                f"the calibrations and maintenance fields respectively.\n"
                f"Please add the missing configs to the appropriate discriminated union."
            )
            pytest.fail(error_msg)

        # If we get here, all device config subclasses are properly covered
        assert True, "All DeviceConfig subclasses are properly covered in discriminated unions"

    def test_datastream_add_basic(self):
        """Test combining two DataStream objects"""
        acq = ephys_acquisition.model_copy()

        stream1 = acq.data_streams[0].model_copy()
        stream2 = acq.data_streams[0].model_copy()

        stream1.active_devices = ["Device1", "Device2"]
        stream2.active_devices = ["Device3", "Device4"]

        combined_stream = stream1 + stream2

        assert combined_stream is not None
        assert combined_stream.stream_start_time == stream1.stream_start_time
        assert combined_stream.stream_end_time == stream1.stream_end_time
        assert len(combined_stream.modalities) == 1
        assert len(combined_stream.active_devices) == 4
        assert len(combined_stream.configurations) == 4

        # Also check that an error is raised if the streams cannot be combined

        stream2.stream_end_time = stream2.stream_end_time.replace(year=2100)

        with pytest.raises(ValueError):
            _ = stream1 + stream2

    def test_datastream_add_combines_notes(self):
        """Test that notes are properly merged when combining DataStreams"""
        acq = ephys_acquisition.model_copy()

        stream1 = acq.data_streams[0].model_copy()
        stream2 = acq.data_streams[0].model_copy()

        stream1.active_devices = ["Device1", "Device2"]
        stream2.active_devices = ["Device3", "Device4"]
        stream1.notes = "Note 1"
        stream2.notes = "Note 2"

        combined_stream = stream1 + stream2

        assert "Note 1" in combined_stream.notes
        assert "Note 2" in combined_stream.notes

    def test_datastream_add_with_duplicate_devices(self):
        """Test that overlapping active devices are logged as warning when combining"""
        acq = ephys_acquisition.model_copy()
        stream1 = acq.data_streams[0]
        stream2 = acq.data_streams[0].model_copy()

        combined_stream = stream1 + stream2

        assert combined_stream is not None

    def test_datastream_add_combines_connections(self):
        """Test that connections are properly combined"""
        acq = ephys_acquisition.model_copy()

        stream1 = acq.data_streams[0].model_copy()
        stream2 = acq.data_streams[0].model_copy()

        stream1.active_devices = ["Device1", "Device2"]
        stream2.active_devices = ["Device3", "Device4"]
        stream1.connections = [Connection(source_device="Device1", target_device="Device2")]
        stream2.connections = [Connection(source_device="Device3", target_device="Device4")]

        combined_stream = stream1 + stream2

        assert len(combined_stream.connections) == 2

    def test_merge_data_stream_lists_single_streams(self):
        """Test merging lists with single streams"""
        acq = ephys_acquisition.model_copy()
        stream1 = acq.data_streams[0].model_copy()
        stream2 = acq.data_streams[1].model_copy()

        stream1.active_devices = ["Device1"]
        stream2.active_devices = ["Device2"]

        merged = Acquisition._merge_data_streams([stream1] + [stream2])

        assert len(merged) == 2

    def test_merge_data_stream_lists_overlapping_streams(self):
        """Test merging streams with overlapping start/end times"""
        acq = ephys_acquisition.model_copy()

        stream1 = acq.data_streams[0].model_copy()
        stream2 = acq.data_streams[0].model_copy()

        stream1.active_devices = ["Device1", "Device2"]
        stream2.active_devices = ["Device3", "Device4"]

        merged = Acquisition._merge_data_streams([stream1] + [stream2])

        assert len(merged) == 1
        assert len(merged[0].active_devices) == 4

    def test_merge_data_stream_lists_non_overlapping_streams(self):
        """Test merging streams with different start/end times"""
        acq = ephys_acquisition.model_copy()

        stream1 = acq.data_streams[1].model_copy()
        stream2 = acq.data_streams[0].model_copy()

        stream1.active_devices = ["Device1"]
        stream2.active_devices = ["Device2"]

        merged = Acquisition._merge_data_streams([stream1] + [stream2])

        assert len(merged) == 2

    def test_merge_data_stream_lists_multiple_overlapping_groups(self):
        """Test merging multiple streams with multiple overlapping groups"""
        acq = ephys_acquisition.model_copy()

        stream1 = acq.data_streams[0].model_copy()
        stream2 = acq.data_streams[0].model_copy()
        stream3 = acq.data_streams[0].model_copy()

        stream1.active_devices = ["DeviceA", "DeviceB"]
        stream2.active_devices = ["DeviceC"]
        stream3.active_devices = ["DeviceD", "DeviceE"]

        start1 = datetime(year=2023, month=4, day=25, hour=2, minute=0, second=0, tzinfo=timezone.utc)
        end1 = datetime(year=2023, month=4, day=25, hour=2, minute=30, second=0, tzinfo=timezone.utc)
        stream1.stream_start_time = start1
        stream1.stream_end_time = end1

        start2 = datetime(year=2023, month=4, day=25, hour=2, minute=0, second=30, tzinfo=timezone.utc)
        end2 = datetime(year=2023, month=4, day=25, hour=2, minute=29, second=30, tzinfo=timezone.utc)
        stream2.stream_start_time = start2
        stream2.stream_end_time = end2

        start3 = datetime(year=2023, month=4, day=25, hour=3, minute=0, second=0, tzinfo=timezone.utc)
        end3 = datetime(year=2023, month=4, day=25, hour=3, minute=30, second=0, tzinfo=timezone.utc)
        stream3.stream_start_time = start3
        stream3.stream_end_time = end3

        merged = Acquisition._merge_data_streams([stream1] + [stream2, stream3])

        for m in merged:
            print(m.stream_start_time, m.stream_end_time, m.active_devices)

        assert len(merged) == 2
        assert len(merged[0].active_devices) == 3

    def test_datastream_add_with_exaspim_example(self):
        """Test combining DataStreams using ExaSPIM example"""
        acq = exaspim_acquisition.model_copy()
        stream1 = acq.data_streams[0].model_copy()

        stream2 = acq.data_streams[0].model_copy()
        stream2.active_devices = ["Device99"]

        combined_stream = stream1 + stream2

        assert combined_stream is not None
        assert Modality.SPIM in combined_stream.modalities
        assert len(combined_stream.active_devices) == 6

    def test_acquisition_start_time_local_with_zoneinfo(self):
        """acquisition_start_time_local converts correctly using a ZoneInfo IANA name"""
        from pydantic_extra_types.timezone_name import TimeZoneName

        dt = datetime(2023, 6, 15, 20, 0, 0, tzinfo=timezone.utc)
        acq = Acquisition.model_construct(
            acquisition_start_time=dt,
            acquisition_start_tz=TimeZoneName("America/Los_Angeles"),
        )
        local = acq.acquisition_start_time_local
        assert local.tzinfo == ZoneInfo("America/Los_Angeles")
        assert local.hour == 13

    def test_acquisition_start_time_local_with_int_offset(self):
        """acquisition_start_time_local converts correctly using an integer UTC offset in hours"""
        dt = datetime(2023, 6, 15, 20, 0, 0, tzinfo=timezone.utc)
        acq = Acquisition.model_construct(
            acquisition_start_time=dt,
            acquisition_start_tz=-7,
        )
        local = acq.acquisition_start_time_local
        assert local.utcoffset() == timedelta(hours=-7)
        assert local.hour == 13

    def test_acquisition_start_time_local_with_no_tz(self):
        """acquisition_start_time_local returns acquisition_start_time unchanged when tz is None"""
        dt = datetime(2023, 6, 15, 20, 0, 0, tzinfo=timezone.utc)
        acq = Acquisition.model_construct(
            acquisition_start_time=dt,
            acquisition_start_tz=None,
        )
        assert acq.acquisition_start_time_local == dt

    def test_acquisition_start_time_local_round_trip(self):
        """acquisition_start_time_local preserves the original wall-clock time after round-tripping
        through Acquisition validation with a ZoneInfo timezone"""
        from examples.exaspim_acquisition import t as exaspim_t

        acq = exaspim_acquisition.model_copy()
        local = acq.acquisition_start_time_local
        assert local.year == exaspim_t.year
        assert local.month == exaspim_t.month
        assert local.day == exaspim_t.day
        assert local.hour == exaspim_t.hour
        assert local.minute == exaspim_t.minute
        assert local.second == exaspim_t.second
        assert local.tzinfo == exaspim_t.tzinfo

    def test_coerce_fixed_offset_tz_string(self):
        """Legacy '-07:00' strings are coerced to integer hour offsets"""
        assert Acquisition.coerce_fixed_offset_tz_string("-07:00") == -7
        assert Acquisition.coerce_fixed_offset_tz_string("+05:30") == 5
        assert Acquisition.coerce_fixed_offset_tz_string("+00:00") == 0
        assert Acquisition.coerce_fixed_offset_tz_string("00:00") == 0
        assert Acquisition.coerce_fixed_offset_tz_string(None) is None
        assert Acquisition.coerce_fixed_offset_tz_string(-7) == -7
        assert Acquisition.coerce_fixed_offset_tz_string("America/Los_Angeles") == "America/Los_Angeles"

    def test_reject_non_iana_tz(self):
        """Host timezone artifacts are rejected, real zones and offsets pass through"""
        for name in NON_IANA_TIMEZONES:
            with pytest.raises(ValueError) as context:
                Acquisition.reject_non_iana_tz(name)
            assert "is not an IANA timezone name" in str(context.value)

        assert Acquisition.reject_non_iana_tz("America/Los_Angeles") == "America/Los_Angeles"
        assert Acquisition.reject_non_iana_tz(-7) == -7
        assert Acquisition.reject_non_iana_tz(None) is None

    def test_non_iana_tz_absent_from_schema(self):
        """The generated enum never advertises host timezone artifacts"""
        enum = Acquisition.model_json_schema()["properties"]["acquisition_start_tz"]["anyOf"][1]["enum"]
        assert not NON_IANA_TIMEZONES.intersection(enum)
        assert "America/Los_Angeles" in enum
