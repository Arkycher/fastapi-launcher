"""Tests for port detection utilities."""

import socket
import time
from unittest.mock import MagicMock, patch

import pytest

from fastapi_launcher.port import (
    PortInfo,
    findAvailablePort,
    getPortInfo,
    isPortInUse,
    waitForPort,
    waitForPortFree,
)


class TestIsPortInUse:
    """Tests for port usage detection."""

    def test_port_not_in_use(self) -> None:
        """Test detecting unused port."""
        # Find a port that's definitely not in use
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        
        # Port should be free now
        assert isPortInUse(port) is False

    def test_port_in_use(self) -> None:
        """Test detecting port in use."""
        # Bind to a port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
            port = sock.getsockname()[1]
            
            # Port should be in use
            assert isPortInUse(port, "127.0.0.1") is True


class TestPortInfo:
    """Tests for PortInfo dataclass."""

    def test_port_info_not_occupied(self) -> None:
        """Test PortInfo for unoccupied port."""
        info = PortInfo(port=8000)
        
        assert info.port == 8000
        assert info.pid is None
        assert info.isOccupied is False

    def test_port_info_occupied(self) -> None:
        """Test PortInfo for occupied port."""
        info = PortInfo(
            port=8000,
            pid=1234,
            processName="python",
            status="LISTEN",
        )
        
        assert info.isOccupied is True
        assert info.processName == "python"


class TestGetPortInfo:
    """Tests for getting port information."""

    def test_get_info_unused_port(self) -> None:
        """Test getting info for unused port."""
        info = getPortInfo(59999)
        
        assert info.port == 59999
        # May or may not have pid depending on system

    @patch("fastapi_launcher.port.psutil")
    def test_get_info_with_process(self, mockPsutil: MagicMock) -> None:
        """Test getting info with process details."""
        mockConn = MagicMock()
        mockConn.laddr.port = 8000
        mockConn.status = "LISTEN"
        mockConn.pid = 1234
        
        mockProc = MagicMock()
        mockProc.name.return_value = "python"
        
        mockPsutil.net_connections.return_value = [mockConn]
        mockPsutil.Process.return_value = mockProc
        
        info = getPortInfo(8000)
        
        assert info.port == 8000
        assert info.pid == 1234
        assert info.processName == "python"


class TestFindAvailablePort:
    """Tests for finding available ports."""

    def test_find_available_port(self) -> None:
        """Test finding an available port."""
        port = findAvailablePort(50000, 50100)
        
        assert port is not None
        assert 50000 <= port < 50100
        assert isPortInUse(port) is False

    def test_find_port_when_first_available(self) -> None:
        """Test that first available port is returned."""
        # This is probabilistic but should generally work
        port = findAvailablePort(60000, 60010)
        
        assert port is not None

    def test_no_port_available(self) -> None:
        """Test when no port is available."""
        # Create a mock scenario where all ports are in use
        with patch("fastapi_launcher.port.isPortInUse", return_value=True):
            port = findAvailablePort(8000, 8002)
            assert port is None


class TestWaitForPort:
    """Tests for waiting for port availability."""

    def test_wait_for_port_already_available(self) -> None:
        """Test waiting when port is already in use."""
        # Start a server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
            port = sock.getsockname()[1]
            
            result = waitForPort(port, timeout=1.0)
            assert result is True

    def test_wait_for_port_timeout(self) -> None:
        """Test timeout when port never becomes available."""
        # Use a port that's definitely not in use
        result = waitForPort(59998, timeout=0.2)
        assert result is False


class TestWaitForPortFree:
    """Tests for waiting for port to be free."""

    def test_wait_for_port_free_already_free(self) -> None:
        """Test when port is already free."""
        result = waitForPortFree(59997, timeout=0.5)
        assert result is True

    def test_wait_for_port_free_becomes_free(self) -> None:
        """Test waiting for port to become free."""
        # This is hard to test reliably without threading
        # Just verify the function works for already-free port
        result = waitForPortFree(59996, timeout=0.2)
        assert result is True


class TestKillProcessOnPort:
    """Tests for killing process on port."""

    def test_kill_no_process(self) -> None:
        """Test killing when no process on port."""
        from fastapi_launcher.port import killProcessOnPort
        
        result = killProcessOnPort(59995)
        assert result is False

    @patch("fastapi_launcher.port.getPortInfo")
    @patch("fastapi_launcher.port.psutil.Process")
    def test_kill_process_success(self, mockProcess: MagicMock, mockGetPort: MagicMock) -> None:
        """Test killing process successfully."""
        from fastapi_launcher.port import killProcessOnPort
        
        mockGetPort.return_value = MagicMock(pid=12345)
        mockProc = MagicMock()
        mockProcess.return_value = mockProc
        
        result = killProcessOnPort(8000)
        
        mockProc.terminate.assert_called_once()

    @patch("fastapi_launcher.port.getPortInfo")
    @patch("fastapi_launcher.port.psutil.Process")
    def test_kill_process_force(self, mockProcess: MagicMock, mockGetPort: MagicMock) -> None:
        """Test force killing process."""
        from fastapi_launcher.port import killProcessOnPort
        
        mockGetPort.return_value = MagicMock(pid=12345)
        mockProc = MagicMock()
        mockProcess.return_value = mockProc
        
        result = killProcessOnPort(8000, force=True)
        
        mockProc.kill.assert_called_once()

    @patch("fastapi_launcher.port.getPortInfo")
    @patch("fastapi_launcher.port.psutil.Process")
    def test_kill_process_no_such_process(self, mockProcess: MagicMock, mockGetPort: MagicMock) -> None:
        """Test killing when process no longer exists."""
        from fastapi_launcher.port import killProcessOnPort
        import psutil as ps
        
        mockGetPort.return_value = MagicMock(pid=12345)
        mockProcess.side_effect = ps.NoSuchProcess(12345)
        
        result = killProcessOnPort(8000)
        assert result is False


class TestGetPortInfoExtended:
    """Extended tests for getPortInfo."""

    @patch("fastapi_launcher.port.psutil.net_connections")
    def test_get_info_access_denied(self, mockConnections: MagicMock) -> None:
        """Test getPortInfo with access denied."""
        import psutil as ps
        
        mockConnections.side_effect = ps.AccessDenied()
        
        with patch("fastapi_launcher.port.isPortInUse") as mockInUse:
            mockInUse.return_value = True
            info = getPortInfo(8000)
            
            assert info.status == "occupied"

    @patch("fastapi_launcher.port.psutil.net_connections")
    def test_get_info_no_listening(self, mockConnections: MagicMock) -> None:
        """Test getPortInfo when port not listening."""
        mockConnections.return_value = []
        
        info = getPortInfo(8000)
        
        assert info.pid is None
