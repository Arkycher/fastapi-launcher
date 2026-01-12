"""Tests for process management utilities."""

import os
import signal
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import psutil
import pytest

from fastapi_launcher.process import (
    ProcessStatus,
    getChildProcesses,
    getProcessStatus,
    isProcessRunning,
    killProcess,
    readPidFile,
    registerSignalHandlers,
    removePidFile,
    sendSignal,
    terminateProcess,
    waitForExit,
    writePidFile,
)


class TestPidFile:
    """Tests for PID file operations."""

    def test_write_pid_file(self, tempDir: Path) -> None:
        """Test writing PID file."""
        pidPath = tempDir / "test.pid"
        writePidFile(pidPath, 12345)
        
        assert pidPath.exists()
        assert pidPath.read_text() == "12345"

    def test_write_pid_file_current_process(self, tempDir: Path) -> None:
        """Test writing current process PID."""
        pidPath = tempDir / "test.pid"
        writePidFile(pidPath)
        
        assert pidPath.read_text() == str(os.getpid())

    def test_write_pid_file_creates_parent(self, tempDir: Path) -> None:
        """Test that parent directories are created."""
        pidPath = tempDir / "subdir" / "nested" / "test.pid"
        writePidFile(pidPath, 12345)
        
        assert pidPath.exists()

    def test_read_pid_file(self, tempDir: Path) -> None:
        """Test reading PID file."""
        pidPath = tempDir / "test.pid"
        pidPath.write_text("12345")
        
        pid = readPidFile(pidPath)
        assert pid == 12345

    def test_read_pid_file_not_exists(self, tempDir: Path) -> None:
        """Test reading non-existent PID file."""
        pidPath = tempDir / "nonexistent.pid"
        
        pid = readPidFile(pidPath)
        assert pid is None

    def test_read_pid_file_invalid(self, tempDir: Path) -> None:
        """Test reading invalid PID file."""
        pidPath = tempDir / "test.pid"
        pidPath.write_text("not a number")
        
        pid = readPidFile(pidPath)
        assert pid is None

    def test_remove_pid_file(self, tempDir: Path) -> None:
        """Test removing PID file."""
        pidPath = tempDir / "test.pid"
        pidPath.write_text("12345")
        
        result = removePidFile(pidPath)
        
        assert result is True
        assert not pidPath.exists()

    def test_remove_pid_file_not_exists(self, tempDir: Path) -> None:
        """Test removing non-existent PID file."""
        pidPath = tempDir / "nonexistent.pid"
        
        result = removePidFile(pidPath)
        assert result is False


class TestProcessRunning:
    """Tests for process running detection."""

    def test_current_process_running(self) -> None:
        """Test that current process is detected as running."""
        assert isProcessRunning(os.getpid()) is True

    def test_invalid_pid(self) -> None:
        """Test that invalid PIDs return False."""
        assert isProcessRunning(-1) is False
        assert isProcessRunning(0) is False

    def test_nonexistent_pid(self) -> None:
        """Test that non-existent PIDs return False."""
        # Use a very high PID that's unlikely to exist
        assert isProcessRunning(9999999) is False


class TestProcessStatus:
    """Tests for getting process status."""

    def test_get_current_process_status(self) -> None:
        """Test getting status of current process."""
        status = getProcessStatus(os.getpid())
        
        assert status.pid == os.getpid()
        assert status.isRunning is True
        assert status.name is not None
        assert status.startTime is not None
        assert status.uptime is not None

    def test_get_nonexistent_process_status(self) -> None:
        """Test getting status of non-existent process."""
        status = getProcessStatus(9999999)
        
        assert status.isRunning is False

    def test_status_has_memory_info(self) -> None:
        """Test that status includes memory info."""
        status = getProcessStatus(os.getpid())
        
        assert status.memoryMb is not None
        assert status.memoryMb > 0


class TestSignals:
    """Tests for signal handling."""

    def test_send_signal_to_self(self) -> None:
        """Test sending signal to self (we can't actually kill ourselves)."""
        # This is tricky to test without killing the test process
        pass

    @patch("fastapi_launcher.process.os.kill")
    def test_send_signal_success(self, mockKill: MagicMock) -> None:
        """Test successful signal sending."""
        result = sendSignal(12345, signal.SIGTERM)
        
        assert result is True
        mockKill.assert_called_once_with(12345, signal.SIGTERM)

    @patch("fastapi_launcher.process.os.kill")
    def test_send_signal_failure(self, mockKill: MagicMock) -> None:
        """Test signal sending failure."""
        mockKill.side_effect = ProcessLookupError()
        
        result = sendSignal(12345, signal.SIGTERM)
        assert result is False


class TestTerminateProcess:
    """Tests for process termination."""

    @patch("fastapi_launcher.process.isProcessRunning")
    def test_terminate_not_running(self, mockRunning: MagicMock) -> None:
        """Test terminating non-running process."""
        mockRunning.return_value = False
        
        result = terminateProcess(12345)
        assert result is True

    @patch("fastapi_launcher.process.psutil.Process")
    @patch("fastapi_launcher.process.isProcessRunning")
    def test_terminate_success(
        self, mockRunning: MagicMock, mockProcess: MagicMock
    ) -> None:
        """Test successful termination."""
        mockRunning.return_value = True
        mockProc = MagicMock()
        mockProcess.return_value = mockProc
        
        result = terminateProcess(12345, timeout=1.0)
        
        mockProc.terminate.assert_called_once()


class TestKillProcess:
    """Tests for force killing process."""

    @patch("fastapi_launcher.process.isProcessRunning")
    def test_kill_not_running(self, mockRunning: MagicMock) -> None:
        """Test killing non-running process."""
        mockRunning.return_value = False
        
        result = killProcess(12345)
        assert result is True


class TestWaitForExit:
    """Tests for waiting for process exit."""

    @patch("fastapi_launcher.process.psutil.Process")
    def test_wait_already_exited(self, mockProcess: MagicMock) -> None:
        """Test waiting for already exited process."""
        mockProcess.side_effect = psutil.NoSuchProcess(12345)
        
        result = waitForExit(12345, timeout=1.0)
        assert result is True

    @patch("fastapi_launcher.process.psutil.Process")
    def test_wait_timeout(self, mockProcess: MagicMock) -> None:
        """Test timeout while waiting."""
        mockProc = MagicMock()
        mockProc.wait.side_effect = psutil.TimeoutExpired(1.0)
        mockProcess.return_value = mockProc
        
        result = waitForExit(12345, timeout=0.1)
        assert result is False


class TestChildProcesses:
    """Tests for child process handling."""

    def test_get_child_processes_none(self) -> None:
        """Test getting children of process with no children."""
        # Current process likely has no children during testing
        children = getChildProcesses(os.getpid())
        
        # Should return a list (may be empty)
        assert isinstance(children, list)

    @patch("fastapi_launcher.process.psutil.Process")
    def test_get_children_success(self, mockProcess: MagicMock) -> None:
        """Test getting child processes."""
        mockChild1 = MagicMock()
        mockChild1.pid = 1001
        mockChild2 = MagicMock()
        mockChild2.pid = 1002
        
        mockProc = MagicMock()
        mockProc.children.return_value = [mockChild1, mockChild2]
        mockProcess.return_value = mockProc
        
        children = getChildProcesses(12345)
        
        assert children == [1001, 1002]


class TestSignalHandlers:
    """Tests for signal handler registration."""

    def test_register_handlers(self) -> None:
        """Test registering signal handlers."""
        # Just verify it doesn't raise
        registerSignalHandlers()

    def test_register_custom_handlers(self) -> None:
        """Test registering custom handlers."""
        handler_called = []
        
        def customHandler(signum, frame):
            handler_called.append(signum)
        
        registerSignalHandlers(onInterrupt=customHandler)
        
        # We can't easily test signal handling without sending signals


class TestTerminateProcessTree:
    """Tests for terminating process tree."""

    @patch("fastapi_launcher.process.isProcessRunning")
    def test_terminate_not_running(self, mockRunning: MagicMock) -> None:
        """Test terminating non-running process."""
        from fastapi_launcher.process import terminateProcessTree
        
        mockRunning.return_value = False
        
        result = terminateProcessTree(12345)
        assert result is True

    @patch("fastapi_launcher.process.psutil.Process")
    @patch("fastapi_launcher.process.psutil.wait_procs")
    @patch("fastapi_launcher.process.isProcessRunning")
    def test_terminate_tree_success(
        self, mockRunning: MagicMock, mockWaitProcs: MagicMock, mockProcess: MagicMock
    ) -> None:
        """Test terminating process tree successfully."""
        from fastapi_launcher.process import terminateProcessTree
        
        mockRunning.return_value = True
        
        mockChild = MagicMock()
        mockProc = MagicMock()
        mockProc.children.return_value = [mockChild]
        mockProcess.return_value = mockProc
        
        mockWaitProcs.return_value = ([mockProc, mockChild], [])
        
        result = terminateProcessTree(12345, timeout=1.0)
        
        mockProc.terminate.assert_called_once()
        mockChild.terminate.assert_called_once()


class TestProcessStatusDataclass:
    """Tests for ProcessStatus dataclass."""

    def test_process_status_fields(self) -> None:
        """Test ProcessStatus has all fields."""
        from fastapi_launcher.process import ProcessStatus
        from datetime import datetime, timedelta
        
        status = ProcessStatus(
            pid=1234,
            isRunning=True,
            name="python",
            cmdline="python main.py",
            memoryMb=128.5,
            cpuPercent=5.0,
            startTime=datetime.now(),
            uptime=timedelta(hours=1),
        )
        
        assert status.pid == 1234
        assert status.isRunning is True
        assert status.name == "python"
        assert status.memoryMb == 128.5


class TestSendSignal:
    """Additional tests for sendSignal."""

    @patch("fastapi_launcher.process.os.kill")
    def test_send_permission_error(self, mockKill: MagicMock) -> None:
        """Test signal sending with permission error."""
        mockKill.side_effect = PermissionError()
        
        result = sendSignal(12345, signal.SIGTERM)
        assert result is False

    @patch("fastapi_launcher.process.os.kill")
    def test_send_os_error(self, mockKill: MagicMock) -> None:
        """Test signal sending with OS error."""
        mockKill.side_effect = OSError()
        
        result = sendSignal(12345, signal.SIGTERM)
        assert result is False


class TestWaitForExit:
    """Tests for waiting for process exit."""

    @patch("fastapi_launcher.process.isProcessRunning")
    def test_wait_process_already_exited(self, mockRunning: MagicMock) -> None:
        """Test waiting for process that's already exited."""
        from fastapi_launcher.process import waitForExit
        
        mockRunning.return_value = False
        
        result = waitForExit(12345, timeout=1.0)
        assert result is True

    @patch("fastapi_launcher.process.isProcessRunning")
    def test_wait_process_exits(self, mockRunning: MagicMock) -> None:
        """Test waiting for process that exits."""
        from fastapi_launcher.process import waitForExit
        
        # Returns True first (running), then False (exited)
        mockRunning.side_effect = [True, True, False]
        
        result = waitForExit(12345, timeout=2.0)
        assert result is True


class TestTerminateProcess:
    """Tests for terminateProcess."""

    @patch("fastapi_launcher.process.isProcessRunning")
    @patch("fastapi_launcher.process.sendSignal")
    def test_terminate_not_running(self, mockSend: MagicMock, mockRunning: MagicMock) -> None:
        """Test terminate process that's not running."""
        from fastapi_launcher.process import terminateProcess
        
        mockRunning.return_value = False
        
        result = terminateProcess(12345)
        assert result is True

    @patch("fastapi_launcher.process.isProcessRunning")
    @patch("fastapi_launcher.process.sendSignal")
    @patch("fastapi_launcher.process.waitForExit")
    def test_terminate_graceful(
        self, mockWait: MagicMock, mockSend: MagicMock, mockRunning: MagicMock
    ) -> None:
        """Test graceful process termination."""
        from fastapi_launcher.process import terminateProcess
        
        # First call returns True (running), subsequent calls return False (exited)
        mockRunning.side_effect = [True, False]
        mockSend.return_value = True
        mockWait.return_value = True
        
        result = terminateProcess(12345)
        
        assert result is True

    @patch("fastapi_launcher.process.isProcessRunning")
    @patch("fastapi_launcher.process.sendSignal")
    @patch("fastapi_launcher.process.waitForExit")
    def test_terminate_force(
        self, mockWait: MagicMock, mockSend: MagicMock, mockRunning: MagicMock
    ) -> None:
        """Test force process termination."""
        from fastapi_launcher.process import terminateProcess
        
        mockRunning.return_value = True
        mockSend.return_value = True
        mockWait.side_effect = [False, True]  # First wait times out, second succeeds
        
        result = terminateProcess(12345, timeout=0.5)
