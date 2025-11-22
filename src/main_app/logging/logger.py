"""Logger setup - Console and rotating file handlers."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Setup centralized logging with console and rotating file handlers.

    Args:
        config: Configuration dict from config files (full config, not just logging section)
    """
    # Extract logging config
    log_config = config.get("logging", {})

    # Parse global level
    level_str = log_config.get("level", "DEBUG")
    try:
        level = getattr(logging, level_str.upper())
    except AttributeError:
        # Invalid log level, fallback to DEBUG with warning
        level = logging.DEBUG
        print(f"WARNING: Invalid log level '{level_str}', falling back to DEBUG")

    # Parse file configuration
    file_config = log_config.get("file", {})
    file_output = file_config.get("enabled", True)
    log_dir = Path(file_config.get("directory", "logs"))
    log_file = file_config.get("filename", "app.log")
    max_bytes = file_config.get("max_bytes", 10 * 1024 * 1024)
    backup_count = file_config.get("backup_count", 5)

    # Parse console configuration
    console_config = log_config.get("console", {})
    console_output = console_config.get("enabled", True)

    # Parse format configuration
    format_config = log_config.get("format", {})
    fmt = format_config.get("fmt", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    datefmt = format_config.get("datefmt", "%Y-%m-%d %H:%M:%S")

    # Create log directory if needed
    if file_output:
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / log_file

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Human-readable format
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # Console handler
    if console_output:
        console_level_str = console_config.get("level", level_str)
        try:
            console_level = getattr(logging, console_level_str.upper())
        except AttributeError:
            console_level = level

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Rotating file handler
    if file_output:
        file_level_str = file_config.get("level", level_str)
        try:
            file_level = getattr(logging, file_level_str.upper())
        except AttributeError:
            file_level = level

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    root_logger.info(
        f"Logging configured successfully: level={logging.getLevelName(level)}, "
        f"console={'enabled' if console_output else 'disabled'}, "
        f"file={'enabled' if file_output else 'disabled'}, "
        f"directory={log_dir}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
