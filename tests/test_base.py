"""tests for base"""

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional
from unittest.mock import MagicMock, mock_open, patch

import pytest
from biodata_models.brain_atlas import BrainStructureModel
from pydantic import Field, SkipValidation, ValidationError, create_model

from biodata_schema.base import (
    MAX_FILE_SIZE,
    AwareDatetimeWithDefault,
    DataCoreModel,
    DataModel,
    GenericModel,
    is_dict_corrupt,
)
from biodata_schema.core.procedures import Procedures
from biodata_schema.core.subject import Subject
from examples.subjects import s as example_subject


class TestBase:
    """tests for the base module"""

    def test_described_by(self):
        """test that described by works"""

        s = Subject.model_validate(example_subject.model_dump())

        assert s.describedBy == (
            "https://raw.githubusercontent.com/AllenNeuralDynamics/"
            "biodata-schema/main/src/biodata_schema/core/subject.py"
        )

    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_write_standard_file(self, mock_open: MagicMock):
        """Tests writer with suffix and output directory defined"""

        s = Subject.model_validate(example_subject.model_dump())
        Subject.write_standard_file(s, output_directory=Path("dir"), suffix=".foo.bar")
        mock_open.assert_called_once_with("w")
        assert 1 == 1

    def test_aware_datetime_with_default(self):
        """Tests AwareDatetimeWithDefault adds tzinfo as default"""

        test_model = create_model("TempModel", dt=(AwareDatetimeWithDefault, ...))
        datetime_without_tz = datetime(2020, 10, 10, 1, 2, 3)
        expected_dt = datetime(2020, 10, 10, 1, 2, 3).astimezone()
        model_instance = test_model(dt=datetime_without_tz)

        # Verify that a timezone was attached if not supplied.
        assert expected_dt == model_instance.dt

    def test_aware_datetime_with_setting(self):
        """Tests AwareDatetimeWithDefault honors timezone input by user"""

        test_model = create_model("TempModel", dt=(AwareDatetimeWithDefault, ...))
        datetime_with_tz = datetime(2020, 10, 10, 1, 2, 3, tzinfo=timezone.utc)
        model_instance = test_model(dt=datetime_with_tz)

        expected_json = '{"dt":"2020-10-10T01:02:03Z"}'
        assert expected_json == model_instance.model_dump_json()

    def test_units(self):
        """Test that models with value/value_unit pairs throw errors properly"""

        class UnitValueModel(DataModel):
            """temporary test model"""

            value: Optional[str] = Field(default=None)
            value_unit: Optional[str] = Field(default=None)

        with pytest.raises(ValidationError):
            UnitValueModel(value="value")

        test0 = UnitValueModel(value="value", value_unit="unit")
        assert test0 is not None

        # it's fine if units are set and the value isn't
        test1 = UnitValueModel(value_unit="unit")
        assert test1 is not None

        # Multi-unit condition
        class MultiModel(DataModel):
            """temporary test model with multiple variables"""

            value_multi_one_with_depth: Optional[str] = Field(default=None)
            value_multi_two_with_depth: Optional[str] = Field(default=None)
            value_multi_unit: Optional[str] = Field(default=None)

        with pytest.raises(ValidationError):
            MultiModel(value_multi_one_with_depth="value")

        test2 = MultiModel(value_multi_one_with_depth="value1", value_multi_unit="unit")
        assert test2 is not None

        test3 = MultiModel(value_multi_unit="unit")
        assert test3 is not None

    def test_zero_multi_value_requires_unit(self):
        """A zero-valued member of a measurement group still needs units."""

        class Measurement(DataModel):
            """Measurement with shared units."""

            value_start: Optional[float] = None
            value_unit: Optional[str] = None

        with pytest.raises(ValidationError, match="Unit value_unit is required"):
            Measurement(value_start=0)
        assert Measurement(value_start=0, value_unit="mm").value_start == 0

    def test_is_dict_corrupt(self):
        """Tests is_dict_corrupt method"""
        good_contents = [
            {"a": 1, "b": {"c": 2, "d": 3}},
            {"a": 1, "b": {"c": 2, "d": 3}, "e": ["f", "g"]},
            {"a": 1, "b": {"c": 2, "d": 3}, "e": ["f.valid", "g"]},
            {"a": 1, "b": {"c": {"d": 2}, "e": 3}},
            {"a": 1, "b": [{"c": 2}, {"d": 3}], "e": 4},
        ]
        bad_contents = [
            {"a.1": 1, "b": {"c": 2, "d": 3}},
            {"a": 1, "b": {"c": 2, "$d": 3}},
            {"a": 1, "b": {"c": {"d": 2}, "$e": 3}},
            {"a": 1, "b": {"c": 2, "d": 3, "e.csv": 4}},
            {"a": 1, "b": [{"c": 2}, {"d.csv": 3}], "e": 4},
        ]
        invalid_types = [
            json.dumps({"a": 1, "b": {"c": 2, "d": 3}}),
            [{"a": 1}, {"b": {"c": 2, "d": 3}}],
            1,
            None,
        ]
        for contents in good_contents:
            assert not is_dict_corrupt(contents)
        for contents in bad_contents:
            assert is_dict_corrupt(contents)
        for contents in invalid_types:
            assert is_dict_corrupt(contents)

    def test_generic_model_constructor(self):
        """Tests default constructor for GenericModel"""
        model = GenericModel()
        assert "{}" == model.model_dump_json()

        params = {"foo": "bar"}
        model = GenericModel(**params)
        assert '{"foo":"bar"}' == model.model_dump_json()

    def test_generic_model_validate_fieldnames(self):
        """Tests that fieldnames are validated in GenericModel"""
        invalid_params = [
            {"$foo": "bar"},
            {"foo": {"foo.name": "bar"}},
        ]
        for params in invalid_params:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                GenericModel(**params)
                assert any("fields that contain '.' or '$'" in str(warning.message) for warning in w)
                GenericModel.model_validate(params)
                assert any("fields that contain '.' or '$'" in str(warning.message) for warning in w)

    def test_ccf_validator(self):
        """Tests that CCFv3 validator works"""

        class StructureModel(DataModel):
            """Test model with a targeted_structure"""

            targeted_structure: BrainStructureModel

        with pytest.raises(ValueError):
            StructureModel(targeted_structure="invalid")

    def test_schema_bump(self):
        """Test that schema version are bumped successfully
        and that validation errors prevent bumping"""

        class TestCoreModel(DataCoreModel):
            """test class"""

            describedBy: str = "modelv1"
            schema_version: SkipValidation[Literal["1.0.0"]] = "1.0.0"

        v1_init = TestCoreModel()
        assert "1.0.0" == v1_init.schema_version

        # Re-define TestCoreModel with a bumped schema version
        class TestCoreModel(DataCoreModel):
            """test class"""

            describedBy: str = "modelv2"
            schema_version: SkipValidation[Literal["1.0.1"]] = "1.0.1"
            extra_field: str = "extra_field"

        v2_from_v1 = TestCoreModel(**v1_init.model_dump())
        assert "1.0.1" == v2_from_v1.schema_version

        # Re-re-define to make sure that the extra field is not allowed
        class TestCoreModel(DataCoreModel):
            """test class"""

            describedBy: str = "modelv1"
            schema_version: SkipValidation[Literal["1.0.0"]] = "1.0.0"

        # Check that adding additional fields still fails validation
        # this is to ensure you can't get a bumped schema_version without passing validation
        with pytest.raises(ValidationError):
            TestCoreModel(**v2_from_v1.model_dump())

    @patch("pathlib.Path.open", new_callable=mock_open)
    @patch("biodata_schema.base.logger")
    def test_write_standard_file_size_warning(self, mock_logger: MagicMock, mock_open: MagicMock):
        """Tests that a warning is logged if the file size exceeds MAX_FILE_SIZE"""

        s = Subject.model_validate(example_subject.model_dump())
        s.subject_name = "s" * (MAX_FILE_SIZE + 1000)
        Subject.write_standard_file(s, output_directory=Path("dir"), suffix=".foo.bar")

        mock_open.assert_called_once_with("w")
        mock_logger.warning.assert_called_once_with(
            f"File size exceeds {MAX_FILE_SIZE / 1024} KB: dir/subjects.foo.bar"
        )


class TestDataModel:
    """Tests for DataModel"""

    def test_generate_object_type(self):
        """Test that generate_object_type correctly sets the object_type field"""

        class TestModel(DataModel):
            """Temporary test model"""

            value: str

        model_instance = TestModel(value="test")
        assert model_instance.object_type == "Test model"

        class AnotherTestModel(DataModel):
            """Another temporary test model"""

            value: str

        another_model_instance = AnotherTestModel(value="test")
        assert another_model_instance.object_type == "Another test model"

        class QCModel(DataModel):
            """Test model with two capital letters in a row"""

            value: str

        qc_model_instance = QCModel(value="test")
        assert qc_model_instance.object_type == "QC model"

    def test_object_type_unique(self):
        """Test that all subclasses of DataModel have unique object_type values"""

        # For some reason duplicate subclasses can get generated at runtime
        subclasses = set(DataModel.__subclasses__())

        object_types = {}
        for subclass in subclasses:
            object_type = subclass._object_type_from_name()
            assert object_type not in object_types.values()

            object_types[subclass.__name__] = object_type


class TestDataCoreModel:
    """Tests for DataCoreModel"""

    @pytest.mark.parametrize("record", [example_subject, Procedures(subject_name="123456")])
    @pytest.mark.parametrize("prefix", [None, "example"])
    def test_single_record_collection_file(self, tmp_path, record, prefix):
        """Single records use the standard collection filename and array shape."""
        type(record).write_standard_file(record, output_directory=tmp_path, prefix=prefix)
        filename = ("subjects" if isinstance(record, Subject) else "procedures") + ".json"
        if prefix:
            filename = prefix + "_" + filename
        assert json.loads((tmp_path / filename).read_text()) == [record.model_dump(mode="json")]

    @pytest.mark.parametrize("record", [example_subject, Procedures(subject_name="123456")])
    def test_write_standard_file_with_collection(self, tmp_path, record):
        """Collections share the normal prefix, filename suffix, and extension handling."""
        other = type(record).model_validate(record.model_dump() | {"subject_name": "789012"})
        type(record).write_standard_file(
            [record, other],
            output_directory=str(tmp_path),
            prefix="example",
            filename_suffix="export",
            suffix=".custom.json",
        )
        name = "subjects" if isinstance(record, Subject) else "procedures"
        contents = json.loads((tmp_path / f"example_{name}_export.custom.json").read_text())
        assert contents == [record.model_dump(mode="json"), other.model_dump(mode="json")]

    def test_write_empty_procedures_collection(self, tmp_path):
        """Empty procedures still produce an empty standard array."""
        Procedures.write_standard_file([], output_directory=tmp_path)
        assert json.loads((tmp_path / "procedures.json").read_text()) == []

    def test_non_collection_model_rejects_collection(self, tmp_path):
        """Object-file models cannot write collection-shaped standard files."""
        with pytest.raises(ValueError, match="does not use a collection file"):
            DataCoreModel.write_standard_file([], output_directory=tmp_path)
        assert not list(tmp_path.iterdir())

    @pytest.mark.parametrize("records", [example_subject, [example_subject]])
    def test_write_standard_file_rejects_wrong_model(self, tmp_path, records):
        """Records must match the model class used to write them."""
        with pytest.raises(TypeError, match="requires Procedures records"):
            Procedures.write_standard_file(records, output_directory=tmp_path)
        assert not list(tmp_path.iterdir())

    def test_default_filename(self):
        """Test that default_filename generates the correct filename"""

        class TestModel(DataCoreModel):
            """Temporary test model"""

            describedBy: str = "modelv1"
            schema_version: str = "1.0.0"

        assert TestModel.default_filename() == "test_model.json"

        class AnotherTestModel(DataCoreModel):
            """Another temporary test model"""

            describedBy: str = "modelv1"
            schema_version: str = "1.0.0"

        assert AnotherTestModel.default_filename() == "another_test_model.json"

        class ChildModel(TestModel):
            """Child model inheriting from TestModel"""

            describedBy: str = "modelv1"
            schema_version: str = "1.0.0"

        assert ChildModel.default_filename() == "test_model.json"

    @patch("pathlib.Path.open", new_callable=mock_open)
    @patch("biodata_schema.utils.validators.recursive_check_paths")
    def test_write_standard_file(self, mock_recursive_check_paths: MagicMock, mock_open: MagicMock):
        """Tests write_standard_file method"""

        class TestModel(DataCoreModel):
            """Temporary test model"""

            describedBy: str = "modelv1"
            schema_version: str = "1.0.0"

        model_instance = TestModel()
        TestModel.write_standard_file(
            model_instance, output_directory=Path("dir"), prefix="prefix", filename_suffix="fsuffix", suffix=".suffix"
        )

        mock_open.assert_called_once_with("w")

    @patch("pathlib.Path.open", new_callable=mock_open)
    @patch("biodata_schema.base.logger")
    @patch("biodata_schema.utils.validators.recursive_check_paths")
    def test_write_standard_file_size_warning(
        self, mock_recursive_check_paths: MagicMock, mock_logger: MagicMock, mock_open: MagicMock
    ):
        """Tests that a warning is logged if the file size exceeds MAX_FILE_SIZE"""

        class TestModel(DataCoreModel):
            """Temporary test model"""

            describedBy: str = "modelv1"
            schema_version: str = "1.0.0"

        model_instance = TestModel()
        model_instance.schema_version = "1" * (MAX_FILE_SIZE + 1000)
        TestModel.write_standard_file(model_instance, output_directory=Path("dir"), suffix=".foo.bar")

        mock_open.assert_called_once_with("w")
        mock_logger.warning.assert_called_once_with(
            f"File size exceeds {MAX_FILE_SIZE / 1024} KB: dir/test_model.foo.bar"
        )

    @patch("pathlib.Path.open", new_callable=mock_open)
    @patch("biodata_schema.utils.validators.recursive_check_paths")
    def test_write_standard_file_string_output_directory(
        self, mock_recursive_check_paths: MagicMock, mock_open: MagicMock
    ):
        """Tests write_standard_file with a string output_directory (should be coerced to Path)"""

        class TestModel(DataCoreModel):
            """Temporary test model"""

            describedBy: str = "modelv1"
            schema_version: str = "1.0.0"

        model_instance = TestModel()
        TestModel.write_standard_file(model_instance, output_directory="dir")
        mock_open.assert_called_once_with("w")

    @patch("pathlib.Path.open", new_callable=mock_open)
    @patch("biodata_schema.utils.validators.recursive_check_paths")
    def test_write_standard_file_no_output_directory(self, mock_recursive_check_paths: MagicMock, mock_open: MagicMock):
        """Tests write_standard_file with no output_directory (defaults to cwd)"""

        class TestModel(DataCoreModel):
            """Temporary test model"""

            describedBy: str = "modelv1"
            schema_version: str = "1.0.0"

        model_instance = TestModel()
        TestModel.write_standard_file(model_instance)
        mock_open.assert_called_once_with("w")
