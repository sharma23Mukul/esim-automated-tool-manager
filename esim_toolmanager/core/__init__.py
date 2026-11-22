"""Core logic: registry, installer, updater, config, dependency checker, doctor."""

from esim_toolmanager.core.config import ConfigManager
from esim_toolmanager.core.dependency import DependencyChecker, ToolStatus
from esim_toolmanager.core.doctor import Doctor, HealthReport
from esim_toolmanager.core.installer import InstallResult, ToolInstaller
from esim_toolmanager.core.registry import ToolDefinition, ToolRegistry
from esim_toolmanager.core.updater import ToolUpdater, UpdateInfo

__all__ = [
    "ToolDefinition",
    "ToolRegistry",
    "ToolInstaller",
    "InstallResult",
    "ToolUpdater",
    "UpdateInfo",
    "ConfigManager",
    "DependencyChecker",
    "ToolStatus",
    "Doctor",
    "HealthReport",
]
