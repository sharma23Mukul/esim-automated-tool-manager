"""Tests for esim_toolmanager.core.registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from esim_toolmanager.core.registry import ToolRegistry


class TestToolRegistry:
    def test_load_default_manifest(self, registry):
        assert len(registry) > 0

    def test_get_tool_found(self, registry):
        tool = registry.get_tool("mock_tool")
        assert tool is not None
        assert tool.name == "MockTool"
        assert tool.required is True
        assert tool.category == "simulation"

    def test_get_tool_not_found(self, registry):
        assert registry.get_tool("nonexistent") is None

    def test_list_tools_all(self, registry):
        tools = registry.list_tools()
        assert len(tools) >= 2

    def test_list_tools_by_category(self, registry):
        tools = registry.list_tools(category="simulation")
        assert all(t.category == "simulation" for t in tools)

    def test_list_tools_required_only(self, registry):
        tools = registry.list_tools(required_only=True)
        assert all(t.required for t in tools)
        assert len(tools) >= 1

    def test_get_tools_for_platform_linux(self, registry):
        tools = registry.get_tools_for_platform("linux")
        ids = [t.id for t in tools]
        assert "mock_tool" in ids
        assert "optional_tool" in ids

    def test_get_tools_for_platform_windows(self, registry):
        tools = registry.get_tools_for_platform("windows")
        ids = [t.id for t in tools]
        assert "mock_tool" in ids
        assert "optional_tool" not in ids  # only on linux

    def test_get_esim_constraints(self, registry):
        constraints = registry.get_esim_constraints("2.5")
        assert "mock_tool" in constraints
        assert constraints["mock_tool"] == ">=1.0"

    def test_get_esim_constraints_unknown(self, registry):
        constraints = registry.get_esim_constraints("99.0")
        assert constraints == {}

    def test_contains(self, registry):
        assert "mock_tool" in registry
        assert "nonexistent" not in registry

    def test_tool_ids(self, registry):
        ids = registry.tool_ids
        assert isinstance(ids, list)
        assert "mock_tool" in ids

    def test_tool_definition_fields(self, registry):
        tool = registry.get_tool("mock_tool")
        assert tool.version_command == ["mocktool", "--version"]
        assert tool.packages.get("apt") == "mock-tool"
        assert "linux" in tool.platforms

    def test_load_invalid_manifest(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("not_a_list_or_dict")
        reg = ToolRegistry()
        with pytest.raises(ValueError):
            reg.load(bad)

    def test_load_missing_file(self):
        reg = ToolRegistry()
        with pytest.raises(FileNotFoundError):
            reg.load(Path("/nonexistent/path.yaml"))

    def test_merge_manifests(self, test_manifest_path, tmp_path):
        extra = tmp_path / "extra.yaml"
        extra.write_text(
            'schema_version: "1.0"\ntools:\n  extra_tool:\n    name: Extra\n'
            "    description: extra\n    category: other\n    required: false\n"
            "    version_command: [extra, --version]\n    version_pattern: '(\\\\d+)'\n"
            "    packages: {}\n    dependencies: []\n    config_hints: {}\n    platforms: [linux]\n"
        )
        reg = ToolRegistry()
        reg.load(test_manifest_path)
        count_before = len(reg)
        reg.load(extra)
        assert len(reg) == count_before + 1
        assert "extra_tool" in reg
