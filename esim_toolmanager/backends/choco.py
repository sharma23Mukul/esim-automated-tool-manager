"""Chocolatey package-manager backend (Windows)."""

from __future__ import annotations

from typing import Optional

from esim_toolmanager.backends.base import PackageBackend
from esim_toolmanager.utils.process import find_executable, run_command

__all__ = ["ChocoBackend"]


class ChocoBackend(PackageBackend):
    """Backend that wraps ``choco``."""

    @property
    def name(self) -> str:
        return "choco"

    def is_available(self) -> bool:
        return find_executable("choco") is not None

    def is_installed(self, package: str) -> bool:
        result = run_command(
            ["choco", "list", "--local-only", "--exact", package],
            check=False,
            dry_run=False,
        )
        if result is None:
            return False
        # Chocolatey prints "X packages installed." on the last line.
        return result.returncode == 0 and package.lower() in result.stdout.lower()

    def get_installed_version(self, package: str) -> Optional[str]:
        result = run_command(
            ["choco", "list", "--local-only", "--exact", package],
            check=False,
            dry_run=False,
        )
        if result and result.returncode == 0 and result.stdout:
            for line in result.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[0].lower() == package.lower():
                    return parts[1]
        return None

    def install(self, package: str, version: Optional[str] = None) -> bool:
        cmd = ["choco", "install", package, "-y", "--no-progress"]
        if version:
            cmd.extend(["--version", version])
        result = run_command(cmd, dry_run=self.dry_run)
        return self.dry_run or (result is not None and result.returncode == 0)

    def update(self, package: str) -> bool:
        result = run_command(
            ["choco", "upgrade", package, "-y", "--no-progress"],
            dry_run=self.dry_run,
        )
        return self.dry_run or (result is not None and result.returncode == 0)
