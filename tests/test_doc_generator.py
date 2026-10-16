"""Tests for model and registry documentation generation."""

import json
import pathlib
from types import SimpleNamespace
from typing import Literal, Optional
from unittest.mock import Mock, call

import pytest
from biodata_models.devices import DataInterface
from biodata_models.organizations import Organization
from biodata_models.registries import Registry
from biodata_models.species import Species

from biodata_schema.utils.docs import doc_generator, model_generator, registries_generator


@pytest.mark.parametrize("stale_intermediate", [False, True])
def test_registry_docs_remove_deleted_modules(tmp_path, monkeypatch, stale_intermediate):
    """Deleted modules are removed even when old intermediate docs remain."""
    monkeypatch.setattr(doc_generator, "__file__", str(tmp_path / "src/biodata_schema/utils/docs/doc_generator.py"))
    model_docs = tmp_path / "docs/base/models"
    registries = model_docs / "biodata_models"
    current_registry = registries / "data_levels"
    current_registry.mkdir(parents=True)
    (current_registry / "DataLevel.md").write_text("### DataLevel\n\nCurrent model\n")
    (model_docs / "model_links.json").write_text(json.dumps({}))

    if stale_intermediate:
        stale_registry = registries / "process_names"
        stale_registry.mkdir()
        (stale_registry / "ProcessName.md").write_text("### ProcessName\n\nObsolete model\n")

    output = tmp_path / "docs/source/biodata_models"
    output.mkdir(parents=True)
    obsolete_page = output / "process_names.md"
    obsolete_page.write_text("# Process_names\n\nObsolete page\n")
    external_page = output / "external.md"
    external_page.write_text("# External registries\n\nHand-written documentation\n")

    doc_generator.generate_all_registry_documentation()

    assert not obsolete_page.exists()
    assert (output / "data_levels.md").read_text() == (
        "# Data_levels\n\n## Model definitions\n\n### DataLevel\n\nCurrent model\n\n\n"
    )
    assert external_page.read_text() == "# External registries\n\nHand-written documentation\n"


def test_process_registry_skips_deleted_module(tmp_path, monkeypatch):
    """A direct generation request cannot recreate a removed module's page."""
    monkeypatch.setattr(doc_generator, "__file__", str(tmp_path / "src/biodata_schema/utils/docs/doc_generator.py"))
    registry_docs = tmp_path / "docs/base/models/biodata_models/process_names"
    registry_docs.mkdir(parents=True)
    (registry_docs / "ProcessName.md").write_text("### ProcessName\n")

    doc_generator.process_registry("process_names", "docs/source/biodata_models")

    assert not (tmp_path / "docs/source/biodata_models/process_names.md").exists()


@pytest.mark.parametrize("registry_value", [Registry.NCBI, Registry.NCBI.value])
def test_registry_table_uses_enum_value(registry_value):
    """Enum members and serialized values produce the same human-readable label."""
    table = registries_generator.create_table_structure(
        ["registry"], [("EXAMPLE", SimpleNamespace(registry=registry_value))]
    )

    assert table == (
        "| Name | registry |\n|------|------|\n| `EXAMPLE` | `National Center for Biotechnology Information (NCBI)` |\n"
    )


@pytest.mark.parametrize("model_class, registry", [(Species, Registry.NCBI), (Organization, Registry.ROR)])
def test_registry_model_docs_use_enum_values(model_class, registry):
    """Actual registry models never render Enum member names in registry cells."""
    table = registries_generator.generate_model_instance_table(model_class)

    assert f"`{registry.value}`" in table
    assert "`Registry." not in table


def test_registry_acronym_links_are_preserved():
    """Legacy plain-string acronyms still use the existing registry links."""
    table = registries_generator.create_table_structure(["registry"], [("EXAMPLE", SimpleNamespace(registry="ROR"))])

    assert "[ROR](biodata_models/registries.md#registry)" in table


@pytest.mark.parametrize(
    "annotation, expected",
    [
        (Literal[DataInterface.USB], '"USB"'),
        (Literal[DataInterface.USB, DataInterface.USB.value, 1], '"USB" or "USB" or 1'),
        (Literal["USB"], '"USB"'),
        (Literal[1, 2], "1 or 2"),
        (Optional[Literal[DataInterface.USB]], 'Optional["USB"]'),
        (list[Literal[DataInterface.USB]], 'List["USB"]'),
    ],
)
def test_literal_types_use_enum_values(annotation, expected):
    """Literal enums render their values rather than runtime-dependent names."""
    assert model_generator.get_type_string(annotation) == expected


@pytest.mark.parametrize(
    "path_type",
    [
        pathlib.Path,
        pathlib.PurePath,
        pathlib.PosixPath,
        pathlib.PurePosixPath,
        pathlib.WindowsPath,
        pathlib.PureWindowsPath,
    ],
)
def test_path_types_use_public_names(path_type):
    """Public pathlib types never expose Python's private implementation modules."""
    expected = f"pathlib.{path_type.__name__}"
    assert model_generator.get_type_string(path_type) == expected
    assert model_generator.get_type_string(Optional[path_type]) == f"Optional[{expected}]"
    assert model_generator.get_type_string(list[path_type]) == f"List[{expected}]"


@pytest.fixture
def docs_workspace(tmp_path, monkeypatch):
    """Isolate all documentation inputs and outputs from the repository."""
    monkeypatch.setattr(doc_generator, "__file__", str(tmp_path / "src/biodata_schema/utils/docs/doc_generator.py"))
    model_docs = tmp_path / "docs/base/models"
    model_docs.mkdir(parents=True)
    (model_docs / "model_links.json").write_text(
        json.dumps(
            {
                "{Code}": "[Code](components/identifiers.md#code)",
                "{Registry}": "[Registry](biodata_models/registries.md#registry)",
            }
        )
    )
    return tmp_path


@pytest.mark.parametrize("core_file", ["data_description", "metadata"])
def test_core_page_assembly(docs_workspace, core_file):
    """Core models come first and metadata does not repeat nested definitions."""
    base = docs_workspace / "docs/base/core"
    base.mkdir()
    (base / f"{core_file}.md").write_text(f"# {core_file}\n")
    models = docs_workspace / "docs/base/models/biodata_schema/core" / core_file
    models.mkdir(parents=True)
    model_name = "".join(word.capitalize() for word in core_file.split("_"))
    (models / f"{model_name}.md").write_text(f"### {model_name}\n")
    (models / "AAA.md").write_text("### AAA\n\n{Code}\n")
    (models / "ZZZ.md").write_text("### ZZZ\n")
    (models / "ignored.txt").write_text("Ignored")

    doc_generator.process_core_file(core_file)

    expected = f"# {core_file}\n\n## Core file\n\n### {model_name}\n"
    if core_file != "metadata":
        expected += "\n\n## Model definitions\n\n### AAA\n\n[Code](components/identifiers.md#code)\n\n\n### ZZZ\n"
    assert (docs_workspace / f"docs/source/{core_file}.md").read_text() == expected


@pytest.mark.parametrize("missing", ["base", "models", "markdown"])
def test_core_page_missing_inputs(docs_workspace, capsys, missing):
    """Missing core inputs produce warnings without writing a partial page."""
    if missing != "base":
        base = docs_workspace / "docs/base/core"
        base.mkdir()
        (base / "subject.md").write_text("# Subject\n")
    if missing == "markdown":
        (docs_workspace / "docs/base/models/biodata_schema/core/subject").mkdir(parents=True)

    doc_generator.process_core_file("subject")

    assert "Warning:" in capsys.readouterr().out
    assert not (docs_workspace / "docs/source/subject.md").exists()


def test_component_page_assembly(docs_workspace):
    """Component assembly sorts models and fixes same-page and registry links."""
    models = docs_workspace / "docs/base/models/biodata_schema/components/identifiers"
    models.mkdir(parents=True)
    (models / "B.md").write_text("### B\n")
    (models / "A.md").write_text("### A\n\n{Code} {Registry}\n")
    (models.parent / "ignored.txt").write_text("Ignored")

    doc_generator.generate_all_component_documentation()

    assert (docs_workspace / "docs/source/components/identifiers.md").read_text() == (
        "# Identifiers\n\n## Model definitions\n\n"
        "### A\n\n[Code](#code) [Registry](../biodata_models/registries.md#registry)\n\n\n### B\n\n\n"
    )


@pytest.mark.parametrize("empty", [False, True])
def test_component_page_missing_inputs(docs_workspace, capsys, empty):
    """Missing or empty component folders do not generate empty pages."""
    if empty:
        (docs_workspace / "docs/base/models/biodata_schema/components/identifiers").mkdir(parents=True)

    doc_generator.process_components("identifiers", "docs/source/components")

    assert "Warning:" in capsys.readouterr().out
    assert not (docs_workspace / "docs/source/components/identifiers.md").exists()


def test_component_dispatch_missing_directory(docs_workspace, capsys):
    """Component discovery reports a missing intermediate root."""
    doc_generator.generate_all_component_documentation()

    assert "Warning: Components directory not found:" in capsys.readouterr().out


@pytest.mark.parametrize("empty", [False, True])
def test_registry_page_missing_inputs(docs_workspace, capsys, empty):
    """Installed registry modules still require nonempty generated inputs."""
    if empty:
        (docs_workspace / "docs/base/models/biodata_models/data_levels").mkdir(parents=True)

    doc_generator.process_registry("data_levels", "docs/source/biodata_models")

    assert "Warning:" in capsys.readouterr().out
    assert not (docs_workspace / "docs/source/biodata_models/data_levels.md").exists()


def test_registry_page_replaces_model_links(docs_workspace):
    """Registry pages resolve model placeholders through the shared link map."""
    models = docs_workspace / "docs/base/models/biodata_models/data_levels"
    models.mkdir(parents=True)
    (models / "DataLevel.md").write_text("### DataLevel\n\n{Registry}\n")

    doc_generator.generate_all_registry_documentation()

    assert (docs_workspace / "docs/source/biodata_models/data_levels.md").read_text() == (
        "# Data_levels\n\n## Model definitions\n\n"
        "### DataLevel\n\n[Registry](biodata_models/registries.md#registry)\n\n\n"
    )


def test_registry_dispatch_missing_directory(docs_workspace, capsys):
    """Registry discovery warns when no intermediate directory exists."""
    doc_generator.generate_all_registry_documentation()

    assert "Warning: Registry directory not found:" in capsys.readouterr().out


def test_core_dispatch_maps_subject_collection(monkeypatch):
    """Core dispatch maps the subjects collection to its singular docs page."""
    process_core_file = Mock()
    monkeypatch.setattr(doc_generator, "process_core_file", process_core_file)

    doc_generator.generate_all_core_documentation()

    assert process_core_file.call_args_list == [
        call("subject" if name == "subjects" else name) for name in doc_generator.CORE_FILES
    ] + [call("metadata")]
