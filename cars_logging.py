from __future__ import annotations

import logging
import logging.config
from pathlib import Path

from cars_paths import LOG_DIR, PROJECT_DIR


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    config_path = PROJECT_DIR / "logging.ini"
    logging.config.fileConfig(config_path, disable_existing_loggers=False)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
