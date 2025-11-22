"""Logger setup - Console and rotating file handlers."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(
    log_dir: Optional[Path] = None,
    log_file: str = "app.log",
    level: int = logging.DEBUG,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Setup centralized logging with console and rotating file handlers.

    Args:
        log_dir: Directory for log files. Defaults to ./logs
        log_file: Name of log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Enable console output
        file_output: Enable file output
        max_bytes: Max size per log file before rotation
        backup_count: Number of backup files to keep
    """
    # Create log directory if needed
    if file_output:
        log_dir = log_dir or Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / log_file

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Human-readable format
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Rotating file handler
    if file_output:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    root_logger.info(
        f"Logging initialized: level={logging.getLevelName(level)}, "
        f"console={'enabled' if console_output else 'disabled'}, "
        f"file={'enabled' if file_output else 'disabled'}"
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
