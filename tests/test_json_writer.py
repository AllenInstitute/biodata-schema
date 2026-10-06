"""Module to test json_writer classes."""

import json
import os
from pathlib import Path
from typing import Annotated, Optional, Union
from unittest.mock import MagicMock, call, mock_open, patch

from jsonschema import Draft202012Validator
from pydantic import BaseModel

from biodata_schema.base import DraftRequirement
from biodata_schema.core.metadata import Metadata
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
from examples.subject import s as subject


class TestSchemaWriter:
    """Tests for SchemaWriter methods"""

    TEST_ARGS = ["--output", "some_test_dir"]

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

        assert set(schema["properties"]) == {"location", "data_description", "subject", "acquisition", "instrument"}
        assert set(schema["required"]) == set(schema["properties"])
        assert schema["additionalProperties"] is True
        assert set(schema["$defs"]) == {"License"}

        expected_nested_fields = {
            "data_description": {"project_name", "license"},
            "subject": {"subject_id"},
            "acquisition": {"acquisition_start_time"},
            "instrument": {"instrument_id"},
        }
        for field_name, fields in expected_nested_fields.items():
            nested_schema = schema["properties"][field_name]
            assert set(nested_schema["properties"]) == fields
            assert set(nested_schema["required"]) == fields
            assert nested_schema["additionalProperties"] is True

    def test_full_metadata_validates_against_draft_schema(self):
        """Tests that a full metadata record validates against the draft schema."""
        metadata = Metadata.model_construct(
            name="full_metadata",
            location="s3://bucket/full_metadata",
            other_identifiers=None,
            subject=subject,
            data_description=data_description,
            procedures=procedures,
            instrument=instrument,
            processing=processing,
            acquisition=acquisition,
            quality_control=quality_control,
            model=model,
        )
        metadata_json = json.loads(metadata.model_dump_json(by_alias=True))

        Draft202012Validator(draft_metadata_schema()).validate(metadata_json)

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
            filename = schema.default_filename()
            file_extension = "".join(Path(filename).suffixes)
            schema_filename = filename.replace(file_extension, "_schema.json")
            path = Path("some_test_dir") / schema_filename
            schema_json: dict = schema.model_json_schema()
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
            filename = schema.default_filename()
            file_extension = "".join(Path(filename).suffixes)
            schema_filename = filename.replace(file_extension, "_schema.json")
            model_directory_name = schema_filename.replace("_schema.json", "")
            path = (
                Path("some_test_dir") / model_directory_name / schema.model_construct().schema_version / schema_filename
            )
            schema_json: dict = schema.model_json_schema()
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
