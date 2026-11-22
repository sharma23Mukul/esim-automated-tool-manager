"""pip package-manager backend (cross-platform, for Python libraries)."""

from __future__ import annotations

import sys
from typing import Optional

from esim_toolmanager.backends.base import PackageBackend
from esim_toolmanager.utils.process import run_command

__all__ = ["PipBackend"]


class PipBackend(PackageBackend):
    """Backend that wraps ``pip`` (via ``sys.executable -m pip``)."""

    @property
    def name(self) -> str:
        return "pip"

    def is_available(self) -> bool:
        result = run_command(
            [sys.executable, "-m", "pip", "--version"],
            check=False,
            dry_run=False,
        )
        return result is not None and result.returncode == 0

    def is_installed(self, package: str) -> bool:
        result = run_command(
            [sys.executable, "-m", "pip", "show", package],
            check=False,
            dry_run=False,
        )
        return result is not None and result.returncode == 0

    def get_installed_version(self, package: str) -> Optional[str]:
        result = run_command(
            [sys.executable, "-m", "pip", "show", package],
            check=False,
            dry_run=False,
        )
        if result and result.returncode == 0 and result.stdout:
            for line in result.stdout.splitlines():
                if line.lower().startswith("version:"):
                    return line.split(":", 1)[1].strip()
        return None

    def install(self, package: str, version: Optional[str] = None) -> bool:
        pkg = f"{package}=={version}" if version else package
        result = run_command(
            [sys.executable, "-m", "pip", "install", pkg],
            dry_run=self.dry_run,
        )
        return self.dry_run or (result is not None and result.returncode == 0)

    def update(self, package: str) -> bool:
        result = run_command(
            [sys.executable, "-m", "pip", "install", "--upgrade", package],
            dry_run=self.dry_run,
        )
        return self.dry_run or (result is not None and result.returncode == 0)
