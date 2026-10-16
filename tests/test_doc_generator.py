"""Tests for registry documentation generation."""

import json

import pytest

from biodata_schema.utils.docs import doc_generator


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
