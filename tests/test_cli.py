"""Tests for esim_toolmanager.cli."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from esim_toolmanager.cli import build_parser, main


class TestBuildParser:
    def test_parser_created(self):
        parser = build_parser()
        assert parser is not None

    def test_version_flag(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "0.1.0" in captured.out

    def test_no_command_shows_help(self, capsys):
        code = main([])
        assert code == 0


class TestCmdList:
    @patch("esim_toolmanager.cli.get_command_version", return_value=None)
    def test_list_text_output(self, _mock, registry, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "list"])
        assert code == 0
        out = capsys.readouterr().out
        assert "MockTool" in out

    @patch("esim_toolmanager.cli.get_command_version", return_value=None)
    def test_list_json_output(self, _mock, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--json", "--dry-run", "list"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)

    @patch("esim_toolmanager.cli.get_command_version", return_value="2.0.0")
    def test_list_installed_tool(self, _mock, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "list"])
        assert code == 0
        out = capsys.readouterr().out
        assert "installed" in out or "✅" in out

    @patch("esim_toolmanager.cli.get_command_version", return_value=None)
    def test_list_required_filter(self, _mock, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "list", "--required"])
        assert code == 0
        out = capsys.readouterr().out
        assert "MockTool" in out

    @patch("esim_toolmanager.cli.get_command_version", return_value=None)
    def test_list_category_filter(self, _mock, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "list", "--category", "simulation"])
        assert code == 0


class TestCmdCheck:
    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="2.0.0")
    def test_check_all_ok(self, _mock, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "check"])
        assert code == 0

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value=None)
    def test_check_missing_deps(self, _mock, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "check"])
        assert code != 0  # missing required tools

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="2.0.0")
    def test_check_json(self, _mock, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--json", "--dry-run", "check"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert "summary" in data
        assert "tools" in data


class TestCmdInstall:
    def test_install_no_tool_or_all(self, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "install"])
        assert code != 0

    @patch("esim_toolmanager.core.installer.get_backend")
    def test_install_dry_run(self, mock_gb, capsys, test_manifest_path):
        mock_backend = MagicMock()
        mock_backend.install.return_value = True
        mock_gb.return_value = mock_backend
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "install", "mock_tool"])
        assert code == 0

    def test_install_unknown_tool(self, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "install", "nope"])
        assert code != 0


class TestCmdDoctor:
    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="2.0.0")
    def test_doctor_markdown(self, _mock, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "doctor"])
        assert code == 0
        out = capsys.readouterr().out
        assert "# eSim Tool Manager" in out

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="2.0.0")
    def test_doctor_json(self, _mock, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--json", "--dry-run", "doctor"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert "all_ok" in data


class TestCmdConfigure:
    def test_configure_export_bash(self, capsys, test_manifest_path, tmp_path):
        cfg_path = tmp_path / "cfg.yaml"
        code = main([
            "--manifest", str(test_manifest_path),
            "--config", str(cfg_path),
            "--dry-run", "configure", "--export", "--shell", "bash",
        ])
        assert code == 0
        out = capsys.readouterr().out
        assert "export" in out or "Generated" in out

    def test_configure_specific_tool(self, capsys, test_manifest_path, tmp_path):
        cfg_path = tmp_path / "cfg.yaml"
        code = main([
            "--manifest", str(test_manifest_path),
            "--config", str(cfg_path),
            "--dry-run", "configure", "mock_tool",
        ])
        assert code == 0

    def test_configure_unknown_tool(self, capsys, test_manifest_path, tmp_path):
        code = main([
            "--manifest", str(test_manifest_path),
            "--config", str(tmp_path / "c.yaml"),
            "--dry-run", "configure", "nope",
        ])
        assert code != 0


class TestCmdOutdated:
    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="2.0.0")
    @patch("esim_toolmanager.core.updater.get_command_version", return_value="2.0.0")
    def test_outdated_none(self, _m1, _m2, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "outdated"])
        assert code == 0
        assert "up to date" in capsys.readouterr().out


class TestCmdUpdate:
    def test_update_no_tool_or_all(self, capsys, test_manifest_path):
        code = main(["--manifest", str(test_manifest_path), "--dry-run", "update"])
        assert code != 0


class TestCmdLogs:
    def test_logs_no_file(self, capsys):
        code = main(["logs"])
        assert code == 0
