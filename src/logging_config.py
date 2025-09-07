# logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler

import structlog

from .constants import LOG_FILE


def setup_logging():
    """Configure structured logging with console and file handlers."""
    # Standard logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )

    # Rotating file handler
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=5)
    file_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(file_handler)

    # Structlog configuration
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


logger = setup_logging()


def log_info(message: str, **kwargs):
    """
    Log an info-level structured message.

    Args:
        message (str): The main log message.
        **kwargs: Additional structured fields (e.g., user_id=123, endpoint="/api").
    """
    logger.info(message, **kwargs)


def log_warn(message: str, **kwargs):
    """
    Log an info-level structured message.

    Args:
        message (str): The main log message.
        **kwargs: Additional structured fields (e.g., user_id=123, endpoint="/api").
    """
    logger.warning(message, **kwargs)


def log_error(message: str, **kwargs):
    """
    Log an info-level structured message.

    Args:
        message (str): The main log message.
        **kwargs: Additional structured fields (e.g., user_id=123, endpoint="/api").
    """
    logger.warning(message, **kwargs)
