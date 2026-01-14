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
    WorkerStatus,
    getChildProcesses,
    getMasterAndWorkerStatus,
    getProcessStatus,
    getWorkerStatuses,
    isProcessRunning,
    killProcess,
    readPidFile,
    registerSignalHandlers,
    removePidFile,
    sendSignal,
    terminateProcess,
    terminateProcessTree,
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


class TestWorkerStatus:
    """Tests for WorkerStatus dataclass."""

    def test_worker_status_fields(self) -> None:
        """Test WorkerStatus has all fields."""
        from datetime import timedelta
        
        status = WorkerStatus(
            pid=1234,
            cpuPercent=5.0,
            memoryMb=128.5,
            requestsHandled=100,
            status="running",
            uptime=timedelta(hours=1),
        )
        
        assert status.pid == 1234
        assert status.cpuPercent == 5.0
        assert status.memoryMb == 128.5
        assert status.requestsHandled == 100
        assert status.status == "running"

    def test_worker_status_optional_uptime(self) -> None:
        """Test WorkerStatus with no uptime."""
        status = WorkerStatus(
            pid=1234,
            cpuPercent=5.0,
            memoryMb=128.5,
            requestsHandled=0,
            status="idle",
        )
        
        assert status.uptime is None


class TestGetWorkerStatuses:
    """Tests for getWorkerStatuses function."""

    @patch("fastapi_launcher.process.psutil.Process")
    def test_get_worker_statuses_no_children(self, mockProcess: MagicMock) -> None:
        """Test getting worker statuses when there are no children."""
        mockProc = MagicMock()
        mockProc.children.return_value = []
        mockProcess.return_value = mockProc
        
        workers = getWorkerStatuses(12345)
        
        assert workers == []

    @patch("fastapi_launcher.process.psutil.Process")
    def test_get_worker_statuses_with_children(self, mockProcess: MagicMock) -> None:
        """Test getting worker statuses with child processes."""
        from datetime import datetime
        
        mockChild = MagicMock()
        mockChild.pid = 1001
        mockChild.cpu_percent.return_value = 5.0
        mockChild.memory_info.return_value = MagicMock(rss=100 * 1024 * 1024)  # 100 MB
        mockChild.create_time.return_value = datetime.now().timestamp() - 3600
        
        mockProc = MagicMock()
        mockProc.children.return_value = [mockChild]
        mockProcess.return_value = mockProc
        
        workers = getWorkerStatuses(12345)
        
        assert len(workers) == 1
        assert workers[0].pid == 1001
        assert workers[0].memoryMb == pytest.approx(100.0, rel=0.1)

    @patch("fastapi_launcher.process.psutil.Process")
    def test_get_worker_statuses_process_not_found(self, mockProcess: MagicMock) -> None:
        """Test getting worker statuses when main process not found."""
        mockProcess.side_effect = psutil.NoSuchProcess(12345)
        
        workers = getWorkerStatuses(12345)
        
        assert workers == []

    @patch("fastapi_launcher.process.psutil.Process")
    def test_get_worker_statuses_child_access_denied(self, mockProcess: MagicMock) -> None:
        """Test getting worker statuses when child access is denied."""
        mockChild = MagicMock()
        mockChild.pid = 1001
        mockChild.cpu_percent.side_effect = psutil.AccessDenied(1001)
        
        mockProc = MagicMock()
        mockProc.children.return_value = [mockChild]
        mockProcess.return_value = mockProc
        
        workers = getWorkerStatuses(12345)
        
        # Should skip the inaccessible child
        assert workers == []

    @patch("fastapi_launcher.process.psutil.Process")
    def test_get_worker_status_running(self, mockProcess: MagicMock) -> None:
        """Test worker status is 'running' when CPU usage is high."""
        from datetime import datetime
        
        mockChild = MagicMock()
        mockChild.pid = 1001
        mockChild.cpu_percent.return_value = 50.0  # High CPU
        mockChild.memory_info.return_value = MagicMock(rss=100 * 1024 * 1024)
        mockChild.create_time.return_value = datetime.now().timestamp() - 3600
        
        mockProc = MagicMock()
        mockProc.children.return_value = [mockChild]
        mockProcess.return_value = mockProc
        
        workers = getWorkerStatuses(12345)
        
        assert workers[0].status == "running"

    @patch("fastapi_launcher.process.psutil.Process")
    def test_get_worker_status_idle(self, mockProcess: MagicMock) -> None:
        """Test worker status is 'idle' when CPU usage is low."""
        from datetime import datetime
        
        mockChild = MagicMock()
        mockChild.pid = 1001
        mockChild.cpu_percent.return_value = 0.1  # Low CPU
        mockChild.memory_info.return_value = MagicMock(rss=100 * 1024 * 1024)
        mockChild.create_time.return_value = datetime.now().timestamp() - 3600
        
        mockProc = MagicMock()
        mockProc.children.return_value = [mockChild]
        mockProcess.return_value = mockProc
        
        workers = getWorkerStatuses(12345)
        
        assert workers[0].status == "idle"


class TestGetMasterAndWorkerStatus:
    """Tests for getMasterAndWorkerStatus function."""

    @patch("fastapi_launcher.process.getWorkerStatuses")
    @patch("fastapi_launcher.process.getProcessStatus")
    def test_get_master_and_worker_status_running(
        self, mockGetStatus: MagicMock, mockGetWorkers: MagicMock
    ) -> None:
        """Test getting master and worker status when running."""
        mockMasterStatus = ProcessStatus(pid=12345, isRunning=True)
        mockGetStatus.return_value = mockMasterStatus
        
        mockWorkers = [
            WorkerStatus(pid=1001, cpuPercent=5.0, memoryMb=100.0, requestsHandled=0, status="running"),
        ]
        mockGetWorkers.return_value = mockWorkers
        
        master, workers = getMasterAndWorkerStatus(12345)
        
        assert master.pid == 12345
        assert master.isRunning is True
        assert len(workers) == 1
        assert workers[0].pid == 1001

    @patch("fastapi_launcher.process.getWorkerStatuses")
    @patch("fastapi_launcher.process.getProcessStatus")
    def test_get_master_and_worker_status_not_running(
        self, mockGetStatus: MagicMock, mockGetWorkers: MagicMock
    ) -> None:
        """Test getting master and worker status when not running."""
        mockMasterStatus = ProcessStatus(pid=12345, isRunning=False)
        mockGetStatus.return_value = mockMasterStatus
        
        master, workers = getMasterAndWorkerStatus(12345)
        
        assert master.isRunning is False
        assert workers == []
        # getWorkerStatuses should not be called when not running
        mockGetWorkers.assert_not_called()


class TestTerminateProcessTreeAdditional:
    """Additional tests for terminateProcessTree."""

    @patch("fastapi_launcher.process.psutil.Process")
    @patch("fastapi_launcher.process.isProcessRunning")
    def test_terminate_tree_with_no_children(
        self, mockRunning: MagicMock, mockProcess: MagicMock
    ) -> None:
        """Test terminating process tree with no children."""
        mockRunning.return_value = True
        
        mockProc = MagicMock()
        mockProc.children.return_value = []
        mockProcess.return_value = mockProc
        
        # Simulate wait_procs returning all processes terminated
        with patch("fastapi_launcher.process.psutil.wait_procs") as mockWaitProcs:
            mockWaitProcs.return_value = ([mockProc], [])
            
            result = terminateProcessTree(12345, timeout=1.0)
            
            mockProc.terminate.assert_called_once()

    @patch("fastapi_launcher.process.psutil.Process")
    @patch("fastapi_launcher.process.isProcessRunning")
    def test_terminate_tree_access_denied(
        self, mockRunning: MagicMock, mockProcess: MagicMock
    ) -> None:
        """Test terminating process tree with access denied."""
        mockRunning.return_value = True
        mockProcess.side_effect = psutil.AccessDenied(12345)
        
        result = terminateProcessTree(12345, timeout=1.0)
        
        # Should return based on isProcessRunning after exception


class TestKillProcessAdditional:
    """Additional tests for killProcess."""

    @patch("fastapi_launcher.process.psutil.Process")
    @patch("fastapi_launcher.process.isProcessRunning")
    def test_kill_process_success(
        self, mockRunning: MagicMock, mockProcess: MagicMock
    ) -> None:
        """Test killing process successfully."""
        mockRunning.return_value = True
        
        mockProc = MagicMock()
        mockProcess.return_value = mockProc
        
        result = killProcess(12345)
        
        mockProc.kill.assert_called_once()

    @patch("fastapi_launcher.process.psutil.Process")
    @patch("fastapi_launcher.process.isProcessRunning")
    def test_kill_process_no_such_process(
        self, mockRunning: MagicMock, mockProcess: MagicMock
    ) -> None:
        """Test killing process that doesn't exist."""
        mockRunning.return_value = True
        mockProcess.side_effect = psutil.NoSuchProcess(12345)
        
        result = killProcess(12345)
        
        # Should return True since process doesn't exist (already dead)
