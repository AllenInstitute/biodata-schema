"""testing examples"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import TypeAdapter

from biodata_schema.core.procedures import Procedures
from biodata_schema.core.subject import Subject
from biodata_schema.utils.examples_generator import ExamplesGenerator
from biodata_schema.utils.json_writer import SchemaWriter

EXAMPLES_DIR = Path(__file__).parents[1] / "examples"
EXAMPLE_FILES = sorted(path for path in EXAMPLES_DIR.glob("*.py") if path.name != "__init__.py")


@pytest.fixture(scope="module")
def generated_examples(tmp_path_factory):
    """Build the examples in a temporary directory."""
    temp_path = tmp_path_factory.mktemp("examples")
    ExamplesGenerator().generate_all_examples(output_directory=temp_path)
    return temp_path


class TestExamples:
    """tests for examples"""

    @pytest.mark.parametrize("example_file", EXAMPLE_FILES, ids=lambda path: path.stem)
    def test_examples_generated(self, generated_examples, example_file):
        """Every example builds and its output passes model and schema validation."""
        filename = example_file.with_suffix(".json").name
        example_path = generated_examples / filename
        assert example_path.exists(), f"{filename} was not generated."

        models = [
            model
            for model in SchemaWriter.get_schemas()
            if filename == SchemaWriter.schema_filename(model).replace("_schema.json", ".json")
            or filename.endswith("_" + SchemaWriter.schema_filename(model).replace("_schema.json", ".json"))
        ]
        assert len(models) == 1, f"{filename} must match exactly one core model."
        model = models[0]
        serialized = example_path.read_bytes()
        adapter = TypeAdapter(list[model] if model in (Subject, Procedures) else model)
        adapter.validate_json(serialized)
        Draft202012Validator(SchemaWriter.model_schema(model)).validate(json.loads(serialized))

    @pytest.mark.parametrize("example_file", EXAMPLE_FILES, ids=lambda path: path.stem)
    def test_examples_do_not_use_model_construct(self, example_file):
        """Examples must never bypass model validation."""
        assert "model_construct" not in example_file.read_text()
