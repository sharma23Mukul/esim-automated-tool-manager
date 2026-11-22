"""Tests for esim_toolmanager.core.dependency."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from esim_toolmanager.core.dependency import DependencyChecker, DependencyReport, ToolStatus


@pytest.fixture
def checker(registry, platform_linux):
    return DependencyChecker(registry, platform_linux)


class TestToolStatus:
    def test_ok_when_no_issues(self):
        s = ToolStatus("t", "T", True, True, "1.0", True, "1.0")
        assert s.ok is True

    def test_not_ok_when_issues(self):
        s = ToolStatus("t", "T", True, False, None, None, "1.0", issues=["missing"])
        assert s.ok is False


class TestDependencyReport:
    def test_all_ok(self):
        s1 = ToolStatus("a", "A", True, True, "1.0", True, "1.0")
        s2 = ToolStatus("b", "B", False, True, "2.0", True, "1.0")
        r = DependencyReport(statuses=[s1, s2])
        assert r.all_ok is True
        assert len(r.missing) == 0
        assert len(r.outdated) == 0

    def test_missing(self):
        s = ToolStatus("a", "A", True, False, None, None, "1.0", issues=["missing"])
        r = DependencyReport(statuses=[s])
        assert r.all_ok is False
        assert len(r.missing) == 1

    def test_outdated(self):
        s = ToolStatus("a", "A", True, True, "0.5", False, "1.0", issues=["old"])
        r = DependencyReport(statuses=[s])
        assert len(r.outdated) == 1

    def test_optional_missing(self):
        s = ToolStatus("a", "A", False, False, None, None, "1.0")
        r = DependencyReport(statuses=[s])
        assert len(r.optional_missing) == 1
        assert len(r.missing) == 0  # not required

    def test_summary(self):
        s = ToolStatus("a", "A", True, True, "1.0", True, "1.0")
        r = DependencyReport(statuses=[s])
        assert "1/1" in r.summary()


class TestDependencyChecker:
    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="2.0.0")
    def test_check_tool_installed_meets_min(self, _mock, checker, registry):
        tool = registry.get_tool("mock_tool")
        status = checker.check_tool(tool)
        assert status.is_installed is True
        assert status.meets_minimum is True
        assert status.ok is True

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="0.5.0")
    def test_check_tool_installed_below_min(self, _mock, checker, registry):
        tool = registry.get_tool("mock_tool")
        status = checker.check_tool(tool)
        assert status.is_installed is True
        assert status.meets_minimum is False
        assert status.ok is False
        assert any("below" in i for i in status.issues)

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value=None)
    def test_check_tool_missing_required(self, _mock, checker, registry):
        tool = registry.get_tool("mock_tool")
        status = checker.check_tool(tool)
        assert status.is_installed is False
        assert status.ok is False
        assert len(status.suggestions) > 0

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value=None)
    def test_check_tool_missing_optional(self, _mock, checker, registry):
        tool = registry.get_tool("optional_tool")
        status = checker.check_tool(tool)
        assert status.is_installed is False
        assert status.ok is True  # optional → no issues

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="1.0.0")
    def test_check_all(self, _mock, checker):
        report = checker.check_all()
        assert isinstance(report, DependencyReport)
        assert len(report.statuses) > 0

    def test_resolve_install_order_simple(self, checker):
        order = checker.resolve_install_order("mock_tool")
        assert order == ["mock_tool"]

    @patch("esim_toolmanager.core.dependency.get_command_version", return_value="1.0.0")
    def test_resolve_install_order_with_deps(self, _mock, checker):
        order = checker.resolve_install_order("optional_tool")
        assert order.index("mock_tool") < order.index("optional_tool")

    def test_resolve_install_order_circular(self, checker):
        with pytest.raises(ValueError, match="Circular"):
            checker.resolve_install_order("dep_cycle_a")
