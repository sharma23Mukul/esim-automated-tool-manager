"""Safe subprocess execution with dry-run support and executable lookup."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

__all__ = ["run_command", "find_executable", "get_command_version"]

logger = logging.getLogger("esim_toolmanager.utils.process")


def run_command(
    cmd: List[str],
    *,
    capture: bool = True,
    check: bool = True,
    dry_run: bool = False,
    timeout: int = 300,
) -> Optional[subprocess.CompletedProcess]:
    """Execute *cmd* as a subprocess.

    Parameters
    ----------
    cmd:
        Command and arguments.
    capture:
        Capture stdout/stderr (default ``True``).
    check:
        Raise on non-zero exit (default ``True``).
    dry_run:
        If ``True`` log the command but do **not** execute it.
    timeout:
        Seconds before the process is killed.

    Returns
    -------
    ``CompletedProcess`` on real execution, ``None`` on dry-run.
    """
    cmd_str = " ".join(cmd)
    if dry_run:
        logger.info("[DRY RUN] Would execute: %s", cmd_str)
        return None

    logger.debug("Executing: %s", cmd_str)
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            check=check,
            timeout=timeout,
        )
        if result.stdout:
            logger.debug("stdout: %s", result.stdout.strip())
        return result
    except subprocess.CalledProcessError as exc:
        logger.error(
            "Command failed (exit %d): %s\n  stderr: %s",
            exc.returncode,
            cmd_str,
            (exc.stderr or "").strip(),
        )
        raise
    except FileNotFoundError:
        logger.error("Command not found: %s", cmd[0])
        raise
    except subprocess.TimeoutExpired:
        logger.error("Command timed out after %ds: %s", timeout, cmd_str)
        raise


def find_executable(name: str) -> Optional[Path]:
    """Locate *name* on ``PATH``.  Returns ``None`` when not found."""
    path = shutil.which(name)
    return Path(path) if path else None


def get_command_version(
    cmd: List[str],
    pattern: str,
) -> Optional[str]:
    """Run *cmd* and extract the first regex match of *pattern*.

    Returns the first capture-group if present, otherwise the whole match.
    Returns ``None`` on any failure.
    """
    import re

    try:
        result = run_command(cmd, check=False, dry_run=False, timeout=30)
        if result is None:
            return None
        output = (result.stdout or "") + (result.stderr or "")
        m = re.search(pattern, output)
        if m:
            return m.group(1) if m.lastindex else m.group(0)
    except Exception:
        logger.debug("Could not get version from %s", " ".join(cmd), exc_info=True)
    return None
