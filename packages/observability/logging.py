"""JSON logs with stable trace fields and no business payloads."""

import logging
import os

import structlog

TRACE_FIELDS = (
    "trace_id",
    "call_id",
    "workflow_id",
    "intent_revision",
    "operation_id",
    "attempt_id",
    "receipt_id",
    "claim_permit_id",
    "audio_segment_id",
    "repair_obligation_id",
    "scenario_id",
    "experiment_run_id",
    "execution_id",
)


def configure_logging(service: str) -> None:
    """Install JSON logging once per service process."""
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    structlog.contextvars.bind_contextvars(service=service)
