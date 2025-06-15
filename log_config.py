import logging
import os
from pythonjsonlogger import jsonlogger


def setup_logger(name="movie_metadata_logger"):
    logger = logging.getLogger(name)
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    logHandler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(logHandler)
    log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    return logger
