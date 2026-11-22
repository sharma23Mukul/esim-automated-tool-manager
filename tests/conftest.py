"""Shared pytest fixtures for the eSim Tool Manager test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from esim_toolmanager.core.registry import ToolRegistry
from esim_toolmanager.platform.detect import PlatformInfo


@pytest.fixture
def test_manifest_path() -> Path:
    """Path to the test tool manifest."""
    return Path(__file__).parent / "fixtures" / "test_tools.yaml"


@pytest.fixture
def registry(test_manifest_path: Path) -> ToolRegistry:
    """A ToolRegistry loaded with the test manifest."""
    reg = ToolRegistry()
    reg.load(test_manifest_path)
    return reg


@pytest.fixture
def platform_linux() -> PlatformInfo:
    return PlatformInfo(
        os_name="linux", arch="x86_64", distro="ubuntu", distro_version="22.04"
    )


@pytest.fixture
def platform_windows() -> PlatformInfo:
    return PlatformInfo(
        os_name="windows", arch="x86_64", distro="windows", distro_version="10.0"
    )


@pytest.fixture
def platform_macos() -> PlatformInfo:
    return PlatformInfo(
        os_name="darwin", arch="arm64", distro="macos", distro_version="14.0"
    )
