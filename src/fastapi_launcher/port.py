"""Port detection and management utilities."""

import socket
from dataclasses import dataclass
from typing import Optional

import psutil


@dataclass
class PortInfo:
    """Information about a port and its occupying process."""

    port: int
    pid: Optional[int] = None
    processName: Optional[str] = None
    status: str = "unknown"

    @property
    def isOccupied(self) -> bool:
        """Check if port is occupied."""
        return self.pid is not None


def isPortInUse(port: int, host: str = "127.0.0.1") -> bool:
    """
    Check if a port is in use.

    Args:
        port: Port number to check
        host: Host to check on

    Returns:
        True if port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        return result == 0


def getPortInfo(port: int) -> PortInfo:
    """
    Get information about a port and its occupying process.

    Args:
        port: Port number to check

    Returns:
        PortInfo with process details if port is occupied
    """
    info = PortInfo(port=port)

    try:
        connections = psutil.net_connections(kind="inet")
        for conn in connections:
            if conn.laddr.port == port and conn.status == "LISTEN":
                info.pid = conn.pid
                info.status = conn.status

                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        info.processName = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                break
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        # Fallback to socket check
        if isPortInUse(port):
            info.status = "occupied"

    return info


def findAvailablePort(startPort: int = 8000, endPort: int = 8100) -> Optional[int]:
    """
    Find an available port in the given range.

    Args:
        startPort: Start of port range
        endPort: End of port range (exclusive)

    Returns:
        First available port, or None if none found
    """
    for port in range(startPort, endPort):
        if not isPortInUse(port):
            return port
    return None


def killProcessOnPort(port: int, force: bool = False) -> bool:
    """
    Kill the process occupying a port.

    Args:
        port: Port number
        force: If True, use SIGKILL instead of SIGTERM

    Returns:
        True if process was killed, False otherwise
    """
    info = getPortInfo(port)

    if info.pid is None:
        return False

    try:
        proc = psutil.Process(info.pid)
        if force:
            proc.kill()  # SIGKILL
        else:
            proc.terminate()  # SIGTERM

        # Wait for process to terminate
        try:
            proc.wait(timeout=5)
            return True
        except psutil.TimeoutExpired:
            if not force:
                # Try force kill
                proc.kill()
                proc.wait(timeout=3)
                return True
            return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def waitForPort(port: int, host: str = "127.0.0.1", timeout: float = 30.0) -> bool:
    """
    Wait for a port to become available (for connection).

    Args:
        port: Port number
        host: Host to check
        timeout: Maximum time to wait in seconds

    Returns:
        True if port became available, False if timeout
    """
    import time

    startTime = time.time()
    while time.time() - startTime < timeout:
        if isPortInUse(port, host):
            return True
        time.sleep(0.1)

    return False


def waitForPortFree(port: int, timeout: float = 10.0) -> bool:
    """
    Wait for a port to become free.

    Args:
        port: Port number
        timeout: Maximum time to wait in seconds

    Returns:
        True if port became free, False if timeout
    """
    import time

    startTime = time.time()
    while time.time() - startTime < timeout:
        if not isPortInUse(port):
            return True
        time.sleep(0.1)

    return False
