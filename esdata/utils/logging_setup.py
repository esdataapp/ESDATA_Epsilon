import logging
from logging import Logger

_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

_DEF_LEVEL = logging.INFO

_loggers = {}

def get_logger(name: str, level=_DEF_LEVEL) -> Logger:
    if name in _loggers:
        return _loggers[name]
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    fmt = logging.Formatter(_FORMAT)
    handler.setFormatter(fmt)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    _loggers[name] = logger
    return logger
