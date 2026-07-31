"""
Logger module for the AI Coding Agent.
Provides rich console logging and structured file logging.
"""

import logging
import sys
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler

_console = Console()
_default_logger: logging.Logger | None = None


def setup_logger(
    name: str = "agent",
    log_level: str = "INFO",
    log_file: Path | str | None = None,
) -> logging.Logger:
    """
    Configure and return a Logger instance with Rich console formatting
    and optional file output.

    Args:
        name: Name of the logger instance.
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a file where logs will be written.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        logger.handlers.clear()

    # Rich Console Handler
    rich_handler = RichHandler(
        console=_console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    rich_handler.setLevel(numeric_level)
    formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    rich_handler.setFormatter(formatter)
    logger.addHandler(rich_handler)

    # File Handler (if log_file specified)
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def get_logger(name: str = "agent") -> logging.Logger:
    """
    Retrieve or create the global logger instance.

    Args:
        name: Name of the logger to retrieve.

    Returns:
        logging.Logger instance.
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger(name=name)
    return logger if (logger := logging.getLogger(name)).handlers else _default_logger


def get_console() -> Console:
    """
    Get the global Rich Console instance for progress displays and rich printing.

    Returns:
        rich.console.Console instance.
    """
    return _console
