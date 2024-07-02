import os
import sys
from pathlib import Path

from loguru import logger

log_dir = Path.home() / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

log_file_path = log_dir / "app.log"

if not os.getenv("TESTING"):
    logger.remove()

    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        level="DEBUG",
    )

    logger.add(
        log_file_path,
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        rotation="1 day",
        retention="10 days",
        level="DEBUG",
    )

    def configure_logger():
        logger.configure(
            handlers=[
                {
                    "sink": sys.stdout,
                    "format": "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
                    "level": "DEBUG",
                },
                {
                    "sink": log_file_path,
                    "format": "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
                    "rotation": "1 day",
                    "retention": "10 days",
                    "level": "DEBUG",
                },
            ]
        )

    configure_logger()
else:
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        level="DEBUG",
    )

log = logger
