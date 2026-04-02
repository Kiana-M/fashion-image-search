import logging

from app.config import LOG_LEVEL


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL, logging.INFO),
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
    else:
        root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
