"""Tests for esim_toolmanager.core.installer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from esim_toolmanager.core.installer import ToolInstaller
from esim_toolmanager.platform.detect import PlatformInfo


@pytest.fixture
def linux_installer(registry, platform_linux):
    return ToolInstaller(registry, platform_linux, dry_run=True)


@pytest.fixture
def win_installer(registry, platform_windows):
    return ToolInstaller(registry, platform_windows, dry_run=True)


class TestToolInstaller:
    def test_install_unknown_tool(self, linux_installer):
        result = linux_installer.install("nonexistent")
        assert result.success is False
        assert "not found" in result.message

    def test_install_unsupported_platform(self, win_installer):
        result = win_installer.install("optional_tool")  # linux only
        assert result.success is False
        assert "not supported" in result.message

    @patch("esim_toolmanager.core.installer.get_backend")
    def test_install_success_dry_run(self, mock_get_backend, linux_installer):
        mock_backend = MagicMock()
        mock_backend.install.return_value = True
        mock_get_backend.return_value = mock_backend

        result = linux_installer.install("mock_tool")
        assert result.success is True
        assert result.dry_run is True
        assert "MockTool" in result.message

    @patch("esim_toolmanager.core.installer.get_backend")
    def test_install_with_version(self, mock_get_backend, linux_installer):
        mock_backend = MagicMock()
        mock_backend.install.return_value = True
        mock_get_backend.return_value = mock_backend

        result = linux_installer.install("mock_tool", version="2.0")
        assert result.success is True
        assert result.version_installed == "2.0"

    @patch("esim_toolmanager.core.installer.get_backend")
    def test_install_backend_failure(self, mock_get_backend, linux_installer):
        mock_backend = MagicMock()
        mock_backend.install.side_effect = RuntimeError("network error")
        mock_get_backend.return_value = mock_backend

        result = linux_installer.install("mock_tool")
        assert result.success is False
        assert "failed" in result.message.lower()

    def test_install_no_backend_available(self, registry):
        p = PlatformInfo("linux", "x86_64", "gentoo", "2.14")
        installer = ToolInstaller(registry, p, dry_run=True)
        # dep_cycle_a has no packages defined
        result = installer.install("dep_cycle_a")
        assert result.success is False

    @patch("esim_toolmanager.core.installer.get_backend")
    def test_install_all_required(self, mock_get_backend, linux_installer):
        mock_backend = MagicMock()
        mock_backend.install.return_value = True
        mock_get_backend.return_value = mock_backend

        results = linux_installer.install_all_required()
        assert len(results) >= 1
        assert all(r.success for r in results)

    def test_select_backend_prefers_platform_pm(self, registry, platform_linux):
        installer = ToolInstaller(registry, platform_linux, dry_run=True)
        tool = registry.get_tool("mock_tool")
        backend = installer._select_backend(tool)
        assert backend == "apt"  # Ubuntu → apt
