"""Tests for health check functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from fastapi_launcher.health import (
    HealthCheckResult,
    checkHealth,
    checkHealthAsync,
    waitForHealthy,
)


class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_healthy_result(self) -> None:
        """Test healthy result."""
        result = HealthCheckResult(
            healthy=True,
            statusCode=200,
            responseTimeMs=50.0,
        )
        
        assert result.healthy is True
        assert result.statusCode == 200
        assert result.responseTimeMs == 50.0

    def test_unhealthy_result(self) -> None:
        """Test unhealthy result."""
        result = HealthCheckResult(
            healthy=False,
            error="Connection refused",
        )
        
        assert result.healthy is False
        assert result.error == "Connection refused"

    def test_result_with_body(self) -> None:
        """Test result with response body."""
        result = HealthCheckResult(
            healthy=True,
            statusCode=200,
            body={"status": "healthy", "version": "1.0.0"},
        )
        
        assert result.body["status"] == "healthy"


class TestCheckHealth:
    """Tests for synchronous health check."""

    @patch("fastapi_launcher.health.httpx.Client")
    def test_check_health_success(self, mockClient: MagicMock) -> None:
        """Test successful health check."""
        mockResponse = MagicMock()
        mockResponse.status_code = 200
        mockResponse.json.return_value = {"status": "healthy"}
        
        mockClientInstance = MagicMock()
        mockClientInstance.__enter__ = MagicMock(return_value=mockClientInstance)
        mockClientInstance.__exit__ = MagicMock(return_value=False)
        mockClientInstance.get.return_value = mockResponse
        mockClient.return_value = mockClientInstance
        
        result = checkHealth(port=8000)
        
        assert result.healthy is True
        assert result.statusCode == 200

    @patch("fastapi_launcher.health.httpx.Client")
    def test_check_health_timeout(self, mockClient: MagicMock) -> None:
        """Test health check timeout."""
        mockClientInstance = MagicMock()
        mockClientInstance.__enter__ = MagicMock(return_value=mockClientInstance)
        mockClientInstance.__exit__ = MagicMock(return_value=False)
        mockClientInstance.get.side_effect = httpx.TimeoutException("Timeout")
        mockClient.return_value = mockClientInstance
        
        result = checkHealth(port=8000)
        
        assert result.healthy is False
        assert result.error == "Request timed out"

    @patch("fastapi_launcher.health.httpx.Client")
    def test_check_health_connection_error(self, mockClient: MagicMock) -> None:
        """Test health check connection error."""
        mockClientInstance = MagicMock()
        mockClientInstance.__enter__ = MagicMock(return_value=mockClientInstance)
        mockClientInstance.__exit__ = MagicMock(return_value=False)
        mockClientInstance.get.side_effect = httpx.ConnectError("Connection refused")
        mockClient.return_value = mockClientInstance
        
        result = checkHealth(port=8000)
        
        assert result.healthy is False
        assert result.error == "Connection refused"

    @patch("fastapi_launcher.health.httpx.Client")
    def test_check_health_5xx_error(self, mockClient: MagicMock) -> None:
        """Test health check with 5xx error."""
        mockResponse = MagicMock()
        mockResponse.status_code = 500
        mockResponse.json.side_effect = ValueError("Not JSON")
        
        mockClientInstance = MagicMock()
        mockClientInstance.__enter__ = MagicMock(return_value=mockClientInstance)
        mockClientInstance.__exit__ = MagicMock(return_value=False)
        mockClientInstance.get.return_value = mockResponse
        mockClient.return_value = mockClientInstance
        
        result = checkHealth(port=8000)
        
        assert result.healthy is False
        assert result.statusCode == 500


class TestCheckHealthAsync:
    """Tests for async health check."""

    @pytest.mark.asyncio
    @patch("fastapi_launcher.health.httpx.AsyncClient")
    async def test_check_health_async_success(self, mockClient: MagicMock) -> None:
        """Test async health check success."""
        mockResponse = MagicMock()
        mockResponse.status_code = 200
        mockResponse.json.return_value = {"status": "ok"}
        
        mockClientInstance = AsyncMock()
        mockClientInstance.get.return_value = mockResponse
        mockClientInstance.__aenter__.return_value = mockClientInstance
        mockClientInstance.__aexit__.return_value = None
        mockClient.return_value = mockClientInstance
        
        result = await checkHealthAsync(port=8000)
        
        assert result.healthy is True

    @pytest.mark.asyncio
    @patch("fastapi_launcher.health.httpx.AsyncClient")
    async def test_check_health_async_timeout(self, mockClient: MagicMock) -> None:
        """Test async health check timeout."""
        mockClientInstance = AsyncMock()
        mockClientInstance.get.side_effect = httpx.TimeoutException("Timeout")
        mockClientInstance.__aenter__.return_value = mockClientInstance
        mockClientInstance.__aexit__.return_value = None
        mockClient.return_value = mockClientInstance
        
        result = await checkHealthAsync(port=8000)
        
        assert result.healthy is False
        assert result.error == "Request timed out"


class TestWaitForHealthy:
    """Tests for waiting for healthy status."""

    @patch("fastapi_launcher.health.checkHealth")
    def test_wait_healthy_immediately(self, mockCheck: MagicMock) -> None:
        """Test when server is healthy immediately."""
        mockCheck.return_value = HealthCheckResult(healthy=True)
        
        result = waitForHealthy(timeout=1.0)
        
        assert result is True

    @patch("fastapi_launcher.health.checkHealth")
    @patch("fastapi_launcher.health.time.sleep")
    def test_wait_becomes_healthy(
        self, mockSleep: MagicMock, mockCheck: MagicMock
    ) -> None:
        """Test waiting until server becomes healthy."""
        # First two checks fail, third succeeds
        mockCheck.side_effect = [
            HealthCheckResult(healthy=False, error="Not ready"),
            HealthCheckResult(healthy=False, error="Not ready"),
            HealthCheckResult(healthy=True),
        ]
        
        result = waitForHealthy(timeout=5.0, checkInterval=0.1)
        
        assert result is True
        assert mockCheck.call_count == 3

    @patch("fastapi_launcher.health.checkHealth")
    @patch("fastapi_launcher.health.time.time")
    def test_wait_timeout(
        self, mockTime: MagicMock, mockCheck: MagicMock
    ) -> None:
        """Test timeout while waiting."""
        mockCheck.return_value = HealthCheckResult(healthy=False, error="Not ready")
        
        # Simulate time passing
        mockTime.side_effect = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        
        result = waitForHealthy(timeout=0.5, checkInterval=0.1)
        
        assert result is False


class TestHealthCheckEdgeCases:
    """Tests for health check edge cases."""

    @patch("fastapi_launcher.health.httpx.Client")
    def test_check_health_json_parse_error(self, mockClient: MagicMock) -> None:
        """Test health check when JSON parsing fails."""
        from fastapi_launcher.health import checkHealth
        
        mockResponse = MagicMock()
        mockResponse.status_code = 200
        mockResponse.json.side_effect = ValueError("Invalid JSON")
        
        mockClient.return_value.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mockResponse)))
        mockClient.return_value.__exit__ = MagicMock(return_value=False)
        
        result = checkHealth()
        
        # Should still be healthy, just without body
        assert result.healthy is True
        assert result.body is None

    @patch("fastapi_launcher.health.httpx.Client")
    def test_check_health_generic_exception(self, mockClient: MagicMock) -> None:
        """Test health check with generic exception."""
        from fastapi_launcher.health import checkHealth
        
        mockClient.return_value.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(side_effect=RuntimeError("Unexpected error")))
        )
        mockClient.return_value.__exit__ = MagicMock(return_value=False)
        
        result = checkHealth()
        
        assert result.healthy is False
        assert "Unexpected error" in result.error
