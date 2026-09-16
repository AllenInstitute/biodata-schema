"""test Device models"""

import pytest
from biodata_models.coordinates import AnatomicalRelative
from biodata_models.harp_types import HarpDeviceType
from biodata_models.organizations import Organization
from biodata_models.units import UnitlessUnit
from pydantic import ValidationError

from biodata_schema.components.coordinates import Translation
from biodata_schema.components.devices import (
    AdditionalImagingDevice,
    DataInterface,
    Detector,
    DetectorType,
    Device,
    DevicePosition,
    Filter,
    FilterType,
    HarpDevice,
    ImagingDeviceType,
    ImmersionMedium,
    Monitor,
    Objective,
)
from tests.coordinate_systems import BREGMA_ARI


class TestDevice:
    """tests device schemas"""

    def test_other_validators(self):
        """tests validators which require notes when an instance of 'other' is used"""

        with pytest.raises(ValueError) as e1:
            Device(name="test_device", manufacturer=Organization.OTHER, notes="")

        assert "Device.notes cannot be empty if manufacturer is 'other'" in str(e1.value)

        with pytest.raises(ValueError) as e2:
            Detector(
                name="test_detector",
                manufacturer=Organization.HAMAMATSU,
                detector_type=DetectorType.OTHER,
                immersion=ImmersionMedium.OTHER,
                data_interface=DataInterface.OTHER,
            )

        assert "Value error, Notes cannot be empty" in str(e2.value)
        assert "'immersion', 'detector_type', 'data_interface'" in str(e2.value)

        with pytest.raises(ValueError) as e3:
            HarpDevice(
                name="test_harp",
                harp_device_type=HarpDeviceType.BEHAVIOR,
                data_interface=DataInterface.OTHER,
                is_clock_generator=False,
            )

        assert "Value error, Notes cannot be empty" in str(e3.value)
        assert "data_interface" in str(e3.value)

        HarpDevice(
            name="test_harp",
            harp_device_type=HarpDeviceType.BEHAVIOR,
            data_interface=DataInterface.USB,
            is_clock_generator=False,
        )

        with pytest.raises(ValueError) as e4:
            Objective(name="test_objective", numerical_aperture=0.5, magnification=10, immersion=ImmersionMedium.OTHER)

        assert "Value error, Notes cannot be empty if immersion is Other" in str(e4.value)

    def test_additional_imaging_device(self):
        """tests the additional imaging device validator"""
        with pytest.raises(ValueError) as e5:
            AdditionalImagingDevice(name="test_additional_imaging", imaging_device_type=ImagingDeviceType.OTHER)

        assert "Notes cannot be empty if imaging_device_type" in str(e5.value)

        valid = AdditionalImagingDevice(
            name="test_additional_imaging",
            imaging_device_type=ImagingDeviceType.OTHER,
            notes="test notes",
        )
        assert valid.name == "test_additional_imaging"

    def test_position_device(self):
        """Test that the DevicePosition validator gets raised properly"""

        # Test with both transform and coordinate_system set
        valid_positioned = DevicePosition(
            relative_position=[AnatomicalRelative.SUPERIOR],
            transform=[
                Translation(
                    translation=[1, 1, 1],
                )
            ],
            local_coordinate_system=BREGMA_ARI,
        )
        assert valid_positioned.transform is not None
        assert valid_positioned.local_coordinate_system is not None

        # Test with both transform and coordinate_system unset
        valid_positioned_unset = DevicePosition(
            relative_position=[AnatomicalRelative.SUPERIOR],
        )
        assert valid_positioned_unset.transform is None
        assert valid_positioned_unset.local_coordinate_system is None

        # Test with transform set but coordinate_system unset
        with pytest.raises(ValueError) as e1:
            DevicePosition(
                relative_position=[AnatomicalRelative.SUPERIOR],
                transform=[
                    Translation(
                        translation=[1, 1, 1],
                    )
                ],
            )
        assert (
            "DevicePosition.transform and DevicePosition.local_coordinate_system must "
            "either both be set or both be unset"
        ) in str(e1.value)

        # Test with coordinate_system set but transform unset
        with pytest.raises(ValueError) as e2:
            DevicePosition(
                relative_position=[AnatomicalRelative.SUPERIOR],
                local_coordinate_system=BREGMA_ARI,
            )
        assert (
            "DevicePosition.transform and DevicePosition.local_coordinate_system must "
            "either both be set or both be unset"
        ) in str(e2.value)


class TestFilter:
    """tests filter schemas"""

    def test_filter(self):
        """tests the filter validator"""

        # Test valid single center wavelength
        valid_filter_single = Filter(
            name="test_filter",
            filter_type=FilterType.BANDPASS,
            manufacturer=Organization.CHROMA,
            center_wavelength=500,
        )
        assert valid_filter_single.center_wavelength == 500

        # Test valid multiple center wavelengths
        valid_filter_multi = Filter(
            name="test_filter_multi",
            filter_type=FilterType.MULTI_NOTCH,
            manufacturer=Organization.CHROMA,
            center_wavelength=[450, 550, 650],
        )
        assert valid_filter_multi.center_wavelength == [450, 550, 650]

        # Test error for multi-band filter with single center wavelength
        with pytest.raises(ValueError) as e1:
            Filter(
                name="test_filter_multi_single",
                filter_type=FilterType.MULTIBAND,
                manufacturer=Organization.CHROMA,
                center_wavelength=500,
            )
        assert "center_wavelength must be a list of wavelengths" in str(e1.value)

        # Test error for single-band filter with multiple center wavelengths
        with pytest.raises(ValueError) as e2:
            Filter(
                name="test_filter_single_multi",
                filter_type=FilterType.BANDPASS,
                manufacturer=Organization.CHROMA,
                center_wavelength=[450, 550],
            )
        assert "center_wavelength must be a single wavelength" in str(e2.value)

        # Test with MULTI_NOTCH filter type and single wavelength (should fail)
        with pytest.raises(ValueError) as e3:
            Filter(
                name="test_filter_notch_single",
                filter_type=FilterType.MULTI_NOTCH,
                manufacturer=Organization.CHROMA,
                center_wavelength=500,
            )
        assert "center_wavelength must be a list of wavelengths" in str(e3.value)


class TestDAQChannel:
    """tests DAQChannel schemas"""


class TestMonitor:
    """tests Monitor schemas"""

    @pytest.mark.parametrize("setting", ["contrast", "brightness"])
    def test_zero_setting_requires_units(self, setting):
        """Zero is a supplied monitor setting, not a missing value."""
        values = dict(
            name="test_monitor",
            manufacturer=Organization.ASUS,
            refresh_rate=60,
            width=1920,
            height=1080,
            viewing_distance=15.0,
            relative_position=[],
        )
        assert getattr(Monitor(**values), setting) is None
        values[setting] = 0
        with pytest.raises(ValidationError, match=f"Unit {setting}_unit is required"):
            Monitor(**values)
        values[f"{setting}_unit"] = UnitlessUnit.PERCENT
        assert getattr(Monitor(**values), setting) == 0

    def test_contrast_brightness_units_not_inferred(self):
        """Units for contrast and brightness are no longer filled in automatically"""

        with pytest.raises(ValidationError) as context:
            Monitor(
                name="test_monitor",
                manufacturer=Organization.ASUS,
                refresh_rate=60,
                width=1920,
                height=1080,
                viewing_distance=15.0,
                relative_position=[AnatomicalRelative.SUPERIOR],
                contrast=50,
                brightness=75,
            )
        assert "Unit contrast_unit is required when contrast is set" in str(context.value)

        monitor_with_explicit_units = Monitor(
            name="test_monitor",
            manufacturer=Organization.ASUS,
            refresh_rate=60,
            width=1920,
            height=1080,
            viewing_distance=15.0,
            relative_position=[AnatomicalRelative.SUPERIOR],
            contrast=50,
            contrast_unit=UnitlessUnit.PERCENT,
            brightness=75,
            brightness_unit=UnitlessUnit.PERCENT,
        )
        assert monitor_with_explicit_units.contrast_unit == UnitlessUnit.PERCENT
        assert monitor_with_explicit_units.brightness_unit == UnitlessUnit.PERCENT
