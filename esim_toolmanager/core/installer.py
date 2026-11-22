"""Tool installer – orchestrates downloading and installing tools via backends."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from esim_toolmanager.backends import get_backend
from esim_toolmanager.core.registry import ToolDefinition, ToolRegistry
from esim_toolmanager.platform.detect import PlatformInfo

__all__ = ["ToolInstaller", "InstallResult"]

logger = logging.getLogger("esim_toolmanager.core.installer")


@dataclass
class InstallResult:
    """Outcome of an install attempt."""

    tool_id: str
    success: bool
    message: str
    dry_run: bool = False
    backend_used: str = ""
    version_installed: Optional[str] = None


class ToolInstaller:
    """Install tools using the appropriate package-manager backend.

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

    def install(
        self,
        tool_id: str,
        version: Optional[str] = None,
    ) -> InstallResult:
        """Install a single tool.

        Parameters
        ----------
        tool_id:
            Identifier from the manifest (e.g. ``"ngspice"``).
        version:
            Explicit version to install.  Defaults to the manifest's
            ``pinned_version`` or latest.
        """
        tool = self.registry.get_tool(tool_id)
        if tool is None:
            return InstallResult(
                tool_id=tool_id,
                success=False,
                message=f"Tool '{tool_id}' not found in manifest.",
            )

        # Platform check
        if self.platform.os_name not in tool.platforms:
            return InstallResult(
                tool_id=tool_id,
                success=False,
                message=(
                    f"Tool '{tool.name}' is not supported on "
                    f"{self.platform.os_name}."
                ),
            )

        # Resolve version
        target_version = version or tool.pinned_version
        if target_version:
            logger.info("Installing %s version %s", tool.name, target_version)
        else:
            logger.info("Installing %s (latest)", tool.name)

        # Select backend
        backend_name = self._select_backend(tool)
        if backend_name is None:
            return InstallResult(
                tool_id=tool_id,
                success=False,
                message=(
                    f"No package-manager backend available for '{tool.name}' "
                    f"on {self.platform.os_name}/{self.platform.distro}."
                ),
            )

        try:
            backend = get_backend(backend_name, dry_run=self.dry_run)
        except KeyError:
            return InstallResult(
                tool_id=tool_id,
                success=False,
                message=f"Backend '{backend_name}' is not implemented.",
            )

        pkg = tool.packages.get(backend_name)
        if not pkg:
            return InstallResult(
                tool_id=tool_id,
                success=False,
                message=(
                    f"No package name for '{tool.name}' "
                    f"in backend '{backend_name}'."
                ),
            )

        # Perform installation
        logger.info(
            "%sInstalling %s via %s…",
            "[DRY RUN] " if self.dry_run else "",
            pkg,
            backend_name,
        )
        try:
            ok = backend.install(pkg, target_version)
        except Exception as exc:
            logger.error("Installation failed: %s", exc)
            return InstallResult(
                tool_id=tool_id,
                success=False,
                message=f"Installation failed: {exc}",
                backend_used=backend_name,
            )

        action = "Would install" if self.dry_run else "Installed"
        return InstallResult(
            tool_id=tool_id,
            success=ok,
            message=f"{action} {tool.name} via {backend_name}.",
            dry_run=self.dry_run,
            backend_used=backend_name,
            version_installed=target_version,
        )

    def install_all_required(self) -> list:
        """Install every tool marked ``required: true`` for this platform."""
        results = []
        for tool in self.registry.get_tools_for_platform(self.platform.os_name):
            if tool.required:
                results.append(self.install(tool.id))
        return results

    # -- helpers --------------------------------------------------------------

    def _select_backend(self, tool: ToolDefinition) -> Optional[str]:
        """Pick the best backend for *tool* on the current platform."""
        # Prefer the platform's default package manager
        pm = self.platform.package_manager
        if pm and tool.packages.get(pm):
            return pm
        # Fallback: try each backend that has a package entry
        for backend_name, pkg in tool.packages.items():
            if pkg:
                try:
                    b = get_backend(backend_name, dry_run=True)
                    if b.is_available():
                        return backend_name
                except KeyError:
                    continue
        return None
