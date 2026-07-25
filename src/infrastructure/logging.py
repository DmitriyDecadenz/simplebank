"""Structured logging configuration based on structlog."""

from __future__ import annotations

import logging
import sys

import structlog

from src.infrastructure.config import load_settings

config = load_settings()


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(ep in msg for ep in config.app.excluded_endpoints)


def configure_logging(*, level: str = "INFO", json_logs: bool = True) -> None:
    log_level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=True, pad_event=0)
    )

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

    httpx_logger = logging.getLogger("httpx")
    httpx_logger.handlers = [handler]
    httpx_logger.setLevel(log_level)
    httpx_logger.propagate = False
