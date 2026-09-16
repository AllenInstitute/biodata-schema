"""Tests for CalibrationFit from measurements module"""

import pytest
from pydantic import ValidationError

from biodata_schema.components.measurements import CalibrationFit, FitType


class TestCalibrationFit:
    """Tests for CalibrationFit class"""

    def test_linear_interpolation_without_parameters(self):
        """Test that linear interpolation fit type works without parameters"""
        fit = CalibrationFit(fit_type=FitType.LINEAR_INTERPOLATION)
        assert fit.fit_type == FitType.LINEAR_INTERPOLATION.value
        assert fit.fit_parameters is None

    def test_linear_interpolation_with_parameters_raises_error(self):
        """Test that linear interpolation fit type raises error with parameters"""
        with pytest.raises(ValidationError) as context:
            CalibrationFit(fit_type=FitType.LINEAR_INTERPOLATION, fit_parameters={"slope": 1.0, "intercept": 0.0})
        assert "Fit parameters should not be provided for linear interpolation fit type" in str(context.value)

    def test_linear_fit_with_parameters(self):
        """Test that linear fit type works with parameters"""
        parameters = {"slope": 1.5, "intercept": 2.0}
        fit = CalibrationFit(fit_type=FitType.LINEAR, fit_parameters=parameters)
        assert fit.fit_type == FitType.LINEAR.value
        # Compare the fit_parameters as a dict using model_dump()
        assert fit.fit_parameters is not None
        assert fit.fit_parameters.model_dump() == parameters

    def test_linear_fit_without_parameters_raises_error(self):
        """Test that linear fit type raises error without parameters"""
        with pytest.raises(ValidationError) as context:
            CalibrationFit(fit_type=FitType.LINEAR)
        assert "Fit parameters must be provided for linear fit type" in str(context.value)

    def test_other_fit_with_parameters(self):
        """Test that other fit type works with parameters"""
        parameters = {"a": 1.0, "b": 2.0, "c": 3.0}
        fit = CalibrationFit(fit_type=FitType.OTHER, fit_parameters=parameters)
        assert fit.fit_type == FitType.OTHER.value
        # Compare the fit_parameters as a dict using model_dump()
        assert fit.fit_parameters is not None
        assert fit.fit_parameters.model_dump() == parameters

    def test_other_fit_without_parameters_raises_error(self):
        """Test that other fit type raises error without parameters"""
        with pytest.raises(ValidationError) as context:
            CalibrationFit(fit_type=FitType.OTHER)
        assert "Fit parameters must be provided for other fit type" in str(context.value)

    def test_linear_fit_with_none_parameters_raises_error(self):
        """Test that linear fit type raises error with None parameters"""
        with pytest.raises(ValidationError) as context:
            CalibrationFit(fit_type=FitType.LINEAR, fit_parameters=None)
        assert "Fit parameters must be provided for linear fit type" in str(context.value)

    def test_other_fit_with_none_parameters_raises_error(self):
        """Test that other fit type raises error with None parameters"""
        with pytest.raises(ValidationError) as context:
            CalibrationFit(fit_type=FitType.OTHER, fit_parameters=None)
        assert "Fit parameters must be provided for other fit type" in str(context.value)
