"""
Logging infrastructure for the medication advisor system.
Provides structured logging with multiple handlers.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

from src.utils.config import config


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Set up a logger with console and optional file handlers.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (defaults to config.LOG_LEVEL)
        log_file: Optional path to log file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    log_level = level or config.LOG_LEVEL
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(exist_ok=True, parents=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10_000_000,
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return setup_logger(name)
