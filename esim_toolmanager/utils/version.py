"""Semantic-version parsing, comparison, and constraint matching.

Supports versions like ``1.2.3``, ``42``, ``7.0.1-rc1`` and constraints
such as ``>=1.0``, ``==2.1``, ``~=1.5`` (compatible release), ``<3.0``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

__all__ = ["Version", "parse_version", "version_satisfies"]

_VERSION_RE = re.compile(
    r"(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[.\-](.+))?"
)


@dataclass(frozen=True)
class Version:
    """A comparable semantic version ``major.minor.patch[-pre]``."""

    major: int
    minor: int = 0
    patch: int = 0
    pre: str = ""

    # -- comparison (pre-release ordering is ignored for simplicity) ----------

    def _key(self) -> tuple:
        return (self.major, self.minor, self.patch)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() == other._key()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() < other._key()

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() <= other._key()

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() > other._key()

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() >= other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __str__(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            s += f"-{self.pre}"
        return s

    def __repr__(self) -> str:
        return f"Version('{self}')"


def parse_version(text: str) -> Optional[Version]:
    """Extract the first version-like string from *text*.

    Returns ``None`` when no version can be found.
    """
    if not text:
        return None
    m = _VERSION_RE.search(text.strip())
    if not m:
        return None
    return Version(
        major=int(m.group(1)),
        minor=int(m.group(2) or 0),
        patch=int(m.group(3) or 0),
        pre=m.group(4) or "",
    )


_CONSTRAINT_RE = re.compile(r"^\s*(>=|<=|==|!=|~=|>|<)\s*(.+)\s*$")


def version_satisfies(version: Version, constraint: str) -> bool:
    """Check whether *version* satisfies a PEP-440-style *constraint*.

    Supported operators: ``>=``, ``<=``, ``==``, ``!=``, ``>``, ``<``, ``~=``.

    ``~=X.Y`` means ``>= X.Y, < (X+1).0`` (compatible release).
    """
    m = _CONSTRAINT_RE.match(constraint)
    if not m:
        # Bare version string → treat as ``>=``
        target = parse_version(constraint)
        if target is None:
            return False
        return version >= target

    op, raw = m.group(1), m.group(2)
    target = parse_version(raw)
    if target is None:
        return False

    if op == ">=":
        return version >= target
    if op == "<=":
        return version <= target
    if op == "==":
        return version == target
    if op == "!=":
        return version != target
    if op == ">":
        return version > target
    if op == "<":
        return version < target
    if op == "~=":
        # Compatible release: >= target AND same major
        return version >= target and version.major == target.major
    return False
