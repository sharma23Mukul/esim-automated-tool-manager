"""Detect operating system, architecture, Linux distribution, and default package manager."""

from __future__ import annotations

import platform as _platform
import shutil
from dataclasses import dataclass
from typing import Optional

__all__ = ["PlatformInfo", "detect_platform"]


@dataclass(frozen=True)
class PlatformInfo:
    """Immutable snapshot of the current platform."""

    os_name: str  # "linux" | "windows" | "darwin"
    arch: str  # "x86_64" | "aarch64" | "arm64" | …
    distro: str  # "ubuntu" | "fedora" | "macos" | "windows" | …
    distro_version: str  # e.g. "22.04", "39", "14.0"

    @property
    def package_manager(self) -> Optional[str]:
        """Return the name of the preferred system package manager."""
        if self.os_name == "linux":
            apt_distros = {"ubuntu", "debian", "linuxmint", "pop", "elementary"}
            dnf_distros = {"fedora", "centos", "rhel", "rocky", "alma"}
            if self.distro in apt_distros:
                return "apt"
            if self.distro in dnf_distros:
                return "dnf"
            if self.distro in {"arch", "manjaro"}:
                return "pacman"
            # Fallback: probe for apt-get / dnf
            if shutil.which("apt-get"):
                return "apt"
            if shutil.which("dnf"):
                return "dnf"
        elif self.os_name == "darwin":
            if shutil.which("brew"):
                return "brew"
        elif self.os_name == "windows":
            if shutil.which("choco"):
                return "choco"
            if shutil.which("winget"):
                return "winget"
        return None

    @property
    def is_linux(self) -> bool:
        return self.os_name == "linux"

    @property
    def is_windows(self) -> bool:
        return self.os_name == "windows"

    @property
    def is_macos(self) -> bool:
        return self.os_name == "darwin"


def _parse_os_release() -> tuple:
    """Parse ``/etc/os-release`` for distro id and version."""
    try:
        with open("/etc/os-release") as fh:
            data: dict = {}
            for line in fh:
                line = line.strip()
                if "=" in line:
                    key, _, value = line.partition("=")
                    data[key] = value.strip('"').strip("'")
            return data.get("ID", "unknown"), data.get("VERSION_ID", "")
    except (FileNotFoundError, PermissionError):
        return "unknown", ""


def detect_platform() -> PlatformInfo:
    """Detect and return information about the current platform."""
    os_name = _platform.system().lower()
    arch = _platform.machine().lower()

    distro = ""
    distro_version = ""

    if os_name == "linux":
        distro, distro_version = _parse_os_release()
    elif os_name == "darwin":
        distro = "macos"
        mac_ver = _platform.mac_ver()[0]
        distro_version = mac_ver if mac_ver else ""
    elif os_name == "windows":
        distro = "windows"
        distro_version = _platform.version()
    else:
        distro = os_name
        distro_version = _platform.release()

    return PlatformInfo(
        os_name=os_name,
        arch=arch,
        distro=distro,
        distro_version=distro_version,
    )
