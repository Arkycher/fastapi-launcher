"""Log format enumeration."""

from enum import Enum


class LogFormat(str, Enum):
    """Log output format."""

    PRETTY = "pretty"
    JSON = "json"
