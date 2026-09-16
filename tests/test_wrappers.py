"""Test wrappers module"""

from pathlib import Path, PureWindowsPath

from biodata_schema.components.wrappers import AssetPath


class TestAssetPath:
    """Test AssetPath class"""

    def test_asset_path(self):
        """Test AssetPath with valid path"""
        asset_path = AssetPath("/path/to/file.txt")
        asset_path = AssetPath(Path("/path/to/file.txt"))
        assert str(asset_path) == "/path/to/file.txt"

        asset_path = AssetPath(PureWindowsPath(r"path\to\file.txt"))
        assert str(asset_path) == "path/to/file.txt"
