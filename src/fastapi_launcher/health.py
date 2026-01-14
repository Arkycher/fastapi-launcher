"""Health check functionality."""

import time
from dataclasses import dataclass
from typing import Optional

import httpx

from .ui import printHealthStatus


@dataclass
class HealthCheckResult:
    """Health check result."""

    healthy: bool
    statusCode: Optional[int] = None
    responseTimeMs: Optional[float] = None
    error: Optional[str] = None
    body: Optional[dict] = None


async def checkHealthAsync(
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/health",
    timeout: float = 5.0,
) -> HealthCheckResult:
    """
    Perform async health check.

    Args:
        host: Server host
        port: Server port
        path: Health check endpoint path
        timeout: Request timeout in seconds

    Returns:
        HealthCheckResult with status and timing
    """
    url = f"http://{host}:{port}{path}"

    try:
        startTime = time.perf_counter()

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)

        endTime = time.perf_counter()
        responseTimeMs = (endTime - startTime) * 1000

        # Try to parse JSON body
        body = None
        try:
            body = response.json()
        except Exception:
            pass

        return HealthCheckResult(
            healthy=200 <= response.status_code < 300,
            statusCode=response.status_code,
            responseTimeMs=responseTimeMs,
            body=body,
        )

    except httpx.TimeoutException:
        return HealthCheckResult(
            healthy=False,
            error="Request timed out",
        )
    except httpx.ConnectError:
        return HealthCheckResult(
            healthy=False,
            error="Connection refused",
        )
    except Exception as e:
        return HealthCheckResult(
            healthy=False,
            error=str(e),
        )


def checkHealth(
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/health",
    timeout: float = 5.0,
) -> HealthCheckResult:
    """
    Perform synchronous health check.

    Args:
        host: Server host
        port: Server port
        path: Health check endpoint path
        timeout: Request timeout in seconds

    Returns:
        HealthCheckResult with status and timing
    """
    url = f"http://{host}:{port}{path}"

    try:
        startTime = time.perf_counter()

        with httpx.Client() as client:
            response = client.get(url, timeout=timeout)

        endTime = time.perf_counter()
        responseTimeMs = (endTime - startTime) * 1000

        # Try to parse JSON body
        body = None
        try:
            body = response.json()
        except Exception:
            pass

        return HealthCheckResult(
            healthy=200 <= response.status_code < 300,
            statusCode=response.status_code,
            responseTimeMs=responseTimeMs,
            body=body,
        )

    except httpx.TimeoutException:
        return HealthCheckResult(
            healthy=False,
            error="Request timed out",
        )
    except httpx.ConnectError:
        return HealthCheckResult(
            healthy=False,
            error="Connection refused",
        )
    except Exception as e:
        return HealthCheckResult(
            healthy=False,
            error=str(e),
        )


def printHealthResult(result: HealthCheckResult, url: str) -> None:
    """
    Print health check result.

    Args:
        result: Health check result
        url: Health check URL
    """
    printHealthStatus(
        healthy=result.healthy,
        url=url,
        responseTime=result.responseTimeMs,
    )


def waitForHealthy(
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/health",
    timeout: float = 30.0,
    checkInterval: float = 0.5,
) -> bool:
    """
    Wait for server to become healthy.

    Args:
        host: Server host
        port: Server port
        path: Health check endpoint path
        timeout: Maximum time to wait in seconds
        checkInterval: Time between checks in seconds

    Returns:
        True if healthy, False if timeout
    """
    startTime = time.time()

    while time.time() - startTime < timeout:
        result = checkHealth(host, port, path, timeout=2.0)
        if result.healthy:
            return True
        time.sleep(checkInterval)

    return False
