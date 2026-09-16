"""Tests instrument acquisition compatibility check"""

import pytest

from biodata_schema.utils.compatibility_check import InstrumentAcquisitionCompatibility
from examples.ephys_acquisition import acquisition as ephys_acquisition
from examples.ephys_instrument import inst as ephys_instrument
from examples.exaspim_acquisition import acq as exaspim_acquisition
from examples.exaspim_instrument import inst as exaspim_instrument
from examples.fip_ophys_instrument import instrument as ophys_instrument
from examples.ophys_acquisition import a as ophys_acquisition


class TestInstrumentAcquisitionCompatibility:
    """Tests InstrumentAcquisitionCompatibility class"""

    def setup_method(self):
        """Set up test data"""
        self.ephys_instrument = ephys_instrument.model_copy()
        self.ephys_acquisition = ephys_acquisition.model_copy()
        self.exaspim_instrument = exaspim_instrument.model_copy()
        self.exaspim_acquisition = exaspim_acquisition.model_copy()
        self.ophys_instrument = ophys_instrument.model_copy()
        self.ophys_acquisition = ophys_acquisition.model_copy()

    def test_check_examples_compatibility(self):
        """Tests that examples are compatible"""
        # check that ephys acquisition and instrument are synced
        example_ephys_check = InstrumentAcquisitionCompatibility(
            instrument=self.ephys_instrument, acquisition=self.ephys_acquisition
        )
        assert example_ephys_check.run_compatibility_check() is None

        # check that exaspim acquisition and instrument are synced
        example_exaspim_check = InstrumentAcquisitionCompatibility(
            instrument=self.exaspim_instrument, acquisition=self.exaspim_acquisition
        )
        assert example_exaspim_check.run_compatibility_check() is None

        # check that ophys acquisition and instrument are synced
        example_ophys_check = InstrumentAcquisitionCompatibility(
            instrument=self.ophys_instrument, acquisition=self.ophys_acquisition
        ).run_compatibility_check()
        assert example_ophys_check is None

    def test_compare_instrument_id_error(self):
        """Tests that an error is raised when instrument ids do not match"""
        ophys_acquisition = self.ophys_acquisition.model_copy()
        ophys_acquisition.instrument_id = "wrong_id"
        with pytest.raises(ValueError) as context:
            InstrumentAcquisitionCompatibility(
                instrument=self.ophys_instrument, acquisition=ophys_acquisition
            ).run_compatibility_check()
        assert "Instrument ID in acquisition wrong_id does not match the instrument's" in str(context.value)

    def test_compare_stimulus_devices_error(self):
        """Tests that an error is raised when stimulus devices do not match"""
        ephys_acquisition = self.ephys_acquisition.model_copy()
        if ephys_acquisition.stimulus_epochs:
            ephys_acquisition.stimulus_epochs[0].active_devices = ["NonExistentDevice"]
        with pytest.raises(ValueError) as context:
            InstrumentAcquisitionCompatibility(
                instrument=self.ephys_instrument, acquisition=ephys_acquisition
            ).run_compatibility_check()
        assert "Stimulus epoch device names in acquisition do not match stimulus device names in instrument" in str(
            context.value
        )
