"""Homebrew package-manager backend (macOS)."""

from __future__ import annotations

from typing import Optional

from esim_toolmanager.backends.base import PackageBackend
from esim_toolmanager.utils.process import find_executable, run_command

__all__ = ["BrewBackend"]


class BrewBackend(PackageBackend):
    """Backend that wraps ``brew``."""

    @property
    def name(self) -> str:
        return "brew"

    def is_available(self) -> bool:
        return find_executable("brew") is not None

    def is_installed(self, package: str) -> bool:
        result = run_command(
            ["brew", "list", "--formula", package],
            check=False,
            dry_run=False,
        )
        if result is None:
            return False
        return result.returncode == 0

    def get_installed_version(self, package: str) -> Optional[str]:
        result = run_command(
            ["brew", "list", "--versions", package],
            check=False,
            dry_run=False,
        )
        if result and result.returncode == 0 and result.stdout:
            parts = result.stdout.strip().split()
            if len(parts) >= 2:
                return parts[-1]
        return None

    def install(self, package: str, version: Optional[str] = None) -> bool:
        cmd = ["brew", "install"]
        if version:
            cmd.append(f"{package}@{version}")
        else:
            cmd.append(package)
        result = run_command(cmd, dry_run=self.dry_run)
        return self.dry_run or (result is not None and result.returncode == 0)

    def update(self, package: str) -> bool:
        result = run_command(
            ["brew", "upgrade", package],
            dry_run=self.dry_run,
        )
        return self.dry_run or (result is not None and result.returncode == 0)

    def update_index(self) -> bool:
        result = run_command(["brew", "update"], dry_run=self.dry_run)
        return self.dry_run or (result is not None and result.returncode == 0)
