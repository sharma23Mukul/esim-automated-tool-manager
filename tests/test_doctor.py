"""Tests for esim_toolmanager.core.doctor."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from esim_toolmanager.core.config import ConfigManager
from esim_toolmanager.core.doctor import CheckItem, Doctor, HealthReport


@pytest.fixture
def doctor(registry, platform_linux, tmp_path):
    cfg = ConfigManager(config_path=tmp_path / "cfg.yaml")
    return Doctor(registry, platform_linux, cfg)


class TestCheckItem:
    def test_creation(self):
        c = CheckItem(name="Test", status="ok", message="All good")
        assert c.name == "Test"
        assert c.status == "ok"


class TestHealthReport:
    def test_ok_all_pass(self):
        r = HealthReport(checks=[CheckItem("A", "ok", "good")])
        assert r.ok is True

    def test_not_ok_on_error(self):
        r = HealthReport(checks=[CheckItem("A", "error", "bad")])
        assert r.ok is False

    def test_ok_with_warnings(self):
        r = HealthReport(checks=[CheckItem("A", "warning", "warn")])
        assert r.ok is True

    def test_to_markdown(self):
        r = HealthReport(
            timestamp="2026-01-01T00:00:00",
            platform_info={"os_name": "linux", "arch": "x86_64",
                           "distro": "ubuntu", "distro_version": "22.04",
                           "package_manager": "apt"},
            python_version="3.12.0",
            checks=[CheckItem("Tool", "ok", "installed")],
            dependency_summary="1/1 OK",
        )
        md = r.to_markdown()
        assert "# eSim Tool Manager" in md
        assert "✅" in md
        assert "linux" in md

    def test_to_json_valid(self):
        r = HealthReport(
            timestamp="2026-01-01",
            checks=[CheckItem("T", "ok", "m")],
        )
        data = json.loads(r.to_json())
        assert data["all_ok"] is True
        assert len(data["checks"]) == 1

    def test_to_dict(self):
        r = HealthReport(checks=[])
        d = r.to_dict()
        assert "checks" in d
        assert "all_ok" in d


class TestDoctor:
    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="2.0.0")
    def test_run_produces_report(self, _mock, doctor):
        report = doctor.run()
        assert isinstance(report, HealthReport)
        assert report.timestamp != ""
        assert len(report.checks) > 0
        assert report.python_version != ""

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="2.0.0")
    def test_run_has_package_manager_check(self, _mock, doctor):
        report = doctor.run()
        names = [c.name for c in report.checks]
        assert "Package Manager" in names

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="2.0.0")
    def test_run_has_config_check(self, _mock, doctor):
        report = doctor.run()
        names = [c.name for c in report.checks]
        assert "Configuration" in names

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value=None)
    def test_run_missing_tools_reported(self, _mock, doctor):
        report = doctor.run()
        statuses = [c.status for c in report.checks]
        assert "error" in statuses  # mock_tool is required

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="2.0.0")
    def test_markdown_has_details_section(self, _mock, doctor):
        """When all tools are OK there are no detail entries."""
        report = doctor.run()
        md = report.to_markdown()
        assert "## Checks" in md
