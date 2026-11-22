"""Tests for esim_toolmanager.core.updater."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from esim_toolmanager.core.updater import ToolUpdater, UpdateInfo
from esim_toolmanager.platform.detect import PlatformInfo


@pytest.fixture
def updater_linux(registry, platform_linux):
    return ToolUpdater(registry, platform_linux, dry_run=True)


class TestUpdateInfo:
    def test_update_info_creation(self):
        info = UpdateInfo(
            tool_id="mock_tool",
            tool_name="MockTool",
            installed_version="1.0",
            min_version="1.0",
            is_installed=True,
            is_outdated=False,
            message="up to date",
        )
        assert info.is_installed is True
        assert info.is_outdated is False


class TestToolUpdater:
    @patch("esim_toolmanager.core.updater.get_command_version", return_value="2.0.0")
    def test_check_tool_up_to_date(self, _mock, updater_linux, registry):
        tool = registry.get_tool("mock_tool")
        info = updater_linux.check_tool(tool)
        assert info.is_installed is True
        assert info.is_outdated is False
        assert "up to date" in info.message

    @patch("esim_toolmanager.core.updater.get_command_version", return_value="0.5.0")
    def test_check_tool_outdated(self, _mock, updater_linux, registry):
        tool = registry.get_tool("mock_tool")
        info = updater_linux.check_tool(tool)
        assert info.is_installed is True
        assert info.is_outdated is True
        assert "below" in info.message

    @patch("esim_toolmanager.core.updater.get_command_version", return_value=None)
    def test_check_tool_not_installed(self, _mock, updater_linux, registry):
        tool = registry.get_tool("mock_tool")
        info = updater_linux.check_tool(tool)
        assert info.is_installed is False
        assert "not installed" in info.message

    @patch("esim_toolmanager.core.updater.get_command_version", return_value="0.5.0")
    def test_get_outdated(self, _mock, updater_linux):
        outdated = updater_linux.get_outdated()
        assert len(outdated) > 0
        assert all(o.is_outdated for o in outdated)

    def test_update_unknown_tool(self, updater_linux):
        res = updater_linux.update_tool("nonexistent")
        assert res.success is False
        assert "not found" in res.message

    def test_update_no_backend(self, registry):
        platform_unsupported = PlatformInfo("linux", "x86_64", "gentoo", "1.0")
        updater = ToolUpdater(registry, platform_unsupported, dry_run=True)
        res = updater.update_tool("mock_tool")
        assert res.success is False
        assert "No package-manager" in res.message

    @patch("esim_toolmanager.core.updater.get_backend")
    def test_update_tool_dry_run(self, mock_get_backend, updater_linux):
        mock_b = MagicMock()
        mock_b.update.return_value = True
        mock_get_backend.return_value = mock_b

        res = updater_linux.update_tool("mock_tool")
        assert res.success is True
        assert res.dry_run is True
        assert "Would update" in res.message

    @patch("esim_toolmanager.core.updater.get_backend")
    def test_update_tool_failure(self, mock_get_backend, updater_linux):
        mock_b = MagicMock()
        mock_b.update.side_effect = RuntimeError("network failed")
        mock_get_backend.return_value = mock_b

        res = updater_linux.update_tool("mock_tool")
        assert res.success is False
        assert "failed" in res.message.lower()

    @patch("esim_toolmanager.core.updater.get_command_version", return_value="0.5.0")
    @patch("esim_toolmanager.core.updater.get_backend")
    def test_update_all(self, mock_get_backend, _mock_ver, updater_linux):
        mock_b = MagicMock()
        mock_b.update.return_value = True
        mock_get_backend.return_value = mock_b

        results = updater_linux.update_all()
        assert len(results) >= 1
        assert all(r.success for r in results)
