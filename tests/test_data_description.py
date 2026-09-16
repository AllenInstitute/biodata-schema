"""test DataDescription"""

import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from biodata_models.data_name_patterns import DataLevel
from biodata_models.modalities import Modality
from biodata_models.organizations import Organization
from pydantic import ValidationError

from biodata_schema.components.identifiers import Person
from biodata_schema.core.data_description import DataDescription, Funding, build_data_name
from biodata_schema.utils.inheritance import (
    derive_data_description,
    derive_data_description_from_derived,
    derive_data_description_from_raw,
)
from examples.data_description import d as example_data_description

DATA_DESCRIPTION_FILES_PATH = Path(__file__).parent / "resources" / "ephys_data_description"


class TestDataDescription:
    """test DataDescription"""

    BAD_NAME = "fizzbuzz"
    BASIC_NAME = "1234_3033-12-21_04-22-11"
    DERIVED_NAME = "1234_3033-12-21_04-22-11_spikesorted-ks25_2022-10-12_23-23-11"

    def test_funding_construction(self):
        """Test Funding construction"""
        f = Funding(funder=Organization.NINDS, grant_number="grant001")
        assert f is not None

    def test_raw_data_description_construction(self):
        """Test DataDescription construction"""
        dt = datetime.datetime.now()
        f = Funding(funder=Organization.NINDS, grant_number="grant001")
        da = DataDescription(
            creation_time=dt,
            institution=Organization.AIND,
            data_level=DataLevel.RAW,
            funding_source=[f],
            modalities=[Modality.ECEPHYS],
            subject_id="12345",
            investigators=[Person(name="Jane Smith")],
            project_name="Test",
        )
        assert da is not None

    def test_build_name(self):
        """Test build_data_name function"""
        dt = datetime.datetime(2022, 10, 12, 23, 23, 11)
        name = build_data_name("project", dt)
        assert name == "project_2022-10-12_23-23-11"

    @patch("biodata_schema.core.data_description.build_data_name")
    def test_build_name_validation_error(self, mock_build_data_name: MagicMock):
        """Test build_data_name function to trigger validation error"""
        mock_build_data_name.return_value = "invalid"

        dt = datetime.datetime(2022, 10, 12, 23, 23, 11)
        with pytest.raises(ValueError):
            DataDescription(
                modalities=[Modality.SPIM],
                subject_id="1234",
                data_level=DataLevel.RAW,
                creation_time=dt,
                institution=Organization.AIND,
                funding_source=[Funding(funder=Organization.NINDS, grant_number="grant001")],
                investigators=[Person(name="Jane Smith")],
                project_name="Test",
            )

    def test_derived_data_description_construction(self):
        """Test DataDescription.data_level == DERIVED construction"""
        dt = datetime.datetime.now()
        f = Funding(funder=Organization.NINDS, grant_number="grant001")
        da = DataDescription(
            creation_time=dt,
            institution=Organization.AIND,
            data_level=DataLevel.RAW,
            funding_source=[f],
            modalities=[Modality.ECEPHYS],
            subject_id="12345",
            investigators=[Person(name="Jane Smith")],
            project_name="Test",
        )
        r1 = derive_data_description_from_raw(da, "spikesort-ks25", creation_time=dt)
        assert r1 is not None

    def test_nested_derived_data_description_construction(self):
        """Test nested derived DataDescription construction"""
        dt = datetime.datetime.now()
        f = Funding(funder=Organization.NINDS, grant_number="grant001")
        da = DataDescription(
            creation_time=dt,
            institution=Organization.AIND,
            data_level=DataLevel.RAW,
            funding_source=[f],
            modalities=[Modality.ECEPHYS],
            subject_id="12345",
            investigators=[Person(name="Jane Smith")],
            project_name="Test",
        )
        r1 = derive_data_description_from_raw(da, "spikesort-ks25", creation_time=dt)
        r2 = derive_data_description_from_derived(r1, "some-model", creation_time=dt)
        r3 = derive_data_description_from_derived(r2, "a-paper", creation_time=dt)
        assert r3 is not None

    def test_data_description_construction(self):
        """Test DataDescription construction"""
        dt = datetime.datetime.now()
        f = Funding(funder=Organization.NINDS, grant_number="grant001")
        dd = DataDescription(
            modalities=[Modality.SPIM],
            subject_id="1234",
            data_level=DataLevel.RAW,
            creation_time=dt,
            institution=Organization.AIND,
            funding_source=[f],
            investigators=[Person(name="Jane Smith")],
            project_name="Test",
        )
        assert dd is not None

    def test_data_description_construction_failure(self):
        """Test DataDescription construction failure"""
        dt = datetime.datetime.now()
        f = Funding(funder=Organization.NINDS, grant_number="grant001")
        with pytest.raises(ValidationError):
            DataDescription(
                modalities=[Modality.SPIM],
                subject_id="",
                data_level=DataLevel.RAW,
                creation_time=dt,
                institution=Organization.AIND,
                funding_source=[f],
                investigators=[Person(name="Jane Smith")],
                project_name="Test",
            )

    def test_parse_name_invalid(self):
        """Test DataDescription construction failure with invalid data level"""

        with pytest.raises(ValueError) as context:
            DataDescription.parse_name("name", "invalid_data_level")
        assert "DataLevel" in str(context.value)

    def test_derived_valid(self):
        """Test that you can construct a valid derived DataDescription"""

        dt = datetime.datetime.now()
        f = Funding(funder=Organization.NINDS, grant_number="grant001")
        dr = DataDescription(
            modalities=[Modality.SPIM],
            subject_id="1234",
            data_level=DataLevel.RAW,
            creation_time=dt,
            institution=Organization.AIND,
            funding_source=[f],
            investigators=[Person(name="Jane Smith")],
            project_name="Test",
        )

        # also over-write with specimen ID
        dd = derive_data_description_from_raw(dr, "process", subject_id="1234-56")
        assert dd is not None

    def test_raw_no_subject_id(self):
        """Test that creating a raw data description without subject_id raises an error"""
        dt = datetime.datetime.now()

        with pytest.raises(ValueError) as context:
            DataDescription(
                creation_time=dt,
                institution=Organization.AIND,
                data_level=DataLevel.RAW,
                funding_source=[Funding(funder=Organization.NINDS, grant_number="grant001")],
                modalities=[Modality.ECEPHYS],
                investigators=[Person(name="Jane Smith")],
                project_name="Test",
            )

        assert "subject_id" in str(context.value)

    def test_derived_bad_creation_time(self):
        """Test that a validation error is raised if the creation time is not a datetime object"""
        dt = datetime.datetime.now()

        da = DataDescription(
            creation_time=dt,
            institution=Organization.AIND,
            data_level=DataLevel.RAW,
            funding_source=[Funding(funder=Organization.NINDS, grant_number="grant001")],
            modalities=[Modality.ECEPHYS],
            subject_id="12345",
            investigators=[Person(name="Jane Smith")],
            project_name="Test",
        )

        with pytest.raises(ValueError) as context:
            derive_data_description_from_raw(da, "spikesort-ks25", creation_time="invalid creation time")

        assert "creation_time" in str(context.value)

    def test_data_description_missing_fields(self):
        """Test DataDescription missing fields"""
        with pytest.raises(ValidationError):
            DataDescription()

    def test_pattern_errors(self):
        """Tests that errors are raised if malformed strings are input"""
        with pytest.raises(ValidationError) as e:
            DataDescription(
                modalities=[Modality.SPIM],
                subject_id="1234",
                data_level=DataLevel.RAW,
                project_name="a_32r&!#R$&#",
                creation_time=datetime.datetime(2020, 10, 10, 10, 10, 10),
                institution=Organization.AIND,
                funding_source=[Funding(funder=Organization.NINDS, grant_number="grant001")],
                investigators=[Person(name="Jane Smith")],
            )
        assert "String should match pattern" in str(e.value)

    def test_model_constructors(self):
        """test static methods for constructing models"""

        assert Organization.from_abbreviation("AIND") == Organization.AIND
        assert Organization.from_name("Allen Institute for Neural Dynamics") == Organization.AIND
        assert Modality.from_abbreviation("ecephys") == Modality.ECEPHYS
        assert Organization().name_map["Allen Institute for Neural Dynamics"] == Organization.AIND

    def test_round_trip(self):
        """make sure we can round trip from json"""

        dt = datetime.datetime.now()

        da1 = DataDescription(
            creation_time=dt,
            institution=Organization.AIND,
            data_level=DataLevel.RAW,
            funding_source=[Funding(funder=Organization.NINDS, grant_number="grant001")],
            modalities=[Modality.SPIM],
            subject_id="12345",
            investigators=[Person(name="Jane Smith")],
            project_name="Test",
        )

        da2 = DataDescription.model_validate_json(da1.model_dump_json())
        assert da1.creation_time == da2.creation_time
        assert da1.name == da2.name

    def test_parse_name(self):
        """tests for parsing names"""

        toks = DataDescription.parse_name(self.BASIC_NAME, DataLevel.RAW)
        assert toks["label"] == "1234"
        assert toks["creation_time"] == datetime.datetime(3033, 12, 21, 4, 22, 11)

        with pytest.raises(ValueError):
            DataDescription.parse_name(self.BAD_NAME, DataLevel.RAW)

        toks = DataDescription.parse_name(self.DERIVED_NAME, DataLevel.DERIVED)
        assert toks["input"] == "1234_3033-12-21_04-22-11"
        assert toks["process_name"] == "spikesorted-ks25"
        assert toks["creation_time"] == datetime.datetime(2022, 10, 12, 23, 23, 11)

        toks = DataDescription.parse_name("Test-project_my-analysis_2022-10-12_23-23-11", DataLevel.DERIVED)
        assert toks["project_abbreviation"] == "Test-project"
        assert toks["analysis_name"] == "my-analysis"
        assert toks["creation_time"] == datetime.datetime(2022, 10, 12, 23, 23, 11)

        with pytest.raises(ValueError):
            DataDescription.parse_name(self.BAD_NAME, DataLevel.DERIVED)

    def test_unique_abbreviations(self):
        """Tests that abbreviations are unique"""
        modality_abbreviations = [m().abbreviation for m in Modality.ALL]
        assert len(set(modality_abbreviations)) == len(modality_abbreviations)

    def test_source_data_field(self):
        """Tests the source_data field behavior"""

        # source_data should not be set for raw data
        with pytest.raises(ValueError) as context:
            DataDescription(
                modalities=[Modality.SPIM],
                subject_id="1234",
                data_level=DataLevel.RAW,
                creation_time=datetime.datetime.now(),
                institution=Organization.AIND,
                funding_source=[Funding(funder=Organization.NINDS, grant_number="grant001")],
                investigators=[Person(name="Jane Smith")],
                project_name="Test",
                source_data=["some_source_data"],
            )
        assert "source_data must not be set when data_level is 'raw'" in str(context.value)

        # source_data should be set correctly for derived data
        dt = datetime.datetime.now()
        f = Funding(funder=Organization.NINDS, grant_number="grant001")
        da = DataDescription(
            creation_time=dt,
            institution=Organization.AIND,
            data_level=DataLevel.RAW,
            funding_source=[f],
            modalities=[Modality.ECEPHYS],
            subject_id="12345",
            investigators=[Person(name="Jane Smith")],
            project_name="Test",
        )
        r1 = derive_data_description_from_raw(da, "spikesort-ks25", creation_time=dt)
        assert r1.source_data is not None
        assert len(r1.source_data) == 1
        assert r1.source_data[0] == da.name

    def test_from_raw_with_explicit_source_data(self):
        """Test from_raw with explicitly provided source_data parameter"""
        dt = datetime.datetime.now()
        f = Funding(funder=Organization.NINDS, grant_number="grant001")

        # Create a raw DataDescription
        da = DataDescription(
            creation_time=dt,
            institution=Organization.AIND,
            data_level=DataLevel.RAW,
            funding_source=[f],
            modalities=[Modality.ECEPHYS],
            subject_id="12345",
            investigators=[Person(name="Jane Smith")],
            project_name="Test",
        )

        # Test scenario 3: RAW data → DERIVED with explicit source_data
        explicit_source = ["external_dataset_1", "external_dataset_2"]
        r1 = derive_data_description_from_raw(da, "spikesort-ks25", source_data=explicit_source, creation_time=dt)

        # Should use the explicit source_data instead of the original name
        assert r1.source_data is not None
        assert len(r1.source_data) == 2
        assert r1.source_data == explicit_source
        assert da.name not in r1.source_data

        # Test scenario 4: DERIVED data → DERIVED with explicit source_data
        additional_source = ["another_external_dataset"]
        r2 = derive_data_description_from_derived(r1, "clustering", source_data=additional_source, creation_time=dt)

        # Should use the explicit source_data (not combine with existing)
        assert r2.source_data is not None
        assert len(r2.source_data) == 1  # Just the new source_data
        assert r2.source_data == additional_source

    def test_from_raw_chained_source_data_behavior(self):
        """Test source_data behavior in chained derived data without explicit source_data"""
        dt = datetime.datetime.now()
        f = Funding(funder=Organization.NINDS, grant_number="grant001")

        # Create a raw DataDescription
        da = DataDescription(
            creation_time=dt,
            institution=Organization.AIND,
            data_level=DataLevel.RAW,
            funding_source=[f],
            modalities=[Modality.ECEPHYS],
            subject_id="12345",
            investigators=[Person(name="Jane Smith")],
            project_name="Test",
        )

        # First derivation: RAW → DERIVED (should set source_data to original name)
        r1 = derive_data_description_from_raw(da, "spikesort-ks25", creation_time=dt)
        assert r1.source_data == [da.name]

        # Second derivation: DERIVED → DERIVED (should use only the immediate predecessor)
        r2 = derive_data_description_from_derived(r1, "clustering", creation_time=dt)
        assert len(r2.source_data) == 1
        assert r2.source_data[0] == r1.name  # Only the immediate predecessor

        # Third derivation: should only reference the immediate predecessor
        r3 = derive_data_description_from_derived(r2, "analysis", creation_time=dt)
        assert len(r3.source_data) == 1
        assert r3.source_data[0] == r2.name  # Only the immediate predecessor

    def test_from_derived_basic_functionality(self):
        """Test from_derived creates derived data using original input name"""
        dt = datetime.datetime(2022, 10, 12, 23, 23, 11)

        # Create first derived from example data
        derived1 = derive_data_description_from_raw(example_data_description, "spike_sorting", creation_time=dt)

        # Verify first derived name structure
        assert derived1.name.startswith(example_data_description.name)
        assert "spike_sorting" in derived1.name
        assert derived1.data_level == DataLevel.DERIVED
        assert derived1.source_data == [example_data_description.name]

        # Create second derived using from_derived
        dt2 = datetime.datetime(2022, 10, 13, 10, 15, 30)
        derived2 = derive_data_description_from_derived(derived1, "quality_control", creation_time=dt2)

        # Verify second derived uses original input, not full derived name
        assert derived2.name.startswith(example_data_description.name)
        assert "quality_control" in derived2.name
        assert "spike_sorting" not in derived2.name  # Should not chain process names
        assert derived2.data_level == DataLevel.DERIVED
        assert len(derived2.source_data) == 1
        assert derived2.source_data[0] == derived1.name  # Only immediate predecessor

        # Verify the names have the expected structure
        expected_derived1_prefix = f"{example_data_description.name}_spike_sorting_"
        expected_derived2_prefix = f"{example_data_description.name}_quality_control_"
        assert derived1.name.startswith(expected_derived1_prefix)
        assert derived2.name.startswith(expected_derived2_prefix)

    def test_from_derived_validation_error(self):
        """Test from_derived raises error when input is not DERIVED"""
        dt = datetime.datetime.now()

        with pytest.raises(ValueError) as context:
            derive_data_description_from_derived(example_data_description, "process", creation_time=dt)

        assert "must have data_level=DERIVED" in str(context.value)

    def test_from_derived_with_explicit_source_data(self):
        """Test from_derived with explicitly provided source_data parameter"""
        dt = datetime.datetime(2022, 10, 12, 23, 23, 11)
        dt2 = datetime.datetime(2022, 10, 13, 10, 15, 30)

        # Create first derived from example data
        derived1 = derive_data_description_from_raw(example_data_description, "preprocessing", creation_time=dt)

        # Create second derived with explicit source_data
        explicit_source = ["external_dataset_1", "external_dataset_2"]
        derived2 = derive_data_description_from_derived(
            derived1, "analysis", source_data=explicit_source, creation_time=dt2
        )

        # Should use the explicit source_data (not combine with existing)
        assert len(derived2.source_data) == 2  # Just the explicit source_data
        assert derived2.source_data == explicit_source  # Explicit source_data only

    def test_from_derived_chained_behavior(self):
        """Test chained from_derived calls maintain original input name"""
        dt1 = datetime.datetime(2022, 10, 12, 23, 23, 11)
        dt2 = datetime.datetime(2022, 10, 13, 10, 15, 30)
        dt3 = datetime.datetime(2022, 10, 14, 14, 20, 45)

        # Create chain: RAW → DERIVED → DERIVED → DERIVED
        derived1 = derive_data_description_from_raw(example_data_description, "process1", creation_time=dt1)
        derived2 = derive_data_description_from_derived(derived1, "process2", creation_time=dt2)
        derived3 = derive_data_description_from_derived(derived2, "process3", creation_time=dt3)

        # All derived names should start with the original raw name
        original_prefix = example_data_description.name
        assert derived1.name.startswith(f"{original_prefix}_process1_")
        assert derived2.name.startswith(f"{original_prefix}_process2_")
        assert derived3.name.startswith(f"{original_prefix}_process3_")

        # Verify source_data only contains immediate predecessor
        assert derived1.source_data == [example_data_description.name]
        assert derived2.source_data == [derived1.name]
        assert derived3.source_data == [derived2.name]

    def test_from_derived_name_parsing(self):
        """Test from_derived correctly parses complex derived names"""
        dt1 = datetime.datetime(2022, 10, 12, 23, 23, 11)
        dt2 = datetime.datetime(2022, 10, 13, 10, 15, 30)

        # Create a derived data with complex process name
        derived1 = derive_data_description_from_raw(
            example_data_description, "spike-sorting-v2.1_with-params", creation_time=dt1
        )

        # Create another derived from the first
        derived2 = derive_data_description_from_derived(derived1, "cluster-analysis_final", creation_time=dt2)

        # Verify the second derived uses the original input correctly
        assert derived2.name.startswith(example_data_description.name)
        assert "cluster-analysis_final" in derived2.name
        assert "spike-sorting-v2.1_with-params" not in derived2.name

    def test_from_data_description_with_raw_input(self):
        """Test from_data_description delegates to from_raw for RAW input"""
        dt = datetime.datetime(2022, 10, 12, 23, 23, 11)

        # Should behave exactly like from_raw
        result_from_data_description = derive_data_description(
            example_data_description, "test_process", creation_time=dt
        )

        result_from_raw = derive_data_description_from_raw(example_data_description, "test_process", creation_time=dt)

        # Results should be identical
        assert result_from_data_description.name == result_from_raw.name
        assert result_from_data_description.source_data == result_from_raw.source_data
        assert result_from_data_description.data_level == result_from_raw.data_level

    def test_from_data_description_with_derived_input(self):
        """Test from_data_description delegates to from_derived for DERIVED input"""
        dt1 = datetime.datetime(2022, 10, 12, 23, 23, 11)
        dt2 = datetime.datetime(2022, 10, 13, 10, 15, 30)

        # Create derived data first
        derived1 = derive_data_description_from_raw(example_data_description, "first_process", creation_time=dt1)

        # Should behave exactly like from_derived
        result_from_data_description = derive_data_description(derived1, "second_process", creation_time=dt2)

        result_from_derived = derive_data_description_from_derived(derived1, "second_process", creation_time=dt2)

        # Results should be identical
        assert result_from_data_description.name == result_from_derived.name
        assert result_from_data_description.source_data == result_from_derived.source_data
        assert result_from_data_description.data_level == result_from_derived.data_level

    def test_from_data_description_unsupported_data_level(self):
        """Test from_data_description raises error for unsupported data levels"""
        dt = datetime.datetime.now()

        # Create a mock DataDescription with unsupported data_level
        # We'll create a derived one and then manually change its data_level
        derived = derive_data_description_from_raw(example_data_description, "test", creation_time=dt)
        derived.data_level = DataLevel.SIMULATED  # Not supported by from_data_description

        with pytest.raises(ValueError) as context:
            derive_data_description(derived, "process", creation_time=dt)

        assert "Unsupported data_level: simulated" in str(context.value)

    def test_from_data_description_with_kwargs_and_source_data(self):
        """Test from_data_description passes through kwargs and source_data correctly"""
        dt1 = datetime.datetime(2022, 10, 12, 23, 23, 11)
        dt2 = datetime.datetime(2022, 10, 13, 10, 15, 30)

        # Test with RAW input
        custom_tags = ["custom", "test"]
        explicit_source = ["external_source"]

        result_raw = derive_data_description(
            example_data_description, "test_process", source_data=explicit_source, creation_time=dt1, tags=custom_tags
        )

        assert result_raw.tags == custom_tags
        assert result_raw.source_data == explicit_source

        # Test with DERIVED input
        derived = derive_data_description_from_raw(example_data_description, "first", creation_time=dt1)

        result_derived = derive_data_description(
            derived, "second_process", source_data=explicit_source, creation_time=dt2, tags=custom_tags
        )

        assert result_derived.tags == custom_tags
        # Should use the explicit source_data (not combine with existing)
        assert result_derived.source_data == explicit_source

    def test_from_derived_with_invalid_creation_time(self):
        """Test from_derived error when creation_time is not a datetime object"""
        dt = datetime.datetime.now()

        # Create first derived data
        derived1 = derive_data_description_from_raw(example_data_description, "preprocessing", creation_time=dt)

        with pytest.raises(ValueError) as context:
            derive_data_description_from_derived(derived1, "analysis", creation_time="not_a_datetime")

        assert "creation_time(not_a_datetime) must be a datetime object" in str(context.value)

    def test_from_raw_validation_error_on_derived_input(self):
        """Test from_raw raises error when input data_level is DERIVED"""
        dt = datetime.datetime.now()

        # Create derived data first
        derived = derive_data_description_from_raw(example_data_description, "preprocessing", creation_time=dt)

        # Try to use from_raw on derived data (should fail)
        with pytest.raises(ValueError) as context:
            derive_data_description_from_raw(derived, "another_process", creation_time=dt)

        assert "Input data_description must have data_level=RAW, got derived" in str(context.value)

    def test_from_raw_missing_required_field_raises_error(self):
        """Test from_raw raises error when a required field is missing from the base DataDescription"""
        dt = datetime.datetime.now()

        # Create a copy of the valid DataDescription to avoid modifying the original
        base_data = DataDescription.model_validate(example_data_description.model_dump())

        # Remove a required field to make it invalid
        delattr(base_data, "investigators")

        # Try to create derived data - should trigger the PydanticUndefined error path
        with pytest.raises(ValueError) as context:
            derive_data_description(base_data, "test_process", creation_time=dt)

        # Should raise error about the missing required field
        assert "Required field investigators must have a value" in str(context.value)

    def test_from_derived_missing_required_field_raises_error(self):
        """Test from_raw raises error when a required field is missing from the base DataDescription"""
        dt = datetime.datetime.now()

        # Create a copy of the valid DataDescription to avoid modifying the original
        base_data = DataDescription.model_validate(example_data_description.model_dump())
        derived_data = derive_data_description_from_raw(base_data, "process", creation_time=dt)

        # Remove a required field to make it invalid
        delattr(derived_data, "investigators")

        # Try to create derived data - should trigger the PydanticUndefined error path
        with pytest.raises(ValueError) as context:
            derive_data_description(derived_data, "process-2", creation_time=dt)

        # Should raise error about the missing required field
        assert "Required field investigators must have a value" in str(context.value)
