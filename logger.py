import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from configuration import Configuration


def _init_logger(log_dir: Path) -> logging.Logger:
    logger = logging.getLogger(__name__)

    # create logger
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(
        logging.Formatter("%(asctime)s: %(levelname)s: %(message)s")
    )
    stdout_handler.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler(
        log_dir / 'app.log', maxBytes=20000, backupCount=20
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)

    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)

    return logger


logger = _init_logger(Configuration.LOG_DIR)
