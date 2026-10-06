"""Utility method to write Pydantic schemas to JSON"""

import argparse
import copy
import importlib
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterator, get_args

from pydantic import BaseModel

from biodata_schema import core
from biodata_schema.base import DataCoreModel, DraftRequirement
from biodata_schema.core.metadata import Metadata

# Import all modules in core package
for mod in core.__loader__.get_resource_reader().contents():
    if "__" not in mod and mod.endswith(".py"):
        importlib.import_module(f"biodata_schema.core.{mod.replace('.py', '')}")


def _model_types(annotation: Any) -> Iterator[type[BaseModel]]:
    """Yield Pydantic model types found in an annotation."""
    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        yield annotation
        return

    for argument in get_args(annotation):
        yield from _model_types(argument)


def _is_draft_requirement(field_info: Any) -> bool:
    """Return whether a Pydantic field has the draft-requirement marker."""
    return any(
        metadata is DraftRequirement or isinstance(metadata, DraftRequirement) for metadata in field_info.metadata
    )


def _has_draft_requirements(model: type[BaseModel], visited: set[type[BaseModel]] | None = None) -> bool:
    """Return whether a model contains a draft-required field at any depth."""
    visited = set() if visited is None else visited
    if model in visited:
        return False
    visited.add(model)

    for field in model.model_fields.values():
        if _is_draft_requirement(field):
            return True
        if any(_has_draft_requirements(child, visited.copy()) for child in _model_types(field.annotation)):
            return True
    return False


def _field_schema(source_schema: dict, field_name: str, field_info: Any) -> dict:
    """Copy a field schema from a Pydantic model schema without its default."""
    schema_name = field_info.serialization_alias or field_info.alias or field_name
    schema = copy.deepcopy(source_schema["properties"][schema_name])
    schema.pop("default", None)
    return schema


def _project_model_schema(model: type[BaseModel], definitions: dict[str, dict]) -> dict:
    """Build a schema containing only draft-required fields from a model."""
    source_schema = model.model_json_schema()
    definitions.update(source_schema.get("$defs", {}))

    properties = {}
    required = []
    for field_name, field_info in model.model_fields.items():
        output_field_name = field_info.serialization_alias or field_info.alias or field_name
        if _is_draft_requirement(field_info):
            properties[output_field_name] = _field_schema(source_schema, field_name, field_info)
            required.append(output_field_name)
            continue

        child_models = [child for child in _model_types(field_info.annotation) if _has_draft_requirements(child)]
        if not child_models:
            continue

        # Draft-required fields in this repository are direct fields of nested
        # objects. Keep separate projections for union members if another
        # draft requirement is added later.
        if len(child_models) == 1:
            child_schema = _project_model_schema(child_models[0], definitions)
        else:
            child_schema = {
                "anyOf": [_project_model_schema(child, definitions) for child in child_models],
            }

        source_field_schema = _field_schema(source_schema, field_name, field_info)
        for metadata_name in ("title", "description"):
            if metadata_name in source_field_schema:
                child_schema[metadata_name] = source_field_schema[metadata_name]

        properties[output_field_name] = child_schema
        required.append(output_field_name)

    projected = {
        "title": source_schema.get("title", model.__name__),
        "type": "object",
        "additionalProperties": True,
        "properties": properties,
        "required": required,
    }
    if "description" in source_schema:
        projected["description"] = source_schema["description"]
    return projected


def _add_referenced_definitions(schema: dict, definitions: dict[str, dict]) -> None:
    """Add only the definitions referenced by a projected schema."""
    referenced = {}
    pending = list()

    def find_references(value: Any) -> None:
        if isinstance(value, dict):
            reference = value.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/$defs/"):
                pending.append(reference.removeprefix("#/$defs/"))
            for child in value.values():
                find_references(child)
        elif isinstance(value, list):
            for child in value:
                find_references(child)

    find_references(schema)
    while pending:
        definition_name = pending.pop()
        if definition_name in referenced or definition_name not in definitions:
            continue
        definition = copy.deepcopy(definitions[definition_name])
        referenced[definition_name] = definition
        find_references(definition)

    if referenced:
        schema["$defs"] = referenced


def draft_metadata_schema() -> dict:
    """Return the permissive schema for draft metadata records."""
    definitions = {}
    schema = _project_model_schema(Metadata, definitions)
    _add_referenced_definitions(schema, definitions)
    return schema


class SchemaWriter:
    """Class to write Pydantic schemas to JSON"""

    DEFAULT_FILE_PATH = os.getcwd()
    DRAFT_METADATA_FILENAME = "draft_metadata.json"

    def __init__(self, args: list) -> None:
        """Initialize schema writer class."""
        self.args = args
        self.configs = self._parse_arguments(args)

    def _parse_arguments(self, args: list) -> argparse.Namespace:
        """Parses sys args with argparse"""

        help_message = "Output directory, defaults to current working directory"

        parser = argparse.ArgumentParser()

        parser.add_argument(
            "-o",
            "--output",
            required=False,
            default=self.DEFAULT_FILE_PATH,
            help=help_message,
        )

        parser.add_argument(
            "--attach-version",
            action="store_true",
            help="Add extra directory with schema version number",
        )
        parser.set_defaults(attach_version=False)

        parser.add_argument(
            "--draft",
            action="store_true",
            help="Also write the permissive draft metadata schema",
        )
        parser.set_defaults(draft=False)

        optional_args = parser.parse_args(args)

        return optional_args

    @staticmethod
    def get_schemas() -> Iterator[DataCoreModel]:
        """
        Returns Iterator of DataCoreModel classes
        """

        for model in DataCoreModel.__subclasses__():
            yield model

    def write_to_json(self) -> None:
        """
        Writes Pydantic models to JSON file.
        """
        schemas_to_write = self.get_schemas()
        output_path = self.configs.output
        for schema in schemas_to_write:
            filename = schema.default_filename()
            file_extension = "".join(Path(filename).suffixes)
            schema_filename = filename.replace(file_extension, "_schema.json")
            if self.configs.attach_version:
                schema_version = schema.model_construct().schema_version
                model_directory_name = schema_filename.replace("_schema.json", "")
                sub_directory = Path(output_path) / model_directory_name / schema_version
                output_file = sub_directory / schema_filename
            else:
                output_file = Path(output_path) / schema_filename

            if not os.path.exists(output_file.parent):
                os.makedirs(output_file.parent)

            with open(output_file, "w") as f:
                schema_json: dict = schema.model_json_schema()
                schema_json_str: str = json.dumps(schema_json, indent=3)
                f.write(schema_json_str)

        if self.configs.draft:
            self.write_draft_to_json()

    def write_draft_to_json(self) -> None:
        """Write the permissive draft metadata schema to ``draft_metadata.json``."""
        output_file = Path(self.configs.output) / self.DRAFT_METADATA_FILENAME
        if not os.path.exists(output_file.parent):
            os.makedirs(output_file.parent)

        with open(output_file, "w") as f:
            f.write(json.dumps(draft_metadata_schema(), indent=3))


if __name__ == "__main__":
    """User defined argument for output directory"""
    sys_args = sys.argv[1:]
    s = SchemaWriter(sys_args)
    s.write_to_json()
