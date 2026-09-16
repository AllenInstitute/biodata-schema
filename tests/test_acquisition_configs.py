"""Tests for the configs module"""

from decimal import Decimal

import pytest
from biodata_models.brain_atlas import CCFv3
from biodata_models.units import AngleUnit, FrequencyUnit, SizeUnit, TimeUnit, VolumeUnit
from pydantic import ValidationError

from biodata_schema.components.configs import (
    Channel,
    DetectorConfig,
    ImageSPIM,
    ImagingConfig,
    LaserConfig,
    LickSpoutConfig,
    Liquid,
    MRAcquisitionType,
    MRIScan,
    PlanarImage,
    Plane,
    SamplingStrategy,
    Scale,
    SubjectPosition,
    Valence,
)
from biodata_schema.components.coordinates import Affine, Translation
from tests.coordinate_systems import SPIM_IJK


class TestMRIScan:
    """Tests for the MRIScan class"""

    def test_validate_non_setup_success(self):
        """Test validate_non_setup method with valid primary scan data"""
        scan = MRIScan(
            device_name="MRI Scanner",
            index=1,
            mr_acquisition_type=MRAcquisitionType.SCAN_3D,
            setup=False,
            pulse_sequence_type="RARE",
            echo_time=Decimal("10.0"),
            echo_time_unit=TimeUnit.MS,
            repetition_time=Decimal("2000.0"),
            repetition_time_unit=TimeUnit.MS,
            subject_position=SubjectPosition.PRONE,
            additional_scan_parameters={},
            affine_transform=[
                Affine(
                    affine_transform=[[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]],
                ),
                Translation(
                    translation=[1, 2, 3],
                ),
            ],
            resolution=Scale(
                scale=[0.5, 0.4375, 0.52],
            ),
            resolution_unit=SizeUnit.MM,
        )
        assert scan is not None

    def test_validate_non_setup_failure(self):
        """Test validate_non_setup method with invalid primary scan data"""
        invalid_data = {
            "device_name": "MRI Scanner",
            "index": 1,
            "mr_acquisition_type": MRAcquisitionType.SCAN_3D,
            "setup": False,
            "pulse_sequence_type": "RARE",
            "echo_time": Decimal("10.0"),
            "repetition_time": Decimal("2000.0"),
            "subject_position": SubjectPosition.PRONE,
            "additional_scan_parameters": {},
        }
        with pytest.raises(ValidationError):
            MRIScan(**invalid_data)

    def test_validate_primary_missing_fields(self):
        """Test that missing fields raise ValidationError"""

        with pytest.raises(ValidationError) as context:
            MRIScan(
                device_name="MRI Scanner",
                index=1,
                mr_acquisition_type=MRAcquisitionType.SCAN_3D,
                setup=False,
                pulse_sequence_type="RARE",
                echo_time=Decimal("10.0"),
                echo_time_unit=TimeUnit.MS,
                repetition_time=Decimal("2000.0"),
                repetition_time_unit=TimeUnit.MS,
                subject_position=SubjectPosition.PRONE,
                additional_scan_parameters={},
                resolution_unit=SizeUnit.MM,
            )

        assert "Primary scan must have affine_transform and resolution fields" in str(context.value)


class TestLickSpoutConfig:
    """Tests for the LickSpoutConfig class"""

    def test_validate_other_success(self):
        """Test validate_other method with valid data"""
        lick_spout = LickSpoutConfig(
            device_name="Spout1",
            solution=Liquid.WATER,
            solution_valence=Valence.POSITIVE,
            volume=1.0,
            volume_unit=VolumeUnit.ML,
            relative_position=[],
        )
        assert lick_spout is not None

    def test_validate_other_failure(self):
        """Test validate_other method with invalid data"""
        with pytest.raises(ValueError) as context:
            LickSpoutConfig(
                device_name="Spout1",
                solution=Liquid.OTHER,
                solution_valence=Valence.POSITIVE,
                volume=1.0,
                volume_unit=VolumeUnit.ML,
                relative_position=[],
            )
        assert (
            "Notes cannot be empty if LickSpoutConfig.solution is Other."
            "Describe the solution in the notes field." in str(context.value)
        )


class TestImagingConfig:
    """Tests for the ImagingConfig class"""

    def setup_method(self):
        """Set up common test data"""
        self.channel1 = Channel(
            channel_name="Channel1",
            detector=DetectorConfig(
                device_name="Detector1",
                exposure_time=Decimal("10.0"),
                trigger_type="Internal",
            ),
            light_sources=[
                LaserConfig(
                    device_name="Laser1",
                    wavelength=488,
                )
            ],
        )
        self.channel2 = Channel(
            channel_name="Channel2",
            detector=DetectorConfig(
                device_name="Detector2",
                exposure_time=Decimal("20.0"),
                trigger_type="External",
            ),
            light_sources=[
                LaserConfig(
                    device_name="Laser2",
                    wavelength=561,
                )
            ],
        )
        self.coordinate_system = SPIM_IJK
        self.sampling_strategy = SamplingStrategy(
            frame_rate=30.0,
            frame_rate_unit=FrequencyUnit.HZ,
        )

    def test_check_image_channels_success(self):
        """Test check_image_channels validator with valid data"""
        imaging_config = ImagingConfig(
            device_name="ImagingDevice",
            channels=[self.channel1, self.channel2],
            images=[
                PlanarImage(
                    channel_name="Channel1",
                    image_to_acquisition_transform=[
                        Translation(
                            translation=[0, 0],
                        ),
                    ],
                    dimensions=Scale(
                        scale=[512, 512],
                    ),
                    planes=[
                        Plane(
                            depth=150,
                            depth_unit="micrometer",
                            targeted_structure=CCFv3.HPF,
                            power=10,
                            power_unit="milliwatt",
                        ),
                    ],
                ),
            ],
            sampling_strategy=self.sampling_strategy,
            local_coordinate_system=self.coordinate_system,
        )
        assert imaging_config is not None

    def test_check_image_channels_failure(self):
        """Test check_image_channels validator with invalid data"""
        with pytest.raises(ValidationError) as context:
            ImagingConfig(
                device_name="ImagingDevice",
                channels=[self.channel1],
                images=[
                    PlanarImage(
                        channel_name="InvalidChannel",
                        image_to_acquisition_transform=[
                            Translation(
                                translation=[0, 0],
                            ),
                        ],
                        dimensions=Scale(
                            scale=[512, 512],
                        ),
                        planes=[
                            Plane(
                                depth=150,
                                depth_unit="micrometer",
                                targeted_structure=CCFv3.HPF,
                                power=10,
                                power_unit="milliwatt",
                            ),
                        ],
                    )
                ],
                sampling_strategy=self.sampling_strategy,
                local_coordinate_system=self.coordinate_system,
            )
        assert "Channel InvalidChannel must be defined in the ImagingConfig.channels list" in str(context.value)

    def test_require_cs_images_success(self):
        """Test require_cs_images validator with valid data"""
        imaging_config = ImagingConfig(
            device_name="ImagingDevice",
            channels=[self.channel1],
            images=[
                ImageSPIM(
                    channel_name="Channel1",
                    file_name="test_image.tiff",
                    image_to_acquisition_transform=[
                        Affine(affine_transform=[[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [0, 0, 0, 1]]),
                    ],
                    imaging_angle=45,
                    imaging_angle_unit=AngleUnit.DEG,
                ),
            ],
            local_coordinate_system=self.coordinate_system,
        )
        assert imaging_config is not None

    def test_require_cs_images_failure(self):
        """Test require_cs_images validator with missing coordinate system"""
        with pytest.raises(ValidationError) as context:
            ImagingConfig(
                device_name="ImagingDevice",
                channels=[self.channel1],
                images=[
                    ImageSPIM(
                        channel_name="Channel1",
                        file_name="test_image.tiff",
                        image_to_acquisition_transform=[
                            Affine(affine_transform=[[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [0, 0, 0, 1]]),
                        ],
                        imaging_angle=45,
                        imaging_angle_unit=AngleUnit.DEG,
                    ),
                ],
                local_coordinate_system=None,
            )
        assert (
            "ImagingConfig.local_coordinate_system is required when ImagingConfig.images are ImageSPIM objects"
            in str(context.value)
        )


class TestAirPuffConfig:
    """Tests for the AirPuffConfig class"""
