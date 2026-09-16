"""Unit tests for compatibility_check."""

from unittest.mock import MagicMock

import pytest

from biodata_schema.components.devices import Device
from biodata_schema.core.acquisition import Acquisition, StimulusEpoch
from biodata_schema.core.instrument import Instrument
from biodata_schema.utils.compatibility_check import InstrumentAcquisitionCompatibility
from examples.exaspim_acquisition import acq
from examples.exaspim_instrument import inst


class TestInstrumentAcquisitionCompatibility:
    """Unit tests for InstrumentAcquisitionCompatibility class."""

    def setup_method(self):
        """Set up mock instrument and acquisition objects for testing."""
        self.mock_instrument = MagicMock(spec=Instrument)
        self.mock_acquisition = MagicMock(spec=Acquisition)

        # Mock instrument attributes
        self.mock_instrument.instrument_id = "instrument_1"

        device0 = MagicMock(spec=Device)
        device0.name = "component_1"
        device1 = MagicMock(spec=Device)
        device1.name = "component_2"

        self.mock_instrument.components = [device0, device1]
        # Mock the get_component_names method to return the expected component names
        self.mock_instrument.get_component_names.return_value = ["component_1", "component_2"]

        # Mock acquisition attributes
        self.mock_acquisition.instrument_id = "instrument_1"
        self.mock_acquisition.data_streams = [MagicMock(active_devices=["component_1"])]
        self.mock_acquisition.stimulus_epochs = [MagicMock(active_devices=["component_2"])]

    def test_exaspim_example_compatibility(self):
        """Test compatibility of the exaspim example instrument and acquisition."""
        checker = InstrumentAcquisitionCompatibility(inst, acq)
        assert checker.run_compatibility_check() is None

    def test_compare_instrument_id_success(self):
        """Test that instrument IDs match."""
        checker = InstrumentAcquisitionCompatibility(self.mock_instrument, self.mock_acquisition)
        assert checker._compare_instrument_id() is None

    def test_compare_instrument_id_failure(self):
        """Test that instrument IDs mismatch raises ValueError."""
        self.mock_acquisition.instrument_id = "instrument_2"
        checker = InstrumentAcquisitionCompatibility(self.mock_instrument, self.mock_acquisition)
        error = checker._compare_instrument_id()
        assert isinstance(error, ValueError)
        assert "Instrument ID in acquisition" in str(error)

    def test_compare_stimulus_devices_success(self):
        """Test that stimulus devices in acquisition match instrument components."""
        checker = InstrumentAcquisitionCompatibility(self.mock_instrument, self.mock_acquisition)
        assert checker._compare_stimulus_devices() is None

    def test_compare_stimulus_devices_failure(self):
        """Test that mismatched stimulus devices raise ValueError."""
        epoch = MagicMock(spec=StimulusEpoch)
        epoch.active_devices = ["unknown_device"]
        self.mock_acquisition.stimulus_epochs = [epoch]
        checker = InstrumentAcquisitionCompatibility(self.mock_instrument, self.mock_acquisition)
        error = checker._compare_stimulus_devices()
        assert isinstance(error, ValueError)
        assert "Stimulus epoch device names in acquisition" in str(error)

    def test_run_compatibility_check_success(self):
        """Test that compatibility check passes when all comparisons succeed."""
        checker = InstrumentAcquisitionCompatibility(self.mock_instrument, self.mock_acquisition)
        assert checker.run_compatibility_check() is None

    def test_run_compatibility_check_failure(self):
        """Test that compatibility check raises ValueError when comparisons fail."""
        self.mock_acquisition.instrument_id = "instrument_2"
        checker = InstrumentAcquisitionCompatibility(self.mock_instrument, self.mock_acquisition)
        with pytest.raises(ValueError) as context:
            checker.run_compatibility_check()
        assert "Instrument ID in acquisition" in str(context.value)

    def test_compare_active_devices_missing_with_raise_false(self):
        """Test that missing active devices logs error when raise_for_missing_devices is False."""
        self.mock_acquisition.data_streams = [MagicMock(active_devices=["unknown_device"])]
        checker = InstrumentAcquisitionCompatibility(self.mock_instrument, self.mock_acquisition)
        error = checker._compare_active_devices(raise_for_missing_devices=False)
        assert error is None

    def test_compare_active_devices_missing_with_raise_true(self):
        """Test that missing active devices raise ValueError when raise_for_missing_devices is True."""
        self.mock_acquisition.data_streams = [MagicMock(active_devices=["unknown_device"])]
        checker = InstrumentAcquisitionCompatibility(self.mock_instrument, self.mock_acquisition)
        error = checker._compare_active_devices(raise_for_missing_devices=True)
        assert isinstance(error, ValueError)
        assert "Active devices" in str(error)
        assert "were not found in Instrument.components" in str(error)

    def test_run_compatibility_check_with_raise_for_missing_devices_false(self):
        """Test compatibility check with raise_for_missing_devices=False logs missing devices."""
        self.mock_acquisition.data_streams = [MagicMock(active_devices=["unknown_device"])]
        checker = InstrumentAcquisitionCompatibility(self.mock_instrument, self.mock_acquisition)
        assert checker.run_compatibility_check(raise_for_missing_devices=False) is None

    def test_run_compatibility_check_with_raise_for_missing_devices_true(self):
        """Test compatibility check with raise_for_missing_devices=True raises ValueError."""
        self.mock_acquisition.data_streams = [MagicMock(active_devices=["unknown_device"])]
        checker = InstrumentAcquisitionCompatibility(self.mock_instrument, self.mock_acquisition)
        with pytest.raises(ValueError) as context:
            checker.run_compatibility_check(raise_for_missing_devices=True)
        assert "Active devices" in str(context.value)
