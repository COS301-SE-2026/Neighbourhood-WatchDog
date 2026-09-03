from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app_config import get_app_data_dir


LOG_FILE_NAME = "watchdog.log"
MAX_LOG_BYTES = 2 * 1024 * 1024
LOG_BACKUP_COUNT = 5


def configure_application_logging() -> Path:
    """
    Configure persistent rotating logs for the WatchDog desktop app.

    Logs are stored in the OS-appropriate WatchDog application-data
    directory, not in the repository.

    Returns:
        The active log-file path.
    """

    log_directory = get_app_data_dir() / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)

    log_path = log_directory / LOG_FILE_NAME

    logger = logging.getLogger("watchdog")
    logger.setLevel(logging.INFO)

    # Prevent messages from being passed to Python's root logger as
    # well, which can otherwise create duplicate output.
    logger.propagate = False

    # The application can create pages more than once. Do not add a
    # second file handler every time logging is initialised.
    for handler in logger.handlers:
        if (
            isinstance(handler, RotatingFileHandler)
            and Path(handler.baseFilename) == log_path
        ):
            return log_path

    handler = RotatingFileHandler(
        log_path,
        maxBytes=MAX_LOG_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )

    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s "
            "%(name)s: %(message)s"
        )
    )

    logger.addHandler(handler)

    logger.info("Persistent application logging configured.")
    return log_path