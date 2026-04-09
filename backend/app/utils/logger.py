import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name: str = "invoice_app"):
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # avoid duplicate logs

    logger.setLevel(logging.INFO)

    # File log
    log_file = os.path.join(
        LOG_DIR,
        f"log_{datetime.now().strftime('%Y%m%d')}.log"
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Console log
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
