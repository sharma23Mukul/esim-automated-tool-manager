"""Structured logging with rotating file handler and coloured console output."""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

__all__ = ["setup_logging", "get_logger"]

_CONFIGURED = False

# ANSI colour helpers (console only; no dependency needed).
_RESET = "\033[0m"
_COLOURS = {
    "DEBUG": "\033[36m",     # cyan
    "INFO": "\033[32m",      # green
    "WARNING": "\033[33m",   # yellow
    "ERROR": "\033[31m",     # red
    "CRITICAL": "\033[1;31m",  # bold red
}


class _ColouredFormatter(logging.Formatter):
    """Formatter that prepends ANSI colour codes per log level."""

    def __init__(self, fmt: str, datefmt: Optional[str] = None) -> None:
        super().__init__(fmt, datefmt)
        self._use_colour = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        if self._use_colour:
            colour = _COLOURS.get(record.levelname, "")
            return f"{colour}{msg}{_RESET}"
        return msg


def setup_logging(
    verbose: bool = False,
    log_dir: Optional[Path] = None,
) -> logging.Logger:
    """Configure the ``esim_toolmanager`` logger.

    Parameters
    ----------
    verbose:
        If ``True``, console shows DEBUG messages; otherwise INFO and above.
    log_dir:
        Directory for the rotating log file.  Created if it doesn't exist.
        If ``None``, file logging is disabled.
    """
    global _CONFIGURED  # noqa: PLW0603

    logger = logging.getLogger("esim_toolmanager")
    if _CONFIGURED:
        return logger
    logger.setLevel(logging.DEBUG)

    # --- Console handler ---
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    cfmt = "%(levelname)-8s %(message)s"
    console.setFormatter(_ColouredFormatter(cfmt))
    logger.addHandler(console)

    # --- Rotating file handler ---
    if log_dir is not None:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            fh = logging.handlers.RotatingFileHandler(
                log_dir / "esim-tm.log",
                maxBytes=1_000_000,
                backupCount=5,
                encoding="utf-8",
            )
            fh.setLevel(logging.DEBUG)
            ffmt = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
            fh.setFormatter(logging.Formatter(ffmt, datefmt="%Y-%m-%d %H:%M:%S"))
            logger.addHandler(fh)
        except (PermissionError, OSError):
            # Can't write logs to disk — continue with console only.
            pass

    _CONFIGURED = True
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``esim_toolmanager`` namespace."""
    return logging.getLogger(f"esim_toolmanager.{name}")
