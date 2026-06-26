import sys

import structlog

from app.config import settings


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    pre_chain = [
        structlog.processors.add_log_level,
        timestamper,
    ]

    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            timestamper,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handler = sys.stderr
    logger = structlog.get_logger()
    logger.info("logging.configured", level=settings.log_level)
