"""Command-line interface for eSim Tool Manager.

Entry point: ``esim-tm`` (installed via ``pip install .``).
Also callable as ``python -m esim_toolmanager``.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

from esim_toolmanager import (
    EXIT_DEPENDENCY_MISSING,
    EXIT_ERROR,
    EXIT_INSTALL_FAILED,
    EXIT_OK,
    EXIT_TOOL_NOT_FOUND,
    EXIT_VERSION_MISMATCH,
    __version__,
)
from esim_toolmanager.core.config import ConfigManager
from esim_toolmanager.core.dependency import DependencyChecker
from esim_toolmanager.core.doctor import Doctor
from esim_toolmanager.core.installer import ToolInstaller
from esim_toolmanager.core.registry import ToolRegistry
from esim_toolmanager.core.updater import ToolUpdater
from esim_toolmanager.platform.detect import detect_platform
from esim_toolmanager.utils.log import setup_logging
from esim_toolmanager.utils.process import get_command_version
from esim_toolmanager.utils.version import parse_version

logger = logging.getLogger("esim_toolmanager.cli")

# Default log directory
_LOG_DIR = Path.home() / ".esim-toolmanager" / "logs"


# ── arg-parser ───────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="esim-tm",
        description="eSim Tool Manager – manage external EDA tools and dependencies.",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate actions without modifying the system.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug-level output.",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit machine-readable JSON output.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config file (default: ~/.esim-toolmanager/config.yaml).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to tool manifest (default: built-in tools.yaml).",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # list
    p_list = sub.add_parser("list", help="Show all tools with status.")
    p_list.add_argument("--category", help="Filter by category.")
    p_list.add_argument("--required", action="store_true", help="Show only required tools.")

    # check
    sub.add_parser("check", help="Run a dependency and compatibility check.")

    # install
    p_install = sub.add_parser("install", help="Install a tool.")
    p_install.add_argument("tool", nargs="?", help="Tool id (or --all).")
    p_install.add_argument("--all", dest="install_all", action="store_true", help="Install all required tools.")
    p_install.add_argument("--version", dest="tool_version", help="Specific version to install.")

    # update
    p_update = sub.add_parser("update", help="Update tool(s).")
    p_update.add_argument("tool", nargs="?", help="Tool id (or --all).")
    p_update.add_argument("--all", dest="update_all", action="store_true", help="Update all outdated tools.")

    # outdated
    sub.add_parser("outdated", help="List tools that are below the minimum version.")

    # configure
    p_conf = sub.add_parser("configure", help="Configure env vars / paths for tools.")
    p_conf.add_argument("tool", nargs="?", help="Tool id to configure (or omit for all).")
    p_conf.add_argument("--shell", default="bash", choices=["bash", "zsh", "fish", "powershell", "cmd"],
                        help="Shell for env-script output.")
    p_conf.add_argument("--export", action="store_true", help="Print export script to stdout.")

    # doctor
    p_doctor = sub.add_parser("doctor", help="Run a full health check.")
    p_doctor.add_argument("--format", dest="report_format", default="markdown",
                          choices=["markdown", "json"], help="Report output format.")

    # logs
    p_logs = sub.add_parser("logs", help="Show recent log entries.")
    p_logs.add_argument("-n", "--lines", type=int, default=50, help="Number of lines to show.")

    return parser


# ── command handlers ─────────────────────────────────────────────────────────


def _init_core(args: argparse.Namespace):
    """Bootstrap registry, platform info, and config from parsed args."""
    platform_info = detect_platform()
    registry = ToolRegistry()
    registry.load(args.manifest)

    config = ConfigManager(config_path=args.config, dry_run=args.dry_run)
    config.load()

    return registry, platform_info, config


def cmd_list(args: argparse.Namespace) -> int:
    registry, platform_info, _ = _init_core(args)
    tools = registry.get_tools_for_platform(platform_info.os_name)

    if args.category:
        tools = [t for t in tools if t.category == args.category]
    if args.required:
        tools = [t for t in tools if t.required]

    rows = []
    for tool in tools:
        ver_str = get_command_version(tool.version_command, tool.version_pattern)
        installed = ver_str is not None
        status = "installed" if installed else "missing"

        # Version check
        if installed and tool.min_version and ver_str:
            v = parse_version(ver_str)
            from esim_toolmanager.utils.version import version_satisfies
            if v and not version_satisfies(v, f">={tool.min_version}"):
                status = "outdated"

        rows.append({
            "id": tool.id,
            "name": tool.name,
            "category": tool.category,
            "required": tool.required,
            "installed_version": ver_str or "—",
            "min_version": tool.min_version or "—",
            "status": status,
        })

    if args.json_output:
        print(json.dumps(rows, indent=2))
    else:
        # Pretty table
        header = f"{'Tool':<16} {'Version':<12} {'Required':<10} {'Min':<10} {'Status':<10}"
        print(header)
        print("─" * len(header))
        for r in rows:
            req = "yes" if r["required"] else "no"
            icon = {"installed": "✅", "outdated": "⚠️", "missing": "❌"}.get(r["status"], "?")
            print(
                f"{r['name']:<16} {r['installed_version']:<12} "
                f"{req:<10} {r['min_version']:<10} {icon} {r['status']}"
            )
        print(f"\n{len(rows)} tools shown.")

    return EXIT_OK


def cmd_check(args: argparse.Namespace) -> int:
    registry, platform_info, _ = _init_core(args)
    checker = DependencyChecker(registry, platform_info)
    report = checker.check_all()

    if args.json_output:
        data = []
        for s in report.statuses:
            data.append({
                "tool_id": s.tool_id,
                "name": s.tool_name,
                "installed": s.is_installed,
                "version": s.installed_version,
                "ok": s.ok,
                "issues": s.issues,
                "suggestions": s.suggestions,
            })
        print(json.dumps({"summary": report.summary(), "tools": data}, indent=2))
    else:
        print("Dependency Check Report")
        print("═" * 40)
        for s in report.statuses:
            icon = "✅" if s.ok else ("❌" if s.required else "⚠️")
            ver = s.installed_version or "not installed"
            print(f"  {icon} {s.tool_name}: {ver}")
            for issue in s.issues:
                print(f"      ✗ {issue}")
            for sug in s.suggestions:
                print(f"      → {sug}")
        print()
        print(report.summary())

    if report.missing:
        return EXIT_DEPENDENCY_MISSING
    if report.outdated:
        return EXIT_VERSION_MISMATCH
    return EXIT_OK


def cmd_install(args: argparse.Namespace) -> int:
    if not args.tool and not args.install_all:
        print("Error: specify a tool id or use --all.", file=sys.stderr)
        return EXIT_ERROR

    registry, platform_info, _ = _init_core(args)
    installer = ToolInstaller(registry, platform_info, dry_run=args.dry_run)

    if args.install_all:
        results = installer.install_all_required()
    else:
        results = [installer.install(args.tool, version=args.tool_version)]

    exit_code = EXIT_OK
    for r in results:
        icon = "✅" if r.success else "❌"
        if args.json_output:
            print(json.dumps({
                "tool": r.tool_id, "success": r.success,
                "message": r.message, "dry_run": r.dry_run,
            }))
        else:
            print(f"  {icon} {r.message}")
        if not r.success:
            exit_code = EXIT_INSTALL_FAILED

    return exit_code


def cmd_update(args: argparse.Namespace) -> int:
    if not args.tool and not args.update_all:
        print("Error: specify a tool id or use --all.", file=sys.stderr)
        return EXIT_ERROR

    registry, platform_info, _ = _init_core(args)
    updater = ToolUpdater(registry, platform_info, dry_run=args.dry_run)

    results = updater.update_all() if args.update_all else [updater.update_tool(args.tool)]

    exit_code = EXIT_OK
    for r in results:
        icon = "✅" if r.success else "❌"
        if args.json_output:
            print(json.dumps({
                "tool": r.tool_id, "success": r.success,
                "message": r.message, "dry_run": r.dry_run,
            }))
        else:
            print(f"  {icon} {r.message}")
        if not r.success:
            exit_code = EXIT_ERROR

    return exit_code


def cmd_outdated(args: argparse.Namespace) -> int:
    registry, platform_info, _ = _init_core(args)
    updater = ToolUpdater(registry, platform_info, dry_run=True)
    outdated = updater.get_outdated()

    if args.json_output:
        print(json.dumps([
            {"tool_id": o.tool_id, "name": o.tool_name,
             "installed": o.installed_version, "min": o.min_version,
             "message": o.message}
            for o in outdated
        ], indent=2))
    else:
        if not outdated:
            print("All tools are up to date. ✅")
        else:
            print("Outdated tools:")
            for o in outdated:
                print(f"  ⚠️  {o.tool_name}: {o.installed_version} → requires >={o.min_version}")

    return EXIT_OK


def cmd_configure(args: argparse.Namespace) -> int:
    registry, platform_info, config = _init_core(args)

    # Backup before changes
    config.backup()

    if args.tool:
        tool = registry.get_tool(args.tool)
        if not tool:
            print(f"Error: tool '{args.tool}' not found.", file=sys.stderr)
            return EXIT_TOOL_NOT_FOUND
        config.configure_tool(tool.id, tool.config_hints)
    else:
        for tool in registry.get_tools_for_platform(platform_info.os_name):
            config.configure_tool(tool.id, tool.config_hints)

    config.save()

    if args.export:
        print(config.export_env_script(args.shell))
    else:
        env_vars = config.get_env_vars()
        paths = config.get_paths()
        if args.json_output:
            print(json.dumps({"env_vars": env_vars, "paths": paths}, indent=2))
        else:
            print("Configuration applied:")
            for k, v in env_vars.items():
                print(f"  {k}={v}")
            if paths:
                print(f"  PATH additions: {', '.join(paths)}")
            print(f"\nRun with --export --shell {args.shell} to get an export script.")

    return EXIT_OK


def cmd_doctor(args: argparse.Namespace) -> int:
    registry, platform_info, config = _init_core(args)
    doctor = Doctor(registry, platform_info, config)
    report = doctor.run()

    if args.report_format == "json" or args.json_output:
        print(report.to_json())
    else:
        print(report.to_markdown())

    return EXIT_OK if report.ok else EXIT_ERROR


def cmd_logs(args: argparse.Namespace) -> int:
    log_file = _LOG_DIR / "esim-tm.log"
    if not log_file.exists():
        print("No log file found yet. Run a command first.")
        return EXIT_OK

    with open(log_file, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()

    for line in lines[-args.lines:]:
        print(line, end="")

    return EXIT_OK


# ── dispatch ─────────────────────────────────────────────────────────────────

_COMMANDS = {
    "list": cmd_list,
    "check": cmd_check,
    "install": cmd_install,
    "update": cmd_update,
    "outdated": cmd_outdated,
    "configure": cmd_configure,
    "doctor": cmd_doctor,
    "logs": cmd_logs,
}


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point.  Returns an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Set up logging early
    setup_logging(verbose=args.verbose, log_dir=_LOG_DIR)

    if args.command is None:
        parser.print_help()
        return EXIT_OK

    handler = _COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        return EXIT_ERROR

    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        if args.verbose:
            logger.exception("Unhandled error")
        else:
            print(f"Error: {exc}", file=sys.stderr)
            print("Run with --verbose for the full traceback.", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
