"""Module to test json_writer classes."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Optional, Union
from unittest.mock import MagicMock, call, mock_open, patch

import pytest
from jsonschema import Draft202012Validator
from pydantic import BaseModel, TypeAdapter

from biodata_schema.base import DraftRequirement
from biodata_schema.core.metadata import Metadata
from biodata_schema.core.procedures import Procedures
from biodata_schema.core.subject import Subject
from biodata_schema.utils.json_writer import (
    SchemaWriter,
    _add_referenced_definitions,
    _has_draft_requirements,
    _project_model_schema,
    draft_metadata_schema,
)
from examples.aibs_smartspim_instrument import inst as instrument
from examples.barseq_acquisition import acquisition
from examples.data_description import d as data_description
from examples.model import m as model
from examples.procedures import p as procedures
from examples.processing import p as processing
from examples.quality_control import q as quality_control
from examples.subjects import s as subject


class TestSchemaWriter:
    """Tests for SchemaWriter methods"""

    TEST_ARGS = ["--output", "some_test_dir"]

    @pytest.mark.parametrize(
        "script,field_name,count",
        [
            ("subjects", "subjects", 2),
            ("procedures", "procedures", 2),
            ("ophys_procedures", "procedures", 1),
            ("aibs_smartspim_procedures", "procedures", 1),
            ("thermistor_procedures", "procedures", 1),
        ],
    )
    def test_collection_examples(self, tmp_path, script, field_name, count):
        """Runnable examples produce standard files that match published collection schemas."""
        example = Path(__file__).parents[1] / "examples" / f"{script}.py"
        subprocess.run([sys.executable, str(example), "--output-dir", str(tmp_path)], check=True)
        assert {path.name for path in tmp_path.iterdir()} == {f"{script}.json"}
        records = json.loads((tmp_path / f"{script}.json").read_text())
        assert len(records) == count
        model_class = Subject if field_name == "subjects" else Procedures
        Draft202012Validator(SchemaWriter.model_schema(model_class)).validate(records)

    def test_collection_schemas_validate_written_files(self, tmp_path):
        """Published collection schemas validate the actual array files."""
        SchemaWriter(["--output", str(tmp_path)]).write_to_json()
        metadata = Metadata.model_construct(
            name="test",
            location="",
            subjects=[subject, subject.model_copy(update={"subject_name": "789012"})],
            procedures=[Procedures(subject_name="123456"), Procedures(subject_name="789012")],
        )
        metadata.write_standard_files(output_directory=tmp_path)
        for field_name in ("subjects", "procedures"):
            schema = json.loads((tmp_path / f"{field_name}_schema.json").read_text())
            records = json.loads((tmp_path / f"{field_name}.json").read_text())
            validator = Draft202012Validator(schema)
            assert schema["type"] == "array"
            validator.validate(records)
            assert not validator.is_valid(records[0])
        assert not (tmp_path / "subject_schema.json").exists()

    def test_get_schemas(self):
        """Tests get schemas method"""
        sw = SchemaWriter([])
        schema_gen = sw.get_schemas()

        for schema in schema_gen:
            filename = schema.default_filename()
            # file_extension = schema.default_file_extension()
            # schema_filename = filename.replace(file_extension, "_schema.json")
            schema_contents = schema.model_json_schema()
            assert filename is not None
            assert schema_contents is not None

    def test_parse_args(self):
        """Tests arguments are parsed correctly."""
        sw = SchemaWriter(self.TEST_ARGS)

        sw2 = SchemaWriter([])
        sw3 = SchemaWriter(["--draft"])

        expected_output = "some_test_dir"

        assert expected_output == sw.configs.output
        assert self.TEST_ARGS == sw.args
        assert os.getcwd() == sw2.configs.output
        assert sw3.configs.draft is True

    def test_draft_metadata_schema(self):
        """Tests that the draft schema contains only its required metadata fields."""
        schema = draft_metadata_schema()

        assert set(schema["properties"]) == {"location", "data_description", "subjects", "acquisition", "instrument"}
        assert set(schema["required"]) == set(schema["properties"])
        assert schema["properties"]["subjects"]["minItems"] == 1
        assert schema["additionalProperties"] is True
        assert set(schema["$defs"]) == {"License"}

        expected_nested_fields = {
            "data_description": {"project_name", "license"},
            "subjects": {"subject_name"},
            "acquisition": {"acquisition_start_time"},
            "instrument": {"instrument_name"},
        }
        for field_name, fields in expected_nested_fields.items():
            nested_schema = schema["properties"][field_name]
            if field_name == "subjects":
                assert nested_schema["type"] == "array"
                nested_schema = nested_schema["items"]
            assert set(nested_schema["properties"]) == fields
            assert set(nested_schema["required"]) == fields
            assert nested_schema["additionalProperties"] is True

    def test_full_metadata_validates_against_draft_schema(self):
        """Tests that a full metadata record validates against the draft schema."""
        metadata = Metadata.model_construct(
            name="full_metadata",
            location="s3://bucket/full_metadata",
            other_identifiers=None,
            subjects=[subject],
            data_description=data_description,
            procedures=[procedures],
            instrument=instrument,
            processing=processing,
            acquisition=acquisition,
            quality_control=quality_control,
            model=model,
        )
        metadata_json = json.loads(metadata.model_dump_json(by_alias=True))

        Draft202012Validator(draft_metadata_schema()).validate(metadata_json)
        metadata_json["subjects"] = []
        assert not Draft202012Validator(draft_metadata_schema()).is_valid(metadata_json)

    def test_draft_schema_projection_helpers(self):
        """Tests nested, recursive, and union model projections."""

        class NestedModel(BaseModel):
            draft_field: Annotated[str, DraftRequirement]

        class ParentModel(BaseModel):
            nested: NestedModel

        class UnionModelA(BaseModel):
            draft_field: Annotated[str, DraftRequirement]

        class UnionModelB(BaseModel):
            draft_field: Annotated[str, DraftRequirement]

        class UnionParentModel(BaseModel):
            nested: Union[UnionModelA, UnionModelB]

        class RecursiveModel(BaseModel):
            child: Optional["RecursiveModel"] = None

        RecursiveModel.model_rebuild()

        assert _has_draft_requirements(ParentModel) is True
        assert _has_draft_requirements(RecursiveModel) is False

        union_schema = _project_model_schema(UnionParentModel, {})
        assert len(union_schema["properties"]["nested"]["anyOf"]) == 2

        references_schema = {"anyOf": [{"$ref": "#/$defs/Example"}, {"$ref": "#/$defs/Example"}]}
        _add_referenced_definitions(references_schema, {"Example": {"type": "string"}})
        assert references_schema["$defs"] == {"Example": {"type": "string"}}

    @patch("builtins.open", new_callable=mock_open())
    @patch("os.path.exists")
    @patch("os.mkdir")
    def test_write_to_json(self, mock_mkdir: MagicMock, mock_path_exists: MagicMock, mock_file: MagicMock):
        """Tests that model is written to JSON"""
        mock_path_exists.return_value = False
        sw = SchemaWriter(self.TEST_ARGS)
        schema_list = list(sw.get_schemas())
        mock_path_exists.side_effect = [False] + [True for _ in schema_list[:-1]]
        sw.write_to_json()
        file_handle = mock_file.return_value.__enter__.return_value
        schema_gen = sw.get_schemas()
        open_calls = []
        write_calls = []
        for schema in schema_gen:
            filename = "subjects.json" if schema is Subject else schema.default_filename()
            file_extension = "".join(Path(filename).suffixes)
            schema_filename = filename.replace(file_extension, "_schema.json")
            path = Path("some_test_dir") / schema_filename
            schema_json: dict = (
                TypeAdapter(list[schema]).json_schema()
                if schema in (Subject, Procedures)
                else schema.model_json_schema()
            )
            if schema is Subject:
                schema_json["minItems"] = 1
            schema_json_str: str = json.dumps(schema_json, indent=3)
            open_calls.append(call(path, "w"))
            write_calls.append(call(schema_json_str))
        mock_mkdir.assert_called_once_with(Path("some_test_dir"), 511)
        mock_file.assert_has_calls(open_calls, any_order=True)
        file_handle.write.assert_has_calls(write_calls, any_order=True)

    @patch("builtins.open", new_callable=mock_open())
    @patch("os.path.exists")
    @patch("os.mkdir")
    def test_write_to_json_version_number(
        self, mock_mkdir: MagicMock, mock_path_exists: MagicMock, mock_file: MagicMock
    ):
        """Tests that model is written to JSON with version directory"""
        mock_path_exists.return_value = False
        sys_args = ["--output", "some_test_dir", "--attach-version"]
        sw = SchemaWriter(sys_args)
        sw.write_to_json()
        file_handle = mock_file.return_value.__enter__.return_value
        schema_list = list(sw.get_schemas())
        mock_path_exists.side_effect = [False] + [True for _ in schema_list[:-1]]
        schema_gen = sw.get_schemas()
        open_calls = []
        write_calls = []
        mkdir_calls = []
        for schema in schema_gen:
            filename = "subjects.json" if schema is Subject else schema.default_filename()
            file_extension = "".join(Path(filename).suffixes)
            schema_filename = filename.replace(file_extension, "_schema.json")
            model_directory_name = schema_filename.replace("_schema.json", "")
            path = (
                Path("some_test_dir") / model_directory_name / schema.model_construct().schema_version / schema_filename
            )
            schema_json: dict = (
                TypeAdapter(list[schema]).json_schema()
                if schema in (Subject, Procedures)
                else schema.model_json_schema()
            )
            if schema is Subject:
                schema_json["minItems"] = 1
            schema_json_str: str = json.dumps(schema_json, indent=3)
            mkdir_calls.append(call("some_test_dir", 511))
            mkdir_calls.append(call(str(path.parent.parent), 511))
            mkdir_calls.append(call(path.parent, 511))

            open_calls.append(call(path, "w"))
            write_calls.append(call(schema_json_str))
        mock_mkdir.assert_has_calls(
            calls=mkdir_calls,
            any_order=True,
        )
        mock_file.assert_has_calls(open_calls, any_order=True)
        file_handle.write.assert_has_calls(write_calls, any_order=True)

    @patch("builtins.open", new_callable=mock_open())
    @patch("os.path.exists")
    @patch("os.mkdir")
    def test_write_draft_to_json(self, mock_mkdir: MagicMock, mock_path_exists: MagicMock, mock_file: MagicMock):
        """Tests that the draft schema is written to its unversioned filename."""
        mock_path_exists.return_value = False
        sw = SchemaWriter(["--output", "some_test_dir", "--draft"])

        sw.write_to_json()

        output_file = Path("some_test_dir") / "draft_metadata.json"
        mock_file.assert_any_call(output_file, "w")
        draft_schema_json = json.dumps(draft_metadata_schema(), indent=3)
        mock_file.return_value.__enter__.return_value.write.assert_any_call(draft_schema_json)
