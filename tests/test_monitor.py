"""Tests for monitor module."""

from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fastapi_launcher.monitor import (
    _buildStatusTable,
    _buildWorkerTable,
    _formatUptime,
    checkTextualInstalled,
)
from fastapi_launcher.process import ProcessStatus, WorkerStatus


class TestFormatUptime:
    """Tests for _formatUptime function."""

    def test_format_none(self) -> None:
        """Test formatting None uptime."""
        assert _formatUptime(None) == "N/A"

    def test_format_seconds(self) -> None:
        """Test formatting seconds."""
        result = _formatUptime(timedelta(seconds=45))
        assert result == "45s"

    def test_format_minutes(self) -> None:
        """Test formatting minutes."""
        result = _formatUptime(timedelta(minutes=5, seconds=30))
        assert result == "5m 30s"

    def test_format_hours(self) -> None:
        """Test formatting hours."""
        result = _formatUptime(timedelta(hours=2, minutes=30, seconds=15))
        assert result == "2h 30m 15s"

    def test_format_days(self) -> None:
        """Test formatting days."""
        result = _formatUptime(timedelta(days=3, hours=4, minutes=5))
        assert result == "3d 4h 5m"


class TestBuildStatusTable:
    """Tests for _buildStatusTable function."""

    def test_build_running_status_table(self) -> None:
        """Test building status table for running server."""
        masterStatus = ProcessStatus(
            pid=1234,
            isRunning=True,
            name="python",
            memoryMb=100.5,
            cpuPercent=5.2,
            uptime=timedelta(hours=1, minutes=30),
        )
        workerStatuses = [
            WorkerStatus(
                pid=1235,
                cpuPercent=2.0,
                memoryMb=50.0,
                requestsHandled=100,
                status="running",
                uptime=timedelta(hours=1),
            ),
        ]
        
        class MockConfig:
            host = "127.0.0.1"
            port = 8000
        
        table = _buildStatusTable(masterStatus, workerStatuses, MockConfig())
        
        # Should not raise
        assert table is not None
        assert table.title == "FastAPI Launcher Monitor"

    def test_build_stopped_status_table(self) -> None:
        """Test building status table for stopped server."""
        masterStatus = ProcessStatus(
            pid=0,
            isRunning=False,
        )
        
        class MockConfig:
            host = "127.0.0.1"
            port = 8000
        
        table = _buildStatusTable(masterStatus, [], MockConfig())
        
        assert table is not None


class TestBuildWorkerTable:
    """Tests for _buildWorkerTable function."""

    def test_build_worker_table_with_workers(self) -> None:
        """Test building worker table with workers."""
        workerStatuses = [
            WorkerStatus(
                pid=1001,
                cpuPercent=5.0,
                memoryMb=100.0,
                requestsHandled=50,
                status="running",
                uptime=timedelta(minutes=30),
            ),
            WorkerStatus(
                pid=1002,
                cpuPercent=0.1,
                memoryMb=80.0,
                requestsHandled=10,
                status="idle",
                uptime=timedelta(minutes=30),
            ),
        ]
        
        table = _buildWorkerTable(workerStatuses)
        
        assert table is not None
        assert table.title == "Workers"

    def test_build_worker_table_empty(self) -> None:
        """Test building worker table with no workers."""
        table = _buildWorkerTable([])
        
        assert table is not None


class TestCheckTextualInstalled:
    """Tests for checkTextualInstalled function."""

    def test_textual_installed(self) -> None:
        """Test detection when textual is installed."""
        # This test may pass or fail depending on environment
        # Just verify the function runs without error
        result = checkTextualInstalled()
        assert isinstance(result, bool)


class TestRunMonitorSimple:
    """Tests for runMonitorSimple function."""

    @pytest.mark.timeout(5)
    def test_run_monitor_simple_not_running(self, tempDir: Path) -> None:
        """Test simple monitor when server not running."""
        from fastapi_launcher.monitor import runMonitorSimple
        
        # Create mock runtime dir structure
        runtimeDir = tempDir / "runtime"
        runtimeDir.mkdir(parents=True, exist_ok=True)
        
        # Mock Live to immediately exit
        mockLiveInstance = MagicMock()
        mockLiveInstance.__enter__ = MagicMock(return_value=mockLiveInstance)
        mockLiveInstance.__exit__ = MagicMock(return_value=False)
        
        with patch("fastapi_launcher.monitor.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.monitor.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.monitor.console") as mockConsole, \
             patch("fastapi_launcher.monitor.Live", return_value=mockLiveInstance), \
             patch("fastapi_launcher.monitor.time.sleep", side_effect=KeyboardInterrupt):
            
            mockLoadConfig.return_value = MagicMock(runtimeDir=runtimeDir)
            mockReadPid.return_value = None
            
            # Should not hang - KeyboardInterrupt raised on first sleep
            runMonitorSimple(tempDir)

    @pytest.mark.timeout(5)
    def test_run_monitor_simple_running(self, tempDir: Path) -> None:
        """Test simple monitor when server is running."""
        from fastapi_launcher.monitor import runMonitorSimple
        
        # Create mock runtime dir structure
        runtimeDir = tempDir / "runtime"
        runtimeDir.mkdir(parents=True, exist_ok=True)
        
        # Mock Live to immediately exit
        mockLiveInstance = MagicMock()
        mockLiveInstance.__enter__ = MagicMock(return_value=mockLiveInstance)
        mockLiveInstance.__exit__ = MagicMock(return_value=False)
        
        with patch("fastapi_launcher.monitor.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.monitor.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.monitor.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.monitor.getProcessStatus") as mockGetStatus, \
             patch("fastapi_launcher.monitor.getWorkerStatuses") as mockGetWorkers, \
             patch("fastapi_launcher.monitor.console") as mockConsole, \
             patch("fastapi_launcher.monitor.Live", return_value=mockLiveInstance), \
             patch("fastapi_launcher.monitor.time.sleep", side_effect=KeyboardInterrupt):
            
            mockLoadConfig.return_value = MagicMock(
                runtimeDir=runtimeDir,
                host="127.0.0.1",
                port=8000
            )
            mockReadPid.return_value = 12345
            mockIsRunning.return_value = True
            mockGetStatus.return_value = ProcessStatus(pid=12345, isRunning=True, cpuPercent=5.0, memoryMb=100.0)
            mockGetWorkers.return_value = [
                WorkerStatus(pid=1001, cpuPercent=2.0, memoryMb=50.0, requestsHandled=10, status="running")
            ]
            
            # Should not hang - KeyboardInterrupt raised on first sleep
            runMonitorSimple(tempDir)


class TestGetMasterAndWorkerStatusFromProcess:
    """Tests for getMasterAndWorkerStatus from process module."""

    def test_get_status(self) -> None:
        """Test getting master and worker status."""
        with patch("fastapi_launcher.process.getProcessStatus") as mockGetStatus, \
             patch("fastapi_launcher.process.getWorkerStatuses") as mockGetWorkers:
            
            mockGetStatus.return_value = ProcessStatus(pid=12345, isRunning=True)
            mockGetWorkers.return_value = []
            
            from fastapi_launcher.process import getMasterAndWorkerStatus
            master, workers = getMasterAndWorkerStatus(12345)
            
            assert master.pid == 12345
            assert master.isRunning is True


class TestBuildStatusTableEdgeCases:
    """Tests for edge cases in _buildStatusTable."""

    def test_build_status_table_with_zero_values(self) -> None:
        """Test building status table with zero values."""
        masterStatus = ProcessStatus(
            pid=1234,
            isRunning=True,
            name="python",
            memoryMb=0.0,
            cpuPercent=0.0,
        )
        
        class MockConfig:
            host = "0.0.0.0"
            port = 80
        
        table = _buildStatusTable(masterStatus, [], MockConfig())
        
        assert table is not None

    def test_build_status_table_with_high_values(self) -> None:
        """Test building status table with high values."""
        masterStatus = ProcessStatus(
            pid=999999,
            isRunning=True,
            name="python",
            memoryMb=16384.0,
            cpuPercent=800.0,  # 8 cores
            uptime=timedelta(days=365),
        )
        workerStatuses = [
            WorkerStatus(
                pid=i,
                cpuPercent=100.0,
                memoryMb=1024.0,
                requestsHandled=1000000,
                status="running",
                uptime=timedelta(days=365),
            )
            for i in range(8)
        ]
        
        class MockConfig:
            host = "0.0.0.0"
            port = 8080
        
        table = _buildStatusTable(masterStatus, workerStatuses, MockConfig())
        
        assert table is not None


class TestBuildWorkerTableEdgeCases:
    """Tests for edge cases in _buildWorkerTable."""

    def test_build_worker_table_mixed_status(self) -> None:
        """Test building worker table with mixed statuses."""
        workerStatuses = [
            WorkerStatus(pid=1, cpuPercent=100.0, memoryMb=100.0, requestsHandled=0, status="running"),
            WorkerStatus(pid=2, cpuPercent=0.0, memoryMb=50.0, requestsHandled=100, status="idle"),
            WorkerStatus(pid=3, cpuPercent=50.0, memoryMb=75.0, requestsHandled=50, status="running"),
        ]
        
        table = _buildWorkerTable(workerStatuses)
        
        assert table is not None

    def test_build_worker_table_none_uptime(self) -> None:
        """Test building worker table with None uptime."""
        workerStatuses = [
            WorkerStatus(pid=1, cpuPercent=5.0, memoryMb=100.0, requestsHandled=0, status="running", uptime=None),
        ]
        
        table = _buildWorkerTable(workerStatuses)
        
        assert table is not None
