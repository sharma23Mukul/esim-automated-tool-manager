"""Dependency checker – validates that every tool and its deps are present and compatible."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from esim_toolmanager.core.registry import ToolDefinition, ToolRegistry
from esim_toolmanager.platform.detect import PlatformInfo
from esim_toolmanager.utils.process import find_executable, get_command_version
from esim_toolmanager.utils.version import parse_version, version_satisfies

__all__ = ["DependencyChecker", "ToolStatus", "DependencyReport"]

logger = logging.getLogger("esim_toolmanager.core.dependency")


@dataclass
class ToolStatus:
    """Runtime status of a single tool."""

    tool_id: str
    tool_name: str
    required: bool
    is_installed: bool
    installed_version: Optional[str]
    meets_minimum: Optional[bool]  # None when min_version is unset
    min_version: Optional[str]
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """``True`` when this tool has no issues."""
        return len(self.issues) == 0


@dataclass
class DependencyReport:
    """Aggregated result of a full dependency check."""

    statuses: List[ToolStatus] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        return all(s.ok for s in self.statuses)

    @property
    def missing(self) -> List[ToolStatus]:
        return [s for s in self.statuses if not s.is_installed and s.required]

    @property
    def outdated(self) -> List[ToolStatus]:
        return [s for s in self.statuses if s.meets_minimum is False]

    @property
    def optional_missing(self) -> List[ToolStatus]:
        return [s for s in self.statuses if not s.is_installed and not s.required]

    def summary(self) -> str:
        """Human-readable one-line summary."""
        total = len(self.statuses)
        ok = sum(1 for s in self.statuses if s.ok)
        return f"{ok}/{total} tools OK, {len(self.missing)} missing, {len(self.outdated)} outdated."


class DependencyChecker:
    """Check that all required tools are installed and compatible.

    Parameters
    ----------
    registry:
        Loaded tool registry.
    platform_info:
        Current platform information.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        platform_info: PlatformInfo,
    ) -> None:
        self.registry = registry
        self.platform = platform_info

    def check_tool(
        self, tool: ToolDefinition, _seen: Optional[set] = None
    ) -> ToolStatus:
        """Check installation and version of a single *tool*."""
        if _seen is None:
            _seen = set()
        issues: List[str] = []
        suggestions: List[str] = []

        # Detect installation via version command
        installed_ver_str = None
        is_installed = False

        if tool.version_command:
            installed_ver_str = get_command_version(
                tool.version_command, tool.version_pattern
            )
            is_installed = installed_ver_str is not None
        else:
            # Fallback: check if the first token is on PATH
            if tool.version_command:
                is_installed = find_executable(tool.version_command[0]) is not None

        if not is_installed:
            msg = f"{tool.name} is not installed."
            if tool.required:
                issues.append(msg)
                pm = self.platform.package_manager
                pkg = tool.packages.get(pm or "") if pm else None
                if pm and pkg:
                    suggestions.append(f"Install with: esim-tm install {tool.id}")
                    suggestions.append(f"  or manually: {pm} install {pkg}")
                else:
                    suggestions.append(f"Visit {tool.homepage} for installation instructions.")
            else:
                # Optional tools are not flagged as issues
                pass

            return ToolStatus(
                tool_id=tool.id,
                tool_name=tool.name,
                required=tool.required,
                is_installed=False,
                installed_version=None,
                meets_minimum=None,
                min_version=tool.min_version,
                issues=issues,
                suggestions=suggestions,
            )

        # Version check
        meets_min: Optional[bool] = None
        if tool.min_version and installed_ver_str:
            installed = parse_version(installed_ver_str)
            if installed:
                meets_min = version_satisfies(installed, f">={tool.min_version}")
                if not meets_min:
                    issues.append(
                        f"{tool.name} version {installed_ver_str} is below "
                        f"minimum {tool.min_version}."
                    )
                    suggestions.append(f"Update with: esim-tm update {tool.id}")

        # Check max version
        if tool.max_version and installed_ver_str:
            installed = parse_version(installed_ver_str)
            if installed and not version_satisfies(installed, f"<={tool.max_version}"):
                issues.append(
                    f"{tool.name} version {installed_ver_str} exceeds "
                    f"maximum {tool.max_version}."
                )

        # Check dependencies (recursive, with cycle guard)
        _seen.add(tool.id)
        for dep_id in tool.dependencies:
            if dep_id in _seen:
                issues.append(f"Circular dependency: {tool.id} ↔ {dep_id}")
                continue
            dep_tool = self.registry.get_tool(dep_id)
            if dep_tool:
                dep_status = self.check_tool(dep_tool, _seen)
                if not dep_status.ok:
                    issues.append(
                        f"Dependency '{dep_tool.name}' has issues: "
                        + "; ".join(dep_status.issues)
                    )

        return ToolStatus(
            tool_id=tool.id,
            tool_name=tool.name,
            required=tool.required,
            is_installed=True,
            installed_version=installed_ver_str,
            meets_minimum=meets_min,
            min_version=tool.min_version,
            issues=issues,
            suggestions=suggestions,
        )

    def check_all(self) -> DependencyReport:
        """Run dependency checks for all tools on this platform."""
        report = DependencyReport()
        for tool in self.registry.get_tools_for_platform(self.platform.os_name):
            report.statuses.append(self.check_tool(tool))
        return report

    def resolve_install_order(self, tool_id: str) -> List[str]:
        """Return tool_ids in topological (dependency-first) install order.

        Raises ``ValueError`` on circular dependencies.
        """
        visited: Dict[str, bool] = {}  # True = fully processed
        order: List[str] = []

        def _visit(tid: str) -> None:
            if tid in visited:
                if not visited[tid]:
                    raise ValueError(f"Circular dependency detected involving '{tid}'.")
                return
            visited[tid] = False
            tool = self.registry.get_tool(tid)
            if tool:
                for dep in tool.dependencies:
                    _visit(dep)
            visited[tid] = True
            order.append(tid)

        _visit(tool_id)
        return order
