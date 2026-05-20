import logging
import sys

logger = logging.getLogger("standard_mapping")

def setup_logger(level="INFO"):
    global logger
    logger = logging.getLogger("standard_mapping")
    logger.setLevel(getattr(logging, level))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level))
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger