"""Package-manager backend implementations."""

from esim_toolmanager.backends.apt import AptBackend
from esim_toolmanager.backends.base import PackageBackend
from esim_toolmanager.backends.brew import BrewBackend
from esim_toolmanager.backends.choco import ChocoBackend
from esim_toolmanager.backends.pip_backend import PipBackend

__all__ = [
    "PackageBackend",
    "AptBackend",
    "BrewBackend",
    "ChocoBackend",
    "PipBackend",
    "get_backend",
]

_BACKENDS = {
    "apt": AptBackend,
    "brew": BrewBackend,
    "choco": ChocoBackend,
    "pip": PipBackend,
}


def get_backend(name: str, *, dry_run: bool = False) -> PackageBackend:
    """Return a backend instance by *name*.

    Raises ``KeyError`` if the backend is unknown.
    """
    cls = _BACKENDS[name]
    return cls(dry_run=dry_run)
