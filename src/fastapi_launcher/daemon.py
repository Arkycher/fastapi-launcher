"""Daemon mode support (Unix only)."""

import os
import sys
from pathlib import Path
from typing import Optional

from .ui import printErrorMessage, printWarningMessage


def isUnix() -> bool:
    """Check if running on a Unix-like system."""
    return sys.platform != "win32"


def daemonize(
    pidFile: Optional[Path] = None,
    logFile: Optional[Path] = None,
    workDir: Optional[Path] = None,
) -> None:
    """
    Daemonize the current process using double fork.

    This is a Unix-only operation. On Windows, this will print a warning
    and continue running in foreground.

    Args:
        pidFile: Path to write PID file (optional)
        logFile: Path for stdout/stderr redirect (optional)
        workDir: Working directory for daemon (optional)

    Raises:
        OSError: If fork fails
    """
    if not isUnix():
        printWarningMessage(
            "Daemon mode is not supported on Windows. "
            "Consider using NSSM (nssm.cc) for Windows service management."
        )
        return

    # First fork - create child process
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process exits
            sys.exit(0)
    except OSError as e:
        printErrorMessage(f"First fork failed: {e}")
        sys.exit(1)

    # Decouple from parent environment
    os.chdir(workDir or "/")
    os.setsid()  # Create new session
    os.umask(0o022)  # Set file creation mask

    # Second fork - ensure daemon cannot acquire a controlling terminal
    try:
        pid = os.fork()
        if pid > 0:
            # First child exits
            sys.exit(0)
    except OSError as e:
        printErrorMessage(f"Second fork failed: {e}")
        sys.exit(1)

    # Now running as daemon

    # Redirect standard file descriptors
    _redirectStdStreams(logFile)

    # Write PID file if specified
    if pidFile:
        pidFile.parent.mkdir(parents=True, exist_ok=True)
        pidFile.write_text(str(os.getpid()))


def _redirectStdStreams(logFile: Optional[Path] = None) -> None:
    """
    Redirect stdin, stdout, stderr to /dev/null or log file.

    Args:
        logFile: Path for stdout/stderr redirect
    """
    # Close all open file descriptors
    sys.stdout.flush()
    sys.stderr.flush()

    # Open /dev/null for stdin
    devNull = open("/dev/null", "r")
    os.dup2(devNull.fileno(), sys.stdin.fileno())

    # Open log file or /dev/null for stdout/stderr
    if logFile:
        logFile.parent.mkdir(parents=True, exist_ok=True)
        logFd = open(logFile, "a+")
        os.dup2(logFd.fileno(), sys.stdout.fileno())
        os.dup2(logFd.fileno(), sys.stderr.fileno())
    else:
        devNullOut = open("/dev/null", "w")
        os.dup2(devNullOut.fileno(), sys.stdout.fileno())
        os.dup2(devNullOut.fileno(), sys.stderr.fileno())


def setupDaemonLogging(runtimeDir: Path) -> Path:
    """
    Setup logging directory for daemon mode.

    Args:
        runtimeDir: Runtime directory path

    Returns:
        Path to log file
    """
    logsDir = runtimeDir / "logs"
    logsDir.mkdir(parents=True, exist_ok=True)

    logFile = logsDir / "fa.log"
    return logFile


def checkDaemonSupport() -> tuple[bool, str]:
    """
    Check if daemon mode is supported on this platform.

    Returns:
        Tuple of (supported, message)
    """
    if isUnix():
        return True, "Daemon mode is supported on this platform."
    else:
        return False, (
            "Daemon mode is not supported on Windows. "
            "Consider using NSSM (nssm.cc) or running as a Windows Service."
        )
