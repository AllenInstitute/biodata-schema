"""testing examples"""

import json
from pathlib import Path

import pytest

from biodata_schema.utils.examples_generator import ExamplesGenerator

EXAMPLES_DIR = Path(__file__).parents[1] / "examples"


@pytest.fixture(scope="module")
def generated_examples(tmp_path_factory):
    """Build the examples in a temporary directory."""
    temp_path = tmp_path_factory.mktemp("examples")
    ExamplesGenerator().generate_all_examples(output_directory=temp_path)
    return temp_path


class TestExamples:
    """tests for examples"""

    def test_examples_generated(self, generated_examples):
        """Test that each example file generates valid JSON."""
        example_files = [
            path.with_suffix(".json").name for path in EXAMPLES_DIR.glob("*.py") if path.name != "__init__.py"
        ]

        for example_file in example_files:
            example_path = generated_examples / example_file
            assert example_path.exists(), f"{example_file} was not generated."

            with example_path.open() as f:
                json_data = json.load(f)
            assert isinstance(json_data, dict), f"{example_file} does not contain valid JSON."
