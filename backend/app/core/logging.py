"""Central logging setup.

Rules for the whole codebase:
  * Log ticket IDs, event names, model names, durations - NEVER ticket
    titles/descriptions, contact details, prompts, or raw model output.
  * The filter below is a safety net that masks credentials in URLs.
"""

import logging
import re
import sys

_CREDENTIALS_IN_URL = re.compile(r"(://[^:/\s@]+:)[^@\s]+(@)")


class RedactSecretsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = _CREDENTIALS_IN_URL.sub(r"\1***\2", message)
        if redacted != message:
            record.msg = redacted
            record.args = None
        return True


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(RedactSecretsFilter())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"helpdesk.{name}")