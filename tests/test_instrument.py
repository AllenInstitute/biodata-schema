"""test Instrument"""

import json
from datetime import date
from unittest.mock import patch

import pytest
from biodata_models.coordinates import AnatomicalRelative
from biodata_models.harp_types import HarpDeviceType
from biodata_models.modalities import Modality
from biodata_models.organizations import Organization
from biodata_models.units import FrequencyUnit, PowerUnit
from pydantic import ValidationError

from biodata_schema.components.connections import Connection
from biodata_schema.components.coordinates import CoordinateSystem
from biodata_schema.components.devices import (
    Camera,
    CameraAssembly,
    CameraTarget,
    Computer,
    DAQChannel,
    Detector,
    DetectorType,
    Device,
    Disc,
    EphysAssembly,
    EphysProbe,
    FiberPatchCord,
    HarpDevice,
    Laser,
    LaserAssembly,
    Lens,
    LickSpout,
    LickSpoutAssembly,
    Manipulator,
    Microscope,
    NeuropixelsBasestation,
    Objective,
    Olfactometer,
    OlfactometerChannel,
    OlfactometerChannelType,
    ScanningStage,
)
from biodata_schema.components.identifiers import Software
from biodata_schema.components.measurements import Calibration
from biodata_schema.core.instrument import (
    DEVICES_REQUIRED,
    Instrument,
)
from examples.ephys_instrument import inst as ephys_instrument
from examples.slap2_instrument import dmds
from tests.coordinate_systems import BREGMA_ARI

dmd = dmds[0]

computer_foo = Computer(name="foo")
computer_ASDF = Computer(name="ASDF")
computer_W10XXX000 = Computer(name="W10XXX000")

microscope = Microscope(
    name="Microscope A",
)

daqs = [
    NeuropixelsBasestation(
        name="Neuropixels basestation",
        basestation_firmware_version="1",
        bsc_firmware_version="2",
        slot=0,
        manufacturer=Organization.IMEC,
        ports=[],
        channels=[
            DAQChannel(
                channel_name="123",
                channel_type="Analog Output",
            ),
            DAQChannel(
                channel_name="321",
                channel_type="Analog Output",
            ),
            DAQChannel(
                channel_name="234",
                channel_type="Digital Output",
            ),
            DAQChannel(
                channel_name="2354",
                channel_type="Digital Output",
            ),
        ],
    )
]

connections = [
    Connection(
        source_device="Neuropixels basestation",
        source_port="123",
        target_device="Laser A",
    ),
    Connection(
        source_device="Neuropixels basestation",
        source_port="321",
        target_device="Probe A",
    ),
    Connection(
        source_device="Neuropixels basestation",
        source_port="234",
        target_device="Camera A",
    ),
    Connection(
        source_device="Neuropixels basestation",
        source_port="2354",
        target_device="Disc A",
    ),
    Connection(
        source_device="Neuropixels basestation",
        target_device="foo",
    ),
    Connection(
        source_device="cam",
        target_device="ASDF",
    ),
    Connection(
        source_device="Neuropixels basestation",
        target_device="foo",
    ),
    Connection(
        source_device="Camera A",
        target_device="ASDF",
    ),
    Connection(
        source_device="Olfactometer",
        target_device="W10XXX000",
    ),
]

ems = [
    EphysAssembly(
        probes=[EphysProbe(probe_model="Neuropixels 1.0", name="Probe A")],
        manipulator=Manipulator(
            name="Probe manipulator",
            manufacturer=Organization.NEW_SCALE_TECHNOLOGIES,
            serial_number="4321",
        ),
        name="Ephys_assemblyA",
    )
]

laser = Laser(
    manufacturer=Organization.HAMAMATSU,
    serial_number="1234",
    name="Laser A",
    wavelength=488,
)

lms = [
    LaserAssembly(
        lasers=[
            Laser(
                manufacturer=Organization.HAMAMATSU,
                serial_number="1234",
                name="Laser A",
                wavelength=488,
            ),
        ],
        manipulator=Manipulator(
            name="Laser manipulator",
            manufacturer=Organization.NEW_SCALE_TECHNOLOGIES,
            serial_number="1234",
        ),
        name="Laser_assembly",
        collimator=Device(name="Collimator A"),
        fiber=FiberPatchCord(
            name="Bundle Branching Fiber-optic Patch Cord",
            manufacturer=Organization.DORIC,
            model="BBP(4)_200/220/900-0.37_Custom_FCM-4xMF1.25",
            core_diameter=200,
            numerical_aperture=0.37,
        ),
    )
]
cameras = [
    CameraAssembly(
        name="cam",
        target=CameraTarget.FACE,
        relative_position=[AnatomicalRelative.ANTERIOR, AnatomicalRelative.INFERIOR],
        lens=Lens(name="Camera lens", manufacturer=Organization.OTHER, notes="Manufacturer unknown"),
        camera=Camera(
            name="Camera A",
            detector_type=DetectorType.CAMERA,
            manufacturer=Organization.OTHER,
            data_interface="USB",
            frame_rate=144,
            frame_rate_unit=FrequencyUnit.HZ,
            sensor_width=1,
            sensor_height=1,
            chroma="Color",
            notes="Manufacturer unknown",
        ),
    )
]
scan_stage = ScanningStage(
    name="Sample stage Z",
    model="LS-50",
    manufacturer=Organization.ASI,
    stage_axis_direction="Detection axis",
    stage_axis_name="Z",
    travel=50,
)

stick_microscopes = [
    CameraAssembly(
        name="Assembly A",
        camera=Camera(
            name="Camera A",
            detector_type=DetectorType.CAMERA,
            manufacturer=Organization.OTHER,
            data_interface="USB",
            frame_rate=144,
            frame_rate_unit=FrequencyUnit.HZ,
            sensor_width=1,
            sensor_height=1,
            chroma="Color",
            notes="Manufacturer unknown",
        ),
        target=CameraTarget.BRAIN,
        relative_position=[AnatomicalRelative.SUPERIOR],
        lens=Lens(name="Lens A", manufacturer=Organization.OTHER, notes="Manufacturer unknown"),
    )
]
light_sources = [
    Laser(
        manufacturer=Organization.HAMAMATSU,
        serial_number="1234",
        name="Laser A",
        wavelength=488,
    )
]
detectors = [
    Detector(
        name="FLIR CMOS for Green Channel",
        serial_number="21396991",
        manufacturer=Organization.FLIR,
        model="BFS-U3-20S40M",
        detector_type=DetectorType.CAMERA,
        data_interface="USB",
        cooling="Air",
        immersion="air",
        bin_width=4,
        bin_height=4,
        bin_mode="Additive",
        crop_width=200,
        crop_height=200,
        gain=2,
        chroma="Monochrome",
        bit_depth=16,
    )
]
patch_cords = [
    FiberPatchCord(
        name="Bundle Branching Fiber-optic Patch Cord",
        manufacturer=Organization.DORIC,
        model="BBP(4)_200/220/900-0.37_Custom_FCM-4xMF1.25",
        core_diameter=200,
        numerical_aperture=0.37,
    )
]
objectives = [
    Objective(
        name="TLX Objective 1",
        numerical_aperture=0.2,
        magnification=3.6,
        manufacturer=Organization.LIFECANVAS,
        immersion="multi",
        notes="Thorlabs TL4X-SAP with LifeCanvas dipping cap and correction optics.",
    )
]
stimulus_devices = [
    Olfactometer(
        name="Olfactometer",
        manufacturer=Organization.CHAMPALIMAUD,
        model="1234",
        serial_number="213456",
        hardware_version="1",
        is_clock_generator=False,
        channels=[
            OlfactometerChannel(
                channel_index=0,
                channel_type=OlfactometerChannelType.CARRIER,
                flow_capacity=100,
            ),
            OlfactometerChannel(
                channel_index=1,
                channel_type=OlfactometerChannelType.ODOR,
                flow_capacity=100,
            ),
        ],
    ),
    LickSpoutAssembly(
        name="Lick spout assembly",
        lick_spouts=[
            LickSpout(
                name="Left spout",
                spout_diameter=1.2,
                solenoid_valve=Device(name="Solenoid Left"),
                lick_sensor=Device(
                    name="Lick-o-meter Left",
                ),
            ),
            LickSpout(
                name="Right spout",
                spout_diameter=1.2,
                solenoid_valve=Device(name="Solenoid Right"),
                lick_sensor=Device(
                    name="Lick-o-meter Right",
                ),
            ),
        ],
    ),
]
calibration = Calibration(
    calibration_date=date(2020, 10, 10),
    device_name="Laser A",
    description="Laser power calibration",
    input=[10, 40, 80],
    input_unit=PowerUnit.PERCENT,
    output=[2, 6, 10],
    output_unit=PowerUnit.MW,
)


class TestInstrument:
    """test instrument schemas"""

    def test_constructors(self):
        """always returns true"""

        with pytest.raises(ValidationError):
            Instrument()

        assert ephys_instrument is not None
        assert ephys_instrument.instrument_id in ephys_instrument.get_component_names()

    def test_other_camera_target(self):
        """Test that the camera_target being set to Other throws a validation error without notes"""

        camera_no_target = cameras[0].model_copy()
        camera_no_target.target = CameraTarget.OTHER

        with pytest.raises(ValidationError):
            Instrument(
                instrument_id="123_EPHYS1-OPTO_20220101",
                modification_date=date(2020, 10, 10),
                modalities=[Modality.ECEPHYS, Modality.FIB],
                global_coordinate_system="NotApplicable",
                components=[
                    *daqs,
                    camera_no_target,
                    *stick_microscopes,
                    *light_sources,
                    *lms,
                    *ems,
                    *detectors,
                    *patch_cords,
                    *stimulus_devices,
                    Disc(name="Disc A", radius=1),
                ],
                calibrations=[
                    Calibration(
                        calibration_date=date(2020, 10, 10),
                        device_name="Laser A",
                        description="Laser power calibration",
                        input=[10, 40, 80],
                        input_unit=PowerUnit.PERCENT,
                        output=[2, 6, 10],
                        output_unit=PowerUnit.MW,
                    )
                ],
                connections=[
                    Connection(
                        source_device="Olfactometer",
                        target_device="Laser A",
                    )
                ],
            )

        inst = Instrument(
            instrument_id="123_EPHYS1-OPTO_20220101",
            modification_date=date(2020, 10, 10),
            modalities=[Modality.ECEPHYS, Modality.FIB],
            global_coordinate_system="NotApplicable",
            components=[
                *daqs,
                camera_no_target,
                *stick_microscopes,
                *light_sources,
                *lms,
                *ems,
                *detectors,
                *patch_cords,
                *stimulus_devices,
                Disc(name="Disc A", radius=1),
            ],
            calibrations=[
                Calibration(
                    calibration_date=date(2020, 10, 10),
                    device_name="Laser A",
                    description="Laser power calibration",
                    input=[10, 40, 80],
                    input_unit=PowerUnit.PERCENT,
                    output=[2, 6, 10],
                    output_unit=PowerUnit.MW,
                )
            ],
            connections=[
                Connection(
                    source_device="Olfactometer",
                    target_device="Laser A",
                )
            ],
            notes="Camera target is Other",
        )
        assert inst is not None

    def test_missing_connections(self):
        """Validation error when connections are missing"""
        with pytest.raises(ValueError) as context:
            Instrument(
                instrument_id="123_EPHYS1-OPTO_20220101",
                modification_date=date(2020, 10, 10),
                modalities=[Modality.ECEPHYS, Modality.FIB],
                global_coordinate_system="NotApplicable",
                components=[
                    *daqs,
                    *cameras,
                    *stick_microscopes,
                    *light_sources,
                    *lms,
                    *ems,
                    *detectors,
                    *patch_cords,
                    *stimulus_devices,
                    Disc(name="Disc A", radius=1),
                    dmd,
                ],
                calibrations=[
                    Calibration(
                        calibration_date=date(2020, 10, 10),
                        device_name="Laser A",
                        description="Laser power calibration",
                        input=[10, 40, 80],
                        input_unit=PowerUnit.PERCENT,
                        output=[2, 6, 10],
                        output_unit=PowerUnit.MW,
                    )
                ],
                connections=[
                    Connection(
                        source_device="Not a real device",
                        target_device="Neuropixels basestation",
                    )
                ],
            )

        assert "Device name validation error: 'Not a real device'" in str(context.value)

        with pytest.raises(ValueError) as context:
            Instrument(
                instrument_id="123_EPHYS1-OPTO_20220101",
                modification_date=date(2020, 10, 10),
                modalities=[Modality.ECEPHYS, Modality.FIB],
                global_coordinate_system="NotApplicable",
                components=[
                    *daqs,
                    *cameras,
                    *stick_microscopes,
                    *light_sources,
                    *lms,
                    *ems,
                    *detectors,
                    *patch_cords,
                    *stimulus_devices,
                    Disc(name="Disc A", radius=1),
                    dmd,
                ],
                calibrations=[
                    Calibration(
                        calibration_date=date(2020, 10, 10),
                        device_name="Laser A",
                        description="Laser power calibration",
                        input=[10, 40, 80],
                        input_unit=PowerUnit.PERCENT,
                        output=[2, 6, 10],
                        output_unit=PowerUnit.MW,
                    )
                ],
                connections=[
                    Connection(
                        target_device="Not a real device",
                        source_device="Neuropixels basestation",
                    )
                ],
            )

        assert "Device name validation error: 'Not a real device'" in str(context.value)

    def test_validator_modality_device_missing(self):
        """Test that the modality -> device validator throws validation errors when devices are missing"""

        # Mapping is a dictionary of Modality -> List[Device groups]
        for modality_abbreviation, _ in DEVICES_REQUIRED.items():
            with pytest.raises(ValidationError):
                Instrument(
                    modalities=[Modality.from_abbreviation(modality_abbreviation)],
                    instrument_id="123_EPHYS1-OPTO_20220101",
                    global_coordinate_system="NotApplicable",
                    modification_date=date(2020, 10, 10),
                    components=[],
                    calibrations=[],
                )

    def test_validator_modality_device_present(self):
        """Test that the modality -> device validator does not throw validation errors when devices are present"""

        # Mapping is a dictionary of Modality -> List[Device groups]
        for modality_abbreviation, _ in DEVICES_REQUIRED.items():
            inst = Instrument(
                modalities=[Modality.from_abbreviation(modality_abbreviation)],
                instrument_id="123_EPHYS1-OPTO_20220101",
                modification_date=date(2020, 10, 10),
                global_coordinate_system="NotApplicable",
                components=[
                    *daqs,
                    *cameras,
                    *stick_microscopes,
                    *light_sources,
                    *lms,
                    *ems,
                    *detectors,
                    *patch_cords,
                    *stimulus_devices,
                    *objectives,
                    dmd,
                    scan_stage,
                    microscope,
                ],
                calibrations=[],
            )
            assert inst is not None

    def test_serialize_modalities(self):
        """Tests that modalities serializer can handle different types"""
        expected_modalities = [{"name": "Extracellular electrophysiology", "abbreviation": "ecephys"}]
        # Case 1: Modality is a class instance
        instrument_instance_modality = Instrument.model_construct(
            instrument_id="123_EPHYS1-OPTO_20220101",
            modalities={Modality.ECEPHYS},  # Example with a valid Modality instance
            global_coordinate_system=BREGMA_ARI,
        )
        instrument_json = instrument_instance_modality.model_dump_json()
        instrument_data = json.loads(instrument_json)
        assert instrument_data["modalities"] == expected_modalities

        # Case 2: Modality is a dictionary when Instrument is constructed from JSON
        instrument_dict_modality = Instrument.model_construct(**instrument_data)
        instrument_dict_json = instrument_dict_modality.model_dump_json()
        instrument_dict_data = json.loads(instrument_dict_json)
        assert instrument_dict_data["modalities"] == expected_modalities

    def test_coordinate_validator(self):
        """Test the coordinate_validator function"""

        camera = Camera(
            name="Camera A",
            detector_type=DetectorType.CAMERA,
            manufacturer=Organization.OTHER,
            data_interface="USB",
            frame_rate=144,
            frame_rate_unit=FrequencyUnit.HZ,
            sensor_width=1,
            sensor_height=1,
            chroma="Color",
            notes="Manufacturer unknown",
        )

        # Create a matching CameraAssembly
        camera_assembly = CameraAssembly(
            name="Assembly B",
            camera=camera,
            target=CameraTarget.BRAIN,
            relative_position=[AnatomicalRelative.SUPERIOR],
            lens=Lens(name="Lens A", manufacturer=Organization.OTHER, notes="Manufacturer unknown"),
        )

        inst = Instrument(
            instrument_id="123_EPHYS1-OPTO_20220101",
            modification_date=date(2020, 10, 10),
            modalities=[Modality.ECEPHYS, Modality.FIB],
            global_coordinate_system="NotApplicable",
            components=[
                *daqs,
                *cameras,
                *stick_microscopes,
                *light_sources,
                *lms,
                *ems,
                *detectors,
                *patch_cords,
                *stimulus_devices,
                scan_stage,
                Disc(name="Disc A", radius=1),
                camera_assembly,
                computer_ASDF,
            ],
            calibrations=[],
            connections=[
                Connection(
                    source_device="Camera A",
                    target_device="ASDF",
                )
            ],
        )
        assert inst is not None

    def test_instrument_addition(self):
        """Test the __add__ method of Instrument"""

        # Create a copy of the ephys_instrument for testing
        inst1 = ephys_instrument.model_copy(deep=True)
        inst2 = ephys_instrument.model_copy(deep=True)

        # Test successful addition
        combined = inst1 + inst2

        # Verify the combined instrument has the expected properties
        assert combined.instrument_id == inst1.instrument_id
        assert combined.location == inst1.location
        assert combined.global_coordinate_system == inst1.global_coordinate_system
        assert combined.temperature_control == inst1.temperature_control

        coordinate_free_instrument = Instrument(
            location=inst1.location,
            instrument_id="coordinate-free-instrument",
            modification_date=inst1.modification_date,
            modalities=[],
            global_coordinate_system="NotApplicable",
            temperature_control=inst1.temperature_control,
            components=[Computer(name="Coordinate-free computer")],
        )
        combined_with_coordinate_free = inst1 + coordinate_free_instrument
        assert combined_with_coordinate_free.global_coordinate_system == inst1.global_coordinate_system

        # Check that modalities are combined and sorted (should be the same since we're adding identical instruments)
        assert len(combined.modalities) == len(set(inst1.modalities + inst2.modalities))

        # Check that components are deduplicated (same names from both instruments result in keeping only one)
        assert len(combined.components) == len(inst1.components)

        # Check that connections are combined
        assert len(combined.connections) == len(inst1.connections) + len(inst2.connections)

        # Check that calibrations are combined (if they exist)
        expected_calibrations_len = len(inst1.calibrations or []) + len(inst2.calibrations or [])
        actual_calibrations_len = len(combined.calibrations or [])
        assert actual_calibrations_len == expected_calibrations_len

        # Test incompatible schema versions
        inst1_orig_schema_v = inst1.schema_version
        inst1.schema_version = "0.1.0"

        with pytest.raises(ValueError) as context:
            inst1 + inst2
        assert "Cannot combine Instrument objects with different schema versions" in str(context.value)

        # Restore schema version for next tests
        inst1.schema_version = inst1_orig_schema_v

        # Test that instrument_id differences are merged in alphabetical order
        inst2.instrument_id = "different-instrument-id"
        inst3 = inst1 + inst2
        assert inst3.instrument_id == "EPHYS1_different-instrument-id"

        # Test incompatible locations
        inst2.instrument_id = inst1.instrument_id  # Reset to same
        inst2.location = "Different Location"
        with pytest.raises(ValueError) as context:
            inst1 + inst2
        assert "Cannot combine Instrument objects that differ in key fields" in str(context.value)

        # Test notes combination
        inst2.location = inst1.location  # Reset to same
        inst1.notes = "First note"
        inst2.notes = "Second note"
        combined = inst1 + inst2
        assert "First note" in combined.notes
        assert "Second note" in combined.notes
        assert "\n" in combined.notes  # Should be joined with newline

        # Test notes combination with None values
        inst1.notes = "Only note"
        inst2.notes = None
        combined = inst1 + inst2
        assert combined.notes == "Only note"

        inst1.notes = None
        inst2.notes = "Only note"
        combined = inst1 + inst2
        assert combined.notes == "Only note"

    def test_duplicate_non_harp_device_components(self):
        """Test that duplicate non-HarpDevice components log an error when combining instruments"""

        inst1 = Instrument(
            instrument_id="test_inst",
            modification_date=date(2020, 10, 10),
            modalities=[Modality.ECEPHYS],
            global_coordinate_system="NotApplicable",
            components=[Computer(name="Computer1")],
        )
        inst2 = Instrument(
            instrument_id="test_inst",
            modification_date=date(2020, 10, 10),
            modalities=[Modality.ECEPHYS],
            global_coordinate_system="NotApplicable",
            components=[Computer(name="Computer1")],
        )

        with patch("biodata_schema.core.instrument.logger") as mock_logger:
            combined = inst1 + inst2
            mock_logger.error.assert_called_once()
            error_call_args = mock_logger.error.call_args[0][0]
            assert "Computer1" in error_call_args
            assert "duplicated" in error_call_args

        assert len(combined.components) == 1

    def test_duplicate_harp_clock_generator_devices(self):
        """Test that duplicate HarpDevice clock generators are allowed when combining instruments"""

        harp_clock_gen = HarpDevice(
            name="Harp Clock Generator",
            harp_device_type=HarpDeviceType.CLOCKSYNCHRONIZER,
            core_version="2.1",
            channels=[],
            is_clock_generator=True,
        )

        inst1 = Instrument(
            instrument_id="test_inst",
            modification_date=date(2020, 10, 10),
            modalities=[Modality.ECEPHYS],
            global_coordinate_system="NotApplicable",
            components=[harp_clock_gen],
        )
        inst2 = Instrument(
            instrument_id="test_inst",
            modification_date=date(2020, 10, 10),
            modalities=[Modality.ECEPHYS],
            global_coordinate_system="NotApplicable",
            components=[harp_clock_gen.model_copy(deep=True)],
        )

        with patch("biodata_schema.core.instrument.logger") as mock_logger:
            combined = inst1 + inst2
            mock_logger.info.assert_called_once()
            info_call_args = mock_logger.info.call_args[0][0]
            assert "Harp Clock Generator" in info_call_args

        assert len(combined.components) == 1

    def test_duplicate_non_harp_device_with_clock_generator_attribute(self):
        """Test that duplicate non-HarpDevice components with is_clock_generator log error"""

        harp_clock_gen = HarpDevice(
            name="CustomClockGenerator",
            harp_device_type=HarpDeviceType.BEHAVIOR,
            is_clock_generator=True,
            channels=[],
        )

        harp_non_clock_gen = HarpDevice(
            name="CustomClockGenerator",
            harp_device_type=HarpDeviceType.BEHAVIOR,
            is_clock_generator=False,
            channels=[],
        )

        inst1 = Instrument(
            instrument_id="test_inst",
            modification_date=date(2020, 10, 10),
            modalities=[Modality.BEHAVIOR],
            global_coordinate_system="NotApplicable",
            components=[
                harp_clock_gen,
                LickSpoutAssembly(
                    name="Lick spout assembly A",
                    lick_spouts=[
                        LickSpout(
                            name="Left spout",
                            spout_diameter=1.2,
                            solenoid_valve=Device(name="Solenoid Left"),
                            lick_sensor=Device(name="Lick-o-meter Left"),
                        ),
                    ],
                ),
            ],
        )
        inst2 = Instrument(
            instrument_id="test_inst",
            modification_date=date(2020, 10, 10),
            modalities=[Modality.BEHAVIOR],
            global_coordinate_system="NotApplicable",
            components=[
                harp_non_clock_gen,
                LickSpoutAssembly(
                    name="Lick spout assembly B",
                    lick_spouts=[
                        LickSpout(
                            name="Left spout",
                            spout_diameter=1.2,
                            solenoid_valve=Device(name="Solenoid Left"),
                            lick_sensor=Device(name="Lick-o-meter Left"),
                        ),
                    ],
                ),
            ],
        )

        with patch("biodata_schema.core.instrument.logger") as mock_logger:
            combined = inst1 + inst2
            mock_logger.error.assert_called_once()
            error_call_args = mock_logger.error.call_args[0][0]
            assert "CustomClockGenerator" in error_call_args
            assert "duplicated" in error_call_args

        assert len(combined.components) == 3

    def test_validate_unique_component_names(self):
        """Test that duplicate component names raise an error"""
        duplicate_component = ephys_instrument.components[0].model_copy(deep=True)
        inst_with_dup = Instrument.model_construct(
            instrument_id=ephys_instrument.instrument_id,
            modification_date=ephys_instrument.modification_date,
            modalities=ephys_instrument.modalities,
            global_coordinate_system=ephys_instrument.global_coordinate_system,
            components=list(ephys_instrument.components) + [duplicate_component],
            connections=ephys_instrument.connections or [],
            calibrations=ephys_instrument.calibrations,
        )

        with pytest.raises(ValueError) as context:
            inst_with_dup.validate_unique_component_names()
        assert duplicate_component.name in str(context.value)

        inst_no_dup = Instrument.model_construct(
            instrument_id=ephys_instrument.instrument_id,
            modification_date=ephys_instrument.modification_date,
            modalities=ephys_instrument.modalities,
            global_coordinate_system=ephys_instrument.global_coordinate_system,
            components=list(ephys_instrument.components),
            connections=ephys_instrument.connections or [],
            calibrations=ephys_instrument.calibrations,
        )

        assert inst_no_dup.validate_unique_component_names() is inst_no_dup

    @pytest.mark.parametrize("endpoint", ["source_device", "target_device"])
    def test_connections_reject_software_names(self, endpoint):
        """Software is not a device endpoint even when it is attached to a camera."""
        camera = Camera(
            name="Camera",
            detector_type=DetectorType.CAMERA,
            manufacturer=Organization.AIND,
            data_interface="USB",
            recording_software=Software(name="Bonsai", version="2.5"),
        )
        values = dict(
            instrument_id="rig",
            modification_date=date(2026, 1, 1),
            modalities=[],
            global_coordinate_system="NotApplicable",
            components=[camera],
        )
        instrument = Instrument(**values)
        assert instrument.get_component_names() == ["Camera", "rig"]
        endpoints = dict(source_device="Camera", target_device="rig")
        assert Instrument(**values, connections=[Connection(**endpoints)])
        endpoints[endpoint] = "Bonsai"
        with pytest.raises(ValidationError, match="Bonsai.*not part of the instrument"):
            Instrument(**values, connections=[Connection(**endpoints)])

    def test_shared_software_name_allowed(self):
        """The same Software recorded on several devices is not a name collision"""
        shared_software = Software(name="Bonsai", version="2.5")

        def _camera(name):
            """Build a camera assembly recording with the shared software"""
            return CameraAssembly(
                name=name,
                target=CameraTarget.BRAIN,
                relative_position=[AnatomicalRelative.SUPERIOR],
                camera=Camera(
                    name=f"{name} Detector",
                    detector_type=DetectorType.CAMERA,
                    manufacturer=Organization.OTHER,
                    data_interface="USB",
                    frame_rate=144,
                    frame_rate_unit=FrequencyUnit.HZ,
                    sensor_width=1,
                    sensor_height=1,
                    chroma="Color",
                    notes="Manufacturer unknown",
                    recording_software=shared_software,
                ),
                lens=Lens(name=f"{name} Lens", manufacturer=Organization.OTHER, notes="Manufacturer unknown"),
            )

        inst = Instrument.model_construct(
            instrument_id=ephys_instrument.instrument_id,
            modification_date=ephys_instrument.modification_date,
            modalities=ephys_instrument.modalities,
            global_coordinate_system=ephys_instrument.global_coordinate_system,
            components=[_camera("Camera One"), _camera("Camera Two")],
            connections=[],
            calibrations=[],
        )
        assert inst.validate_unique_component_names() is inst

    def test_coordinate_system_names_ignored(self):
        """Names on coordinate systems are not component collisions"""
        inst = Instrument.model_construct(
            instrument_id=ephys_instrument.instrument_id,
            modification_date=ephys_instrument.modification_date,
            modalities=ephys_instrument.modalities,
            global_coordinate_system=ephys_instrument.global_coordinate_system,
            components=[
                CameraAssembly.model_construct(
                    name="Camera assembly one",
                    local_coordinate_system=CoordinateSystem.model_construct(name="Shared coordinate system"),
                ),
                CameraAssembly.model_construct(
                    name="Camera assembly two",
                    local_coordinate_system=CoordinateSystem.model_construct(name="Shared coordinate system"),
                ),
            ],
            connections=[],
            calibrations=[],
        )

        assert inst.validate_unique_component_names() is inst

    def test_distinct_objects_sharing_a_name_rejected(self):
        """Two different devices with the same name are still a collision"""
        inst = Instrument.model_construct(
            instrument_id=ephys_instrument.instrument_id,
            modification_date=ephys_instrument.modification_date,
            modalities=ephys_instrument.modalities,
            global_coordinate_system=ephys_instrument.global_coordinate_system,
            components=[Disc(name="Shared", radius=1), Disc(name="Shared", radius=2)],
            connections=[],
            calibrations=[],
        )
        with pytest.raises(ValueError) as context:
            inst.validate_unique_component_names()
        assert "Shared" in str(context.value)


class TestConnection:
    """Test the Connection schema"""

    def test_connection(self):
        """Test the Connection schema"""

        connection = Connection(
            source_device="Neuropixels basestation",
            source_port="123",
            target_device="Laser A",
        )
        assert connection is not None

        # Test that a simple connection with valid structure is created successfully
        simple_connection = Connection(
            source_device="Camera A",
            target_device="Invalid Target",
        )
        assert simple_connection is not None

    def test_validate_modalities_sorting(self):
        """Test that validate_modalities sorts modalities by their name"""

        # Create unsorted modalities
        unsorted_modalities = [
            Modality.FIB,
            Modality.ECEPHYS,
            Modality.BEHAVIOR_VIDEOS,
        ]

        # Expected sorted modalities
        expected_sorted_modalities = [
            Modality.BEHAVIOR_VIDEOS.abbreviation,
            Modality.ECEPHYS.abbreviation,
            Modality.FIB.abbreviation,
        ]

        # Create an instrument with unsorted modalities
        inst = Instrument(
            instrument_id="123_EPHYS1-OPTO_20220101",
            modification_date=date(2020, 10, 10),
            modalities=unsorted_modalities,
            global_coordinate_system="NotApplicable",
            components=[
                *daqs,
                *cameras,
                *stick_microscopes,
                *light_sources,
                *lms,
                *ems,
                *detectors,
                *patch_cords,
                *stimulus_devices,
                scan_stage,
                Disc(name="Disc A", radius=1),
                computer_ASDF,
                computer_foo,
                computer_W10XXX000,
            ],
            connections=connections,
            calibrations=[],
        )

        inst_modality_abbr = [modality.abbreviation for modality in inst.modalities]
        # Validate that the modalities are sorted
        assert inst_modality_abbr == expected_sorted_modalities
