"""Run mode enumeration."""

from enum import Enum


class RunMode(str, Enum):
    """Run mode for FastAPI launcher."""

    DEV = "dev"
    PROD = "prod"


class ServerBackend(str, Enum):
    """Server backend enumeration."""

    UVICORN = "uvicorn"
    GUNICORN = "gunicorn"
