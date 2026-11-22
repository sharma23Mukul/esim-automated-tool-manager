"""Doctor – comprehensive health-check producing Markdown / JSON reports."""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from esim_toolmanager.core.config import ConfigManager
from esim_toolmanager.core.dependency import DependencyChecker
from esim_toolmanager.core.registry import ToolRegistry
from esim_toolmanager.platform.detect import PlatformInfo

__all__ = ["Doctor", "HealthReport"]

logger = logging.getLogger("esim_toolmanager.core.doctor")


@dataclass
class CheckItem:
    """Single check result inside a health report."""

    name: str
    status: str  # "ok" | "warning" | "error"
    message: str
    details: str = ""


@dataclass
class HealthReport:
    """Full health-check report."""

    timestamp: str = ""
    platform_info: Dict[str, str] = field(default_factory=dict)
    python_version: str = ""
    checks: List[CheckItem] = field(default_factory=list)
    dependency_summary: str = ""

    @property
    def ok(self) -> bool:
        return all(c.status != "error" for c in self.checks)

    # -- rendering ------------------------------------------------------------

    def to_markdown(self) -> str:
        """Render as Markdown suitable for bug-report attachments."""
        lines = [
            "# eSim Tool Manager – Health Report",
            "",
            f"**Generated:** {self.timestamp}",
            f"**Platform:** {self.platform_info.get('os_name', '?')} "
            f"{self.platform_info.get('arch', '?')} "
            f"({self.platform_info.get('distro', '?')} "
            f"{self.platform_info.get('distro_version', '?')})",
            f"**Python:** {self.python_version}",
            f"**Package Manager:** {self.platform_info.get('package_manager', 'N/A')}",
            "",
            "## Checks",
            "",
            "| Status | Check | Message |",
            "|--------|-------|---------|",
        ]
        status_icons = {"ok": "✅", "warning": "⚠️", "error": "❌"}
        for c in self.checks:
            icon = status_icons.get(c.status, "❓")
            lines.append(f"| {icon} | {c.name} | {c.message} |")

        lines.extend(["", "## Dependency Summary", "", self.dependency_summary])

        # Details section
        details = [c for c in self.checks if c.details]
        if details:
            lines.extend(["", "## Details", ""])
            for c in details:
                lines.append(f"### {c.name}")
                lines.append("")
                lines.append(c.details)
                lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "timestamp": self.timestamp,
            "platform": self.platform_info,
            "python_version": self.python_version,
            "all_ok": self.ok,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.checks
            ],
            "dependency_summary": self.dependency_summary,
        }

    def to_json(self) -> str:
        """Render as pretty-printed JSON."""
        return json.dumps(self.to_dict(), indent=2)


class Doctor:
    """Run a battery of health checks.

    Parameters
    ----------
    registry:
        Loaded tool registry.
    platform_info:
        Current platform information.
    config:
        Loaded configuration manager.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        platform_info: PlatformInfo,
        config: ConfigManager,
    ) -> None:
        self.registry = registry
        self.platform = platform_info
        self.config = config

    def run(self) -> HealthReport:
        """Execute all checks and return a ``HealthReport``."""
        report = HealthReport(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            platform_info={
                "os_name": self.platform.os_name,
                "arch": self.platform.arch,
                "distro": self.platform.distro,
                "distro_version": self.platform.distro_version,
                "package_manager": self.platform.package_manager or "none",
            },
            python_version=sys.version,
        )

        # 1. Package-manager availability
        report.checks.append(self._check_package_manager())

        # 2. Dependency check for each tool
        dep_checker = DependencyChecker(self.registry, self.platform)
        dep_report = dep_checker.check_all()
        report.dependency_summary = dep_report.summary()

        for status in dep_report.statuses:
            if status.ok:
                ver = status.installed_version or "N/A"
                report.checks.append(
                    CheckItem(
                        name=status.tool_name,
                        status="ok",
                        message=f"Installed ({ver})",
                    )
                )
            elif not status.is_installed:
                sev = "error" if status.required else "warning"
                suggestion_text = "; ".join(status.suggestions) if status.suggestions else ""
                report.checks.append(
                    CheckItem(
                        name=status.tool_name,
                        status=sev,
                        message="Not installed" + (" (required)" if status.required else " (optional)"),
                        details=suggestion_text,
                    )
                )
            else:
                report.checks.append(
                    CheckItem(
                        name=status.tool_name,
                        status="error" if status.required else "warning",
                        message="; ".join(status.issues),
                        details="; ".join(status.suggestions),
                    )
                )

        # 3. Config file check
        report.checks.append(self._check_config())

        return report

    # -- individual checks ----------------------------------------------------

    def _check_package_manager(self) -> CheckItem:
        pm = self.platform.package_manager
        if pm:
            return CheckItem(
                name="Package Manager",
                status="ok",
                message=f"Detected: {pm}",
            )
        return CheckItem(
            name="Package Manager",
            status="warning",
            message="No supported package manager detected.",
            details="Install apt, brew, choco, or winget for automatic tool management.",
        )

    def _check_config(self) -> CheckItem:
        if self.config.config_path.exists():
            return CheckItem(
                name="Configuration",
                status="ok",
                message=f"Loaded from {self.config.config_path}",
            )
        return CheckItem(
            name="Configuration",
            status="ok",
            message="Using defaults (no config file yet).",
        )
