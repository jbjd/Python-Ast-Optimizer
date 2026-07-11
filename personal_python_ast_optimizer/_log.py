"""Internal module for logging."""

import logging
import sys


def get_logger() -> logging.Logger:
    logger = logging.getLogger("PAO_logger")
    logger.setLevel(logging.WARNING)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(
        logging.Formatter("[Python AST Optimizer] %(levelname)s:%(name)s:%(message)s")
    )
    logger.addHandler(sh)
    return logger
