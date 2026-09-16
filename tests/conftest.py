"""Shared pytest configuration."""

import pytest


def pytest_addoption(parser):
    """Register the opt-in flag for tests that require external services."""
    parser.addoption(
        "--run-online",
        action="store_true",
        default=False,
        help="run tests that require access to external services",
    )


def pytest_collection_modifyitems(config, items):
    """Skip online tests unless explicitly requested."""
    if config.getoption("--run-online"):
        return  # pragma: no cover

    skip_online = pytest.mark.skip(reason="requires --run-online and external network access")
    for item in items:
        if "online" in item.keywords:
            item.add_marker(skip_online)
