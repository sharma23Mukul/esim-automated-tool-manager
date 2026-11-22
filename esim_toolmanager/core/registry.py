"""Tool registry – loads and queries tool definitions from a YAML manifest."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

__all__ = ["ToolDefinition", "ToolRegistry"]

logger = logging.getLogger("esim_toolmanager.core.registry")

# Default manifest ships with the package.
_DEFAULT_MANIFEST = Path(__file__).resolve().parent.parent / "data" / "tools.yaml"


@dataclass
class ToolDefinition:
    """Everything the manager needs to know about a single external tool."""

    id: str
    name: str
    description: str
    category: str
    required: bool
    version_command: List[str]
    version_pattern: str
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    pinned_version: Optional[str] = None
    packages: Dict[str, Optional[str]] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    config_hints: Dict[str, Any] = field(default_factory=dict)
    platforms: List[str] = field(default_factory=list)
    homepage: str = ""


class ToolRegistry:
    """Load, merge and query tool definitions.

    Usage::

        reg = ToolRegistry()
        reg.load()                           # loads the built-in manifest
        reg.load(Path("custom_tools.yaml"))  # merges additional definitions
        tool = reg.get_tool("ngspice")
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._esim_versions: Dict[str, Any] = {}
        self._schema_version: str = ""

    # -- loading --------------------------------------------------------------

    def load(self, manifest_path: Optional[Path] = None) -> None:
        """Load (or merge) tool definitions from a YAML manifest.

        If *manifest_path* is ``None`` the built-in ``data/tools.yaml`` is
        used.
        """
        path = manifest_path or _DEFAULT_MANIFEST
        logger.debug("Loading manifest: %s", path)

        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid manifest format in {path}")

        self._schema_version = data.get("schema_version", "1.0")
        self._esim_versions.update(data.get("esim_versions", {}))

        for tool_id, raw in data.get("tools", {}).items():
            td = ToolDefinition(
                id=tool_id,
                name=raw.get("name", tool_id),
                description=raw.get("description", ""),
                category=raw.get("category", "other"),
                required=raw.get("required", False),
                version_command=raw.get("version_command", []),
                version_pattern=raw.get("version_pattern", ""),
                min_version=raw.get("min_version"),
                max_version=raw.get("max_version"),
                pinned_version=raw.get("pinned_version"),
                packages=raw.get("packages", {}),
                dependencies=raw.get("dependencies", []),
                config_hints=raw.get("config_hints", {}),
                platforms=raw.get("platforms", []),
                homepage=raw.get("homepage", ""),
            )
            self._tools[tool_id] = td
            logger.debug("Registered tool: %s (%s)", td.name, tool_id)

    # -- queries --------------------------------------------------------------

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """Return the definition for *tool_id*, or ``None``."""
        return self._tools.get(tool_id)

    def list_tools(
        self,
        *,
        category: Optional[str] = None,
        required_only: bool = False,
    ) -> List[ToolDefinition]:
        """Return tool definitions, optionally filtered."""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        if required_only:
            tools = [t for t in tools if t.required]
        return tools

    def get_tools_for_platform(self, os_name: str) -> List[ToolDefinition]:
        """Return tools that support the given OS (``linux`` / ``windows`` / ``darwin``)."""
        return [t for t in self._tools.values() if os_name in t.platforms]

    def get_esim_constraints(self, esim_version: str) -> Dict[str, str]:
        """Return ``{tool_id: constraint}`` for a given eSim release."""
        entry = self._esim_versions.get(esim_version, {})
        return entry.get("tool_constraints", {})

    @property
    def tool_ids(self) -> List[str]:
        """All registered tool ids."""
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, tool_id: str) -> bool:
        return tool_id in self._tools
