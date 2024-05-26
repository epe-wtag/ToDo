import os
import sys

from loguru import logger

if not os.getenv("TESTING"):
    logger.remove()

    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        level="DEBUG",
    )

    logger.add(
        "/logs/app.log",
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
                    "sink": "/logs/app.log",
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
