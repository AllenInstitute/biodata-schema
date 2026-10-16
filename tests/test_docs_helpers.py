"""Tests for documentation formatting, model discovery, and intermediate output."""

import json
from enum import Enum
from types import SimpleNamespace
from typing import Annotated, ClassVar, Dict, Optional, Union
from unittest.mock import Mock

import pytest
from biodata_models.organizations import Organization
from biodata_models.pid_names import PIDName
from pydantic import BaseModel, Field

from biodata_schema.base import DataModel, _GenericModel
from biodata_schema.utils.docs import model_generator, registries_generator, utils


class ExampleEnum(str, Enum):
    """Example choices."""

    FIRST = "First"
    SECOND = "Second"


class ExampleModel(DataModel):
    """Example model documentation."""

    count: int = Field(title="Count", description="Number of items")
    choice: ExampleEnum = ExampleEnum.FIRST
    registry: PIDName
    old: str = Field(default="", deprecated="Use count")
    older: str = Field(default="", deprecated=True)
    ignored: ClassVar[str] = "Not a model field"


class DerivedModel(ExampleModel):
    """Overrides an inherited field."""

    count: int = Field(title="Updated count")


class GenericExample(_GenericModel):
    """A model accepting arbitrary extra fields."""

    value: str


@pytest.mark.parametrize(
    "value, expected",
    [
        ("List[float | str]", "List[float or str]"),
        ("float | str", "float or str"),
        ("Annotated[a.First | b.Second, metadata]", "{First} or {Second}"),
        ("Annotated[int | str, metadata]", "{int} or {str}"),
        ("List[Annotated[a.First | b.Second,\nmetadata]]", "List[{First} or {Second}]"),
        ("Annotated[int, metadata]", "Annotated[int, metadata]"),
        ("Annotated", "Annotated"),
        ("int", "int"),
    ],
)
def test_union_string_formatting(value, expected):
    """String fallbacks preserve containers while formatting union members."""
    assert model_generator.check_for_union(value) == expected


@pytest.mark.parametrize(
    "annotation, expected",
    [
        (Dict[str, int], "Dict[str, int]"),
        (Union[int, str], "int or str"),
        (Optional[int], "Optional[int]"),
        (Annotated[int, "metadata"], "int"),
        (int, "int"),
        (ExampleModel, "{ExampleModel}"),
        (GenericExample, "{GenericExample}"),
        (ExampleEnum, "{ExampleEnum}"),
        (PIDName, "{PIDName}"),
    ],
)
def test_model_type_formatting(annotation, expected):
    """Shared type formatting handles containers, annotations, and model links."""
    assert model_generator.get_type_string(annotation) == expected


def test_field_metadata_annotations_are_not_unwrapped():
    """Pydantic field annotations remain on the existing fallback path."""
    annotation = Annotated[int, Field(title="Value")]
    assert model_generator.get_type_string(annotation).startswith("typing.Annotated[int, FieldInfo(")


def test_legacy_type_fallback():
    """Objects with legacy typing attributes still render their contained types."""
    legacy = SimpleNamespace(__origin__=list, __args__=(int,))
    assert model_generator.get_type_string(legacy) == "List[int]"
    assert model_generator._handle_class_types(legacy) is None


def test_class_type_error_is_handled(monkeypatch):
    """An unsupported subclass check does not break type formatting."""
    monkeypatch.setattr(model_generator, "issubclass", Mock(side_effect=TypeError), raising=False)
    assert model_generator._handle_class_types(ExampleModel) is None


def test_model_fields_and_markdown():
    """Inherited overrides, deprecations, descriptions, and links are preserved."""
    fields = model_generator.get_model_fields(DerivedModel, BaseModel)
    assert "object_type" not in fields
    assert "ignored" not in fields
    assert fields["count"][1].title == "Updated count"
    assert model_generator.get_model_fields(SimpleNamespace, BaseModel) == {}

    table = model_generator.generate_markdown_table(ExampleModel, BaseModel)
    assert "### ExampleModel\n\nExample model documentation." in table
    assert "| `count` | `int` | Count (Number of items) |" in table
    assert "| `choice` | {ExampleEnum} |" in table
    assert "| `registry` | {PIDName} |" in table
    assert "<del>`old`</del>" in table
    assert "**[DEPRECATED]** Use count." in table
    assert "<del>`older`</del>" in table


def test_model_module_generation(tmp_path):
    """Module discovery writes local models and enums, clears old output, and saves links."""
    source = tmp_path / "src"
    source.mkdir()
    module = source / "example.py"
    module.write_text(
        "from enum import Enum\n"
        "from biodata_schema.base import DataModel, _GenericModel\n"
        "class Model(DataModel):\n"
        "    value: int\n"
        "class Generic(_GenericModel):\n"
        "    value: str\n"
        "class Choice(str, Enum):\n"
        "    FIRST = 'First'\n"
        "class Unrelated:\n"
        "    pass\n"
        "not_a_class = 42\n"
    )
    output = tmp_path / "docs"
    old_output = output / "example"
    old_output.mkdir(parents=True)
    (old_output / "Obsolete.md").write_text("Obsolete")
    links = {}

    model_generator.process_module("example", str(module), str(source), str(output), links)
    model_generator.save_model_link_map(str(output), links)

    assert sorted(path.name for path in old_output.iterdir()) == ["Choice.md", "Generic.md", "Model.md"]
    assert "| `value` | `int` |" in (old_output / "Model.md").read_text()
    assert "| `FIRST` | `First` |" in (old_output / "Choice.md").read_text()
    assert json.loads((output / "model_links.json").read_text()) == {
        "{Model}": "[Model](example.md#model)",
        "{Generic}": "[Generic](example.md#generic)",
        "{Choice}": "[Choice](example.md#choice)",
    }


def test_module_generation_import_error(tmp_path, capsys):
    """A failed module import reports its path and error."""
    module = tmp_path / "broken.py"
    module.write_text("raise RuntimeError('broken module')\n")
    model_generator.process_module("broken", str(module), str(tmp_path), str(tmp_path / "docs"), {})

    assert f"Error processing {module}: broken module" in capsys.readouterr().out


def test_module_generation_subclass_error(tmp_path, monkeypatch):
    """Unsupported local classes are skipped without preventing module processing."""
    module = tmp_path / "unsupported.py"
    module.write_text("class Unsupported:\n    pass\n")
    subclass_check = Mock(side_effect=TypeError)
    monkeypatch.setattr(model_generator, "issubclass", subclass_check, raising=False)

    model_generator.process_module("unsupported", str(module), str(tmp_path), str(tmp_path / "docs"), {})

    subclass_check.assert_called_once()


def test_shared_output_and_link_merging(tmp_path):
    """Intermediate files are written and link updates preserve unrelated entries."""
    links = {}
    utils.save_model_info("Example", "### Example\n", "biodata_schema/core/example", str(tmp_path), links)
    assert (tmp_path / "biodata_schema/core/example/Example.md").read_text() == "### Example\n"
    assert links == {"{Example}": "[Example](example.md#example)"}

    utils.update_model_links(str(tmp_path), links)
    utils.update_model_links(str(tmp_path), {"{Other}": "[Other](other.md#other)"})
    assert json.loads((tmp_path / "model_links.json").read_text()) == links | {"{Other}": "[Other](other.md#other)"}
    assert "| `FIRST` | `First` |" in utils.generate_enum_table(ExampleEnum)


def test_registry_instance_field_discovery():
    """Unannotated instances fall back to public attributes and organization extras."""
    instance = SimpleNamespace(
        name="Example", abbreviation="EX", registry="ROR", registry_identifier="123", _private="hidden", ALL=[]
    )
    fields = registries_generator.determine_field_names({}, [("EXAMPLE", instance)], SimpleNamespace)
    assert fields == ["abbreviation", "name", "registry", "registry_identifier"]
    assert registries_generator.ensure_organization_fields(["name"], [("EXAMPLE", instance)]) == [
        "name",
        "abbreviation",
        "registry",
        "registry_identifier",
    ]


def test_empty_registry_instances(capsys):
    """An empty registry produces only its header and an explicit warning."""
    empty = type("Empty", (), {"__doc__": None})
    assert registries_generator.generate_model_instance_table(empty) == "### Empty\n\n"
    assert "Warning: No model instances found in Empty" in capsys.readouterr().out


def test_registry_schema_tables(capsys):
    """Schema tables render field descriptions and fall back to titles or unknown types."""
    schema = SimpleNamespace(
        __name__="Schema",
        model_fields={
            "count": Field(title="Count", description="Number of items"),
            "title_only": Field(title="Title only"),
            "unknown": SimpleNamespace(),
        },
    )
    schema.model_fields["count"].annotation = int
    table = registries_generator.generate_model_schema_table(schema)
    assert "| `count` | `int` | Number of items |" in table
    assert "| `title_only` | `None` | Title only |" in table
    assert "| `unknown` | `Unknown` |  |" in table

    empty = type("Empty", (BaseModel,), {})
    assert registries_generator.generate_model_schema_table(empty).startswith("### Empty\n\n")
    assert "Warning: No fields found" in capsys.readouterr().out
    assert registries_generator.generate_model_schema_table(ExampleEnum).startswith("### ExampleEnum\n\n")
    assert "does not appear to be a valid Pydantic model" in capsys.readouterr().out


def test_registry_type_detection(monkeypatch):
    """Registry routing distinguishes enums, schema classes, instances, and unsupported inputs."""
    assert registries_generator.detect_registry_type(ExampleEnum) == "enum"
    assert registries_generator.detect_registry_type(PIDName) == "model_schema"
    assert registries_generator.detect_registry_type(type("Empty", (), {})) == "unknown"
    assert registries_generator.detect_registry_type(Organization) == "model_instance"

    monkeypatch.setattr(registries_generator, "issubclass", Mock(side_effect=TypeError), raising=False)
    assert registries_generator.detect_registry_type(PIDName) == "model_schema"


def test_registry_generation_dispatch(tmp_path, monkeypatch, capsys):
    """Registry generation writes each supported kind and reports unsupported or failed inputs."""
    monkeypatch.setattr(
        registries_generator, "__file__", str(tmp_path / "src/biodata_schema/utils/docs/registries_generator.py")
    )
    unknown = type("Unsupported", (), {})
    broken = SimpleNamespace(__name__="Broken")
    monkeypatch.setattr(registries_generator, "registries", [ExampleEnum, Organization, PIDName, unknown, broken])

    registries_generator.generate_registry_docs()

    output = tmp_path / "docs/base/models"
    links = json.loads((output / "model_links.json").read_text())
    assert "{ExampleEnum}" in links
    assert "{Organization}" in links
    assert "{PIDName}" in links
    messages = capsys.readouterr().out
    assert "Unknown registry type for Unsupported" in messages
    assert "Error processing registry Broken:" in messages
    assert "Registry documentation generated successfully." in messages
