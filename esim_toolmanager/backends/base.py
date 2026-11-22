"""Abstract base class for all package-manager backends."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

__all__ = ["PackageBackend"]


class PackageBackend(ABC):
    """Interface that every package-manager backend must implement.

    All mutating methods honour ``self.dry_run``; when it is ``True`` the
    backend must log what *would* happen and return ``True`` without touching
    the system.
    """

    def __init__(self, *, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self.logger = logging.getLogger(f"esim_toolmanager.backends.{self.name}")

    # -- identity -------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Short lowercase identifier, e.g. ``apt``, ``brew``."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return ``True`` if this backend's package manager is installed."""

    # -- queries --------------------------------------------------------------

    @abstractmethod
    def is_installed(self, package: str) -> bool:
        """Check if *package* is currently installed."""

    @abstractmethod
    def get_installed_version(self, package: str) -> Optional[str]:
        """Return the installed version string, or ``None``."""

    # -- mutating operations --------------------------------------------------

    @abstractmethod
    def install(self, package: str, version: Optional[str] = None) -> bool:
        """Install *package*, optionally pinning to *version*."""

    @abstractmethod
    def update(self, package: str) -> bool:
        """Update *package* to the latest available version."""

    def update_index(self) -> bool:
        """Refresh the package index (e.g. ``apt-get update``).

        Default implementation is a no-op returning ``True``.
        """
        return True

    # -- string representation ------------------------------------------------

    def __repr__(self) -> str:
        return f"{type(self).__name__}(dry_run={self.dry_run})"
