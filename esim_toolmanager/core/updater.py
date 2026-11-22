"""Update checker and updater – detects outdated tools and applies upgrades."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from esim_toolmanager.backends import get_backend
from esim_toolmanager.core.registry import ToolDefinition, ToolRegistry
from esim_toolmanager.platform.detect import PlatformInfo
from esim_toolmanager.utils.process import get_command_version
from esim_toolmanager.utils.version import parse_version, version_satisfies

__all__ = ["ToolUpdater", "UpdateInfo"]

logger = logging.getLogger("esim_toolmanager.core.updater")


@dataclass
class UpdateInfo:
    """Status of a single tool regarding updates."""

    tool_id: str
    tool_name: str
    installed_version: Optional[str]
    min_version: Optional[str]
    is_installed: bool
    is_outdated: bool
    message: str


@dataclass
class UpdateResult:
    """Outcome of an update attempt."""

    tool_id: str
    success: bool
    message: str
    dry_run: bool = False


class ToolUpdater:
    """Check for outdated tools and apply updates.

    Parameters
    ----------
    registry:
        Loaded tool registry.
    platform_info:
        Current platform information.
    dry_run:
        If ``True`` no actual changes are made.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        platform_info: PlatformInfo,
        *,
        dry_run: bool = False,
    ) -> None:
        self.registry = registry
        self.platform = platform_info
        self.dry_run = dry_run

    # -- queries --------------------------------------------------------------

    def check_tool(self, tool: ToolDefinition) -> UpdateInfo:
        """Return update information for a single *tool*."""
        installed_ver_str = get_command_version(
            tool.version_command, tool.version_pattern
        )
        is_installed = installed_ver_str is not None

        is_outdated = False
        message = ""

        if not is_installed:
            message = f"{tool.name} is not installed."
        elif tool.min_version:
            installed = parse_version(installed_ver_str)  # type: ignore[arg-type]
            if installed and not version_satisfies(installed, f">={tool.min_version}"):
                is_outdated = True
                message = (
                    f"{tool.name} {installed_ver_str} is below the "
                    f"minimum required version {tool.min_version}."
                )
            else:
                message = f"{tool.name} {installed_ver_str} is up to date."
        else:
            message = f"{tool.name} {installed_ver_str} is installed."

        return UpdateInfo(
            tool_id=tool.id,
            tool_name=tool.name,
            installed_version=installed_ver_str,
            min_version=tool.min_version,
            is_installed=is_installed,
            is_outdated=is_outdated,
            message=message,
        )

    def check_all(self) -> List[UpdateInfo]:
        """Return update information for all tools on this platform."""
        results = []
        for tool in self.registry.get_tools_for_platform(self.platform.os_name):
            results.append(self.check_tool(tool))
        return results

    def get_outdated(self) -> List[UpdateInfo]:
        """Return only tools that are outdated."""
        return [info for info in self.check_all() if info.is_outdated]

    # -- mutating operations --------------------------------------------------

    def update_tool(self, tool_id: str) -> UpdateResult:
        """Update a single tool to the latest version."""
        tool = self.registry.get_tool(tool_id)
        if tool is None:
            return UpdateResult(
                tool_id=tool_id,
                success=False,
                message=f"Tool '{tool_id}' not found in manifest.",
            )

        pm = self.platform.package_manager
        pkg_name = tool.packages.get(pm or "") if pm else None
        if not pm or not pkg_name:
            return UpdateResult(
                tool_id=tool_id,
                success=False,
                message=(
                    f"No package-manager backend available for '{tool.name}' "
                    f"on this platform."
                ),
            )

        try:
            backend = get_backend(pm, dry_run=self.dry_run)
        except KeyError:
            return UpdateResult(
                tool_id=tool_id,
                success=False,
                message=f"Backend '{pm}' is not implemented.",
            )

        logger.info(
            "%sUpdating %s via %s…",
            "[DRY RUN] " if self.dry_run else "",
            tool.name,
            pm,
        )

        try:
            ok = backend.update(pkg_name)
        except Exception as exc:
            return UpdateResult(
                tool_id=tool_id,
                success=False,
                message=f"Update failed: {exc}",
                dry_run=self.dry_run,
            )

        action = "Would update" if self.dry_run else "Updated"
        return UpdateResult(
            tool_id=tool_id,
            success=ok,
            message=f"{action} {tool.name} via {pm}.",
            dry_run=self.dry_run,
        )

    def update_all(self) -> List[UpdateResult]:
        """Update every outdated tool on this platform."""
        results = []
        for info in self.get_outdated():
            results.append(self.update_tool(info.tool_id))
        return results
