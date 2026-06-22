"""Structured logging via structlog — JSON in production, pretty in dev."""

import structlog


def setup_logging(json_format: bool = False) -> None:
    """Configure structlog for the application.

    Args:
        json_format: If True, output JSON lines. Otherwise, pretty console output.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_format:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a bound logger instance, optionally named."""
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(component=name)
    return logger
