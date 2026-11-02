"""Structured JSON logging so Loki/Promtail can parse fields."""
import logging
import sys

from pythonjsonlogger.json import JsonFormatter


def configure_logging(level: str = "INFO", service: str = "jobs-api") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"levelname": "level", "asctime": "ts"},
            static_fields={"service": service},
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
