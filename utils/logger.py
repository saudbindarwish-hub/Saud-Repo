import logging
import logging.handlers
import os
from pythonjsonlogger import jsonlogger

from config.settings import settings


def _setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    os.makedirs(settings.log_dir, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(settings.log_dir, "bot.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
    )
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    return _setup_logger(name)
