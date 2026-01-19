"""Logging management."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from rich.console import Console
from rich.logging import RichHandler

from .enums import LogFormat
from .schemas import LogConfig

console = Console()


def setupLogging(
    config: Optional[LogConfig] = None,
    logFormat: LogFormat = LogFormat.PRETTY,
    logLevel: str = "INFO",
) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        config: Log configuration
        logFormat: Output format (pretty or json)
        logLevel: Log level

    Returns:
        Configured logger
    """
    if config is None:
        config = LogConfig()

    # Create log directory
    config.logDir.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger("fastapi_launcher")
    logger.setLevel(logLevel.upper())

    # Remove existing handlers and close them properly
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    if logFormat == LogFormat.PRETTY:
        # Rich handler for pretty output
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        # JSON handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)

    # Also add file handler
    fileHandler = logging.FileHandler(config.logDir / config.logFile)
    fileHandler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(fileHandler)

    return logger


class JsonFormatter(logging.Formatter):
    """JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        logData = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        if record.exc_info:
            logData["exception"] = self.formatException(record.exc_info)

        return json.dumps(logData)


def readLogFile(
    logFile: Path,
    lines: int = 100,
    follow: bool = False,
) -> Generator[str, None, None]:
    """
    Read log file contents.

    Args:
        logFile: Path to log file
        lines: Number of lines to read (from end)
        follow: If True, follow file for new content

    Yields:
        Log lines
    """
    if not logFile.exists():
        return

    if follow:
        yield from _followFile(logFile, lines)
    else:
        yield from _tailFile(logFile, lines)


def _tailFile(filePath: Path, lines: int) -> Generator[str, None, None]:
    """Read last N lines from file."""
    with open(filePath, "r") as f:
        # Simple approach: read all and take last N
        allLines = f.readlines()
        for line in allLines[-lines:]:
            yield line.rstrip()


def _followFile(filePath: Path, initialLines: int = 10) -> Generator[str, None, None]:
    """Follow file for new content (like tail -f)."""
    import time

    with open(filePath, "r") as f:
        # First, output last N lines
        f.seek(0, 2)  # Go to end
        fileSize = f.tell()

        # Simple approach: seek back and read
        f.seek(max(0, fileSize - 10000))  # Read last 10KB
        lines = f.readlines()
        for line in lines[-initialLines:]:
            yield line.rstrip()

        # Now follow
        while True:
            line = f.readline()
            if line:
                yield line.rstrip()
            else:
                time.sleep(0.1)


def getLogFiles(runtimeDir: Path) -> dict[str, Path]:
    """
    Get paths to log files.

    Args:
        runtimeDir: Runtime directory

    Returns:
        Dict mapping log type to file path
    """
    logsDir = runtimeDir / "logs"
    return {
        "main": logsDir / "fa.log",
        "access": logsDir / "access.log",
        "error": logsDir / "error.log",
    }


def rotateLogs(
    runtimeDir: Path, maxBytes: int = 10 * 1024 * 1024, backupCount: int = 5
) -> None:
    """
    Rotate log files if they exceed max size.

    Args:
        runtimeDir: Runtime directory
        maxBytes: Maximum file size before rotation
        backupCount: Number of backup files to keep
    """
    logFiles = getLogFiles(runtimeDir)

    for logType, logFile in logFiles.items():
        if not logFile.exists():
            continue

        if logFile.stat().st_size > maxBytes:
            _rotateFile(logFile, backupCount)


def _rotateFile(filePath: Path, backupCount: int) -> None:
    """Rotate a single log file."""
    # Remove oldest backup
    oldestBackup = Path(f"{filePath}.{backupCount}")
    if oldestBackup.exists():
        oldestBackup.unlink()

    # Shift existing backups
    for i in range(backupCount - 1, 0, -1):
        src = Path(f"{filePath}.{i}")
        dst = Path(f"{filePath}.{i + 1}")
        if src.exists():
            src.rename(dst)

    # Move current to .1
    if filePath.exists():
        filePath.rename(Path(f"{filePath}.1"))


def cleanLogs(runtimeDir: Path) -> int:
    """
    Remove all log files.

    Args:
        runtimeDir: Runtime directory

    Returns:
        Number of files removed
    """
    logsDir = runtimeDir / "logs"
    if not logsDir.exists():
        return 0

    count = 0
    for logFile in logsDir.glob("*.log*"):
        logFile.unlink()
        count += 1

    return count


def printLogEntry(line: str, logFormat: LogFormat = LogFormat.PRETTY) -> None:
    """
    Print a log entry with formatting.

    Args:
        line: Log line content
        logFormat: Output format
    """
    if logFormat == LogFormat.PRETTY:
        # Try to parse and colorize
        if " | ERROR | " in line:
            console.print(f"[red]{line}[/]")
        elif " | WARNING | " in line:
            console.print(f"[yellow]{line}[/]")
        elif " | INFO | " in line:
            console.print(f"[green]{line}[/]")
        else:
            console.print(line)
    else:
        console.print(line)
