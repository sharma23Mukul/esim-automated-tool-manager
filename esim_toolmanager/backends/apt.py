"""APT package-manager backend (Debian / Ubuntu)."""

from __future__ import annotations

from typing import Optional

from esim_toolmanager.backends.base import PackageBackend
from esim_toolmanager.utils.process import find_executable, run_command

__all__ = ["AptBackend"]


class AptBackend(PackageBackend):
    """Backend that wraps ``apt-get`` / ``dpkg``."""

    @property
    def name(self) -> str:
        return "apt"

    def is_available(self) -> bool:
        return find_executable("apt-get") is not None

    def is_installed(self, package: str) -> bool:
        result = run_command(
            ["dpkg", "-s", package],
            check=False,
            dry_run=False,
        )
        if result is None:
            return False
        return result.returncode == 0

    def get_installed_version(self, package: str) -> Optional[str]:
        result = run_command(
            ["dpkg-query", "-W", "-f", "${Version}", package],
            check=False,
            dry_run=False,
        )
        if result and result.returncode == 0 and result.stdout:
            return result.stdout.strip()
        return None

    def install(self, package: str, version: Optional[str] = None) -> bool:
        pkg = f"{package}={version}" if version else package
        result = run_command(
            ["sudo", "apt-get", "install", "-y", pkg],
            dry_run=self.dry_run,
        )
        return self.dry_run or (result is not None and result.returncode == 0)

    def update(self, package: str) -> bool:
        return self.install(package)

    def update_index(self) -> bool:
        result = run_command(
            ["sudo", "apt-get", "update", "-qq"],
            dry_run=self.dry_run,
        )
        return self.dry_run or (result is not None and result.returncode == 0)
