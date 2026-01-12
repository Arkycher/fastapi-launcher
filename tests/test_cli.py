"""Tests for CLI commands."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from fastapi_launcher.cli import app


runner = CliRunner()


class TestVersionCommand:
    """Tests for version command."""

    def test_version_flag(self) -> None:
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        
        assert result.exit_code == 0
        assert "FastAPI Launcher" in result.output

    def test_version_short_flag(self) -> None:
        """Test -v flag."""
        result = runner.invoke(app, ["-v"])
        
        assert result.exit_code == 0


class TestDevCommand:
    """Tests for dev command."""

    @patch("fastapi_launcher.cli.launch")
    def test_dev_default_options(self, mockLaunch: MagicMock, mockProjectDir: Path) -> None:
        """Test dev command with defaults."""
        os.chdir(mockProjectDir)
        
        result = runner.invoke(app, ["dev"])
        
        # May fail due to app discovery, but launch should be attempted
        mockLaunch.assert_called_once()
        callArgs = mockLaunch.call_args
        assert callArgs.kwargs["cliArgs"]["reload"] is True

    @patch("fastapi_launcher.cli.launch")
    def test_dev_custom_port(self, mockLaunch: MagicMock, mockProjectDir: Path) -> None:
        """Test dev command with custom port."""
        os.chdir(mockProjectDir)
        
        result = runner.invoke(app, ["dev", "--port", "9000"])
        
        mockLaunch.assert_called_once()
        callArgs = mockLaunch.call_args
        assert callArgs.kwargs["cliArgs"]["port"] == 9000

    @patch("fastapi_launcher.cli.launch")
    def test_dev_no_reload(self, mockLaunch: MagicMock, mockProjectDir: Path) -> None:
        """Test dev command without reload."""
        os.chdir(mockProjectDir)
        
        result = runner.invoke(app, ["dev", "--no-reload"])
        
        mockLaunch.assert_called_once()
        callArgs = mockLaunch.call_args
        assert callArgs.kwargs["cliArgs"]["reload"] is False


class TestStartCommand:
    """Tests for start command."""

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_start_default_options(
        self, mockLoadConfig: MagicMock, mockLaunch: MagicMock
    ) -> None:
        """Test start command with defaults."""
        mockLoadConfig.return_value = MagicMock(runtimeDir=Path("runtime"))
        
        result = runner.invoke(app, ["start"])
        
        mockLaunch.assert_called_once()
        callArgs = mockLaunch.call_args
        assert callArgs.kwargs["cliArgs"]["workers"] == 4

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_start_custom_workers(
        self, mockLoadConfig: MagicMock, mockLaunch: MagicMock
    ) -> None:
        """Test start command with custom workers."""
        mockLoadConfig.return_value = MagicMock(runtimeDir=Path("runtime"))
        
        result = runner.invoke(app, ["start", "--workers", "8"])
        
        mockLaunch.assert_called_once()
        callArgs = mockLaunch.call_args
        assert callArgs.kwargs["cliArgs"]["workers"] == 8


class TestStopCommand:
    """Tests for stop command."""

    def test_stop_no_pid_file(self, tempDir: Path) -> None:
        """Test stop when no PID file exists."""
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig:
            with patch("fastapi_launcher.cli.readPidFile") as mockReadPid:
                mockLoadConfig.return_value = MagicMock(runtimeDir=tempDir / "runtime")
                mockReadPid.return_value = None
                
                result = runner.invoke(app, ["stop"])
                
                assert result.exit_code == 1

    def test_stop_running_process(self, tempDir: Path) -> None:
        """Test stopping running process."""
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.cli.terminateProcess") as mockTerminate, \
             patch("fastapi_launcher.cli.removePidFile") as mockRemovePid, \
             patch("fastapi_launcher.cli.waitForPortFree") as mockWaitPort, \
             patch("fastapi_launcher.cli.createSpinner") as mockSpinner:
            
            mockLoadConfig.return_value = MagicMock(runtimeDir=tempDir / "runtime", port=8000)
            mockReadPid.return_value = 12345
            mockIsRunning.return_value = True
            mockTerminate.return_value = True
            mockWaitPort.return_value = True
            mockSpinner.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mockSpinner.return_value.__exit__ = MagicMock(return_value=False)
            
            result = runner.invoke(app, ["stop"])
            
            mockTerminate.assert_called_once()


class TestStatusCommand:
    """Tests for status command."""

    def test_status_not_running(self, tempDir: Path) -> None:
        """Test status when not running."""
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isPortInUse") as mockPortInUse, \
             patch("fastapi_launcher.cli.printStatusTable") as mockPrintStatus:
            
            mockLoadConfig.return_value = MagicMock(
                runtimeDir=tempDir / "runtime",
                host="127.0.0.1",
                port=8000,
            )
            mockReadPid.return_value = None
            mockPortInUse.return_value = False
            
            result = runner.invoke(app, ["status"])
            
            assert result.exit_code == 0
            mockPrintStatus.assert_called_once()


class TestLogsCommand:
    """Tests for logs command."""

    @patch("fastapi_launcher.cli.printLogEntry")
    @patch("fastapi_launcher.cli.readLogFile")
    @patch("fastapi_launcher.cli.getLogFiles")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_logs_default(
        self,
        mockLoadConfig: MagicMock,
        mockGetLogFiles: MagicMock,
        mockReadLog: MagicMock,
        mockPrintLog: MagicMock,
        tempDir: Path,
    ) -> None:
        """Test logs command."""
        logFile = tempDir / "logs" / "fa.log"
        logFile.parent.mkdir(parents=True, exist_ok=True)
        logFile.write_text("Test log line\n")
        
        mockLoadConfig.return_value = MagicMock(
            runtimeDir=tempDir,
            logFormat="pretty",
        )
        mockGetLogFiles.return_value = {"main": logFile, "access": logFile, "error": logFile}
        mockReadLog.return_value = iter(["Test log line"])
        
        result = runner.invoke(app, ["logs"])
        
        assert result.exit_code == 0

    @patch("fastapi_launcher.cli.getLogFiles")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_logs_invalid_type(
        self,
        mockLoadConfig: MagicMock,
        mockGetLogFiles: MagicMock,
    ) -> None:
        """Test logs with invalid type."""
        mockLoadConfig.return_value = MagicMock(runtimeDir=Path("runtime"))
        mockGetLogFiles.return_value = {"main": Path("fa.log")}
        
        result = runner.invoke(app, ["logs", "--type", "invalid"])
        
        assert result.exit_code == 1


class TestHealthCommand:
    """Tests for health command."""

    @patch("fastapi_launcher.cli.printHealthResult")
    @patch("fastapi_launcher.cli.checkHealth")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_health_success(
        self,
        mockLoadConfig: MagicMock,
        mockCheckHealth: MagicMock,
        mockPrintResult: MagicMock,
    ) -> None:
        """Test health check success."""
        from fastapi_launcher.health import HealthCheckResult
        
        mockLoadConfig.return_value = MagicMock(
            host="127.0.0.1",
            port=8000,
            healthPath="/health",
        )
        mockCheckHealth.return_value = HealthCheckResult(healthy=True, statusCode=200)
        
        result = runner.invoke(app, ["health"])
        
        assert result.exit_code == 0

    @patch("fastapi_launcher.cli.printHealthResult")
    @patch("fastapi_launcher.cli.checkHealth")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_health_failure(
        self,
        mockLoadConfig: MagicMock,
        mockCheckHealth: MagicMock,
        mockPrintResult: MagicMock,
    ) -> None:
        """Test health check failure."""
        from fastapi_launcher.health import HealthCheckResult
        
        mockLoadConfig.return_value = MagicMock(
            host="127.0.0.1",
            port=8000,
            healthPath="/health",
        )
        mockCheckHealth.return_value = HealthCheckResult(
            healthy=False, error="Connection refused"
        )
        
        result = runner.invoke(app, ["health"])
        
        assert result.exit_code == 1


class TestConfigCommand:
    """Tests for config command."""

    @patch("fastapi_launcher.cli.showConfig")
    def test_config_display(self, mockShowConfig: MagicMock) -> None:
        """Test config command."""
        result = runner.invoke(app, ["config"])
        
        assert result.exit_code == 0
        mockShowConfig.assert_called_once()


class TestCheckCommand:
    """Tests for check command."""

    @patch("fastapi_launcher.cli.printCheckReport")
    @patch("fastapi_launcher.cli.runAllChecks")
    def test_check_all_pass(
        self, mockRunChecks: MagicMock, mockPrintReport: MagicMock
    ) -> None:
        """Test check when all pass."""
        from fastapi_launcher.checker import CheckReport, CheckResult
        
        mockRunChecks.return_value = CheckReport(results=[
            CheckResult("Test", True, "OK"),
        ])
        
        result = runner.invoke(app, ["check"])
        
        assert result.exit_code == 0

    @patch("fastapi_launcher.cli.printCheckReport")
    @patch("fastapi_launcher.cli.runAllChecks")
    def test_check_some_fail(
        self, mockRunChecks: MagicMock, mockPrintReport: MagicMock
    ) -> None:
        """Test check when some fail."""
        from fastapi_launcher.checker import CheckReport, CheckResult
        
        mockRunChecks.return_value = CheckReport(results=[
            CheckResult("Test", False, "Failed"),
        ])
        
        result = runner.invoke(app, ["check"])
        
        assert result.exit_code == 1


class TestCleanCommand:
    """Tests for clean command."""

    @patch("fastapi_launcher.cli.loadConfig")
    def test_clean_no_runtime(self, mockLoadConfig: MagicMock, tempDir: Path) -> None:
        """Test clean when runtime dir doesn't exist."""
        mockLoadConfig.return_value = MagicMock(runtimeDir=tempDir / "nonexistent")
        
        result = runner.invoke(app, ["clean", "--yes"])
        
        assert result.exit_code == 0

    @patch("fastapi_launcher.cli.cleanLogs")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_clean_logs_only(
        self, mockLoadConfig: MagicMock, mockCleanLogs: MagicMock, tempDir: Path
    ) -> None:
        """Test clean logs only."""
        runtimeDir = tempDir / "runtime"
        runtimeDir.mkdir()
        
        mockLoadConfig.return_value = MagicMock(runtimeDir=runtimeDir)
        mockCleanLogs.return_value = 3
        
        result = runner.invoke(app, ["clean", "--logs", "--yes"])
        
        assert result.exit_code == 0
        mockCleanLogs.assert_called_once()

    def test_clean_requires_confirmation(self, tempDir: Path) -> None:
        """Test clean requires confirmation."""
        runtimeDir = tempDir / "runtime"
        runtimeDir.mkdir()
        
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig:
            mockLoadConfig.return_value = MagicMock(runtimeDir=runtimeDir)
            
            # Without --yes, should prompt and exit on "n"
            result = runner.invoke(app, ["clean"], input="n\n")
            
            # Should exit without error when user declines
            assert result.exit_code == 0


class TestRestartCommand:
    """Tests for restart command."""

    def test_restart_not_running(self, tempDir: Path) -> None:
        """Test restart when server not running."""
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.cli.launch") as mockLaunch:
            
            mockLoadConfig.return_value = MagicMock(
                runtimeDir=tempDir / "runtime",
                port=8000,
                mode=MagicMock(),
            )
            mockReadPid.return_value = None
            mockIsRunning.return_value = False
            
            result = runner.invoke(app, ["restart"])
            
            # Should still try to start
            mockLaunch.assert_called_once()

    def test_restart_running_server(self, tempDir: Path) -> None:
        """Test restart when server is running."""
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.cli.terminateProcess") as mockTerminate, \
             patch("fastapi_launcher.cli.removePidFile"), \
             patch("fastapi_launcher.cli.waitForPortFree") as mockWaitPort, \
             patch("fastapi_launcher.cli.setupDaemonLogging"), \
             patch("fastapi_launcher.cli.daemonize"), \
             patch("fastapi_launcher.cli.launch") as mockLaunch:
            
            mockLoadConfig.return_value = MagicMock(
                runtimeDir=tempDir / "runtime",
                port=8000,
                mode=MagicMock(),
            )
            mockReadPid.return_value = 12345
            mockIsRunning.return_value = True
            mockTerminate.return_value = True
            mockWaitPort.return_value = True
            
            result = runner.invoke(app, ["restart"])
            
            mockTerminate.assert_called_once()


class TestDevCommandExtended:
    """Extended tests for dev command."""

    @patch("fastapi_launcher.cli.launch")
    def test_dev_with_reload_dirs(self, mockLaunch: MagicMock) -> None:
        """Test dev command with reload dirs."""
        result = runner.invoke(app, ["dev", "--reload-dirs", "src,lib"])
        
        mockLaunch.assert_called_once()
        callKwargs = mockLaunch.call_args.kwargs
        assert callKwargs["cliArgs"]["reload_dirs"] == ["src", "lib"]

    @patch("fastapi_launcher.cli.launch")
    def test_dev_with_app_path(self, mockLaunch: MagicMock) -> None:
        """Test dev command with app path."""
        result = runner.invoke(app, ["dev", "--app", "mymodule:api"])
        
        mockLaunch.assert_called_once()
        callKwargs = mockLaunch.call_args.kwargs
        assert callKwargs["cliArgs"]["app"] == "mymodule:api"

    @patch("fastapi_launcher.cli.launch")
    def test_dev_keyboard_interrupt(self, mockLaunch: MagicMock) -> None:
        """Test dev command handles keyboard interrupt."""
        mockLaunch.side_effect = KeyboardInterrupt()
        
        result = runner.invoke(app, ["dev"])
        
        # Should exit gracefully
        assert result.exit_code == 0


class TestStartCommandExtended:
    """Extended tests for start command."""

    def test_start_with_daemon(self, tempDir: Path) -> None:
        """Test start command with daemon mode."""
        with patch("fastapi_launcher.cli.launch") as mockLaunch, \
             patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.checkDaemonSupport") as mockCheck, \
             patch("fastapi_launcher.cli.setupDaemonLogging") as mockSetupLog, \
             patch("fastapi_launcher.cli.daemonize") as mockDaemonize, \
             patch("fastapi_launcher.cli.Path") as mockPath:
            
            runtimeDir = MagicMock()
            runtimeDir.is_absolute.return_value = True
            runtimeDir.__truediv__ = MagicMock(return_value=tempDir / "fa.pid")
            
            mockLoadConfig.return_value = MagicMock(runtimeDir=runtimeDir)
            mockCheck.return_value = (True, "Supported")
            mockSetupLog.return_value = tempDir / "runtime/logs/fa.log"
            mockPath.cwd.return_value = tempDir
            
            result = runner.invoke(app, ["start", "--daemon"])
            
            # Daemon mode should be triggered
            mockCheck.assert_called_once()

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_start_daemon_not_supported(self, mockLoadConfig: MagicMock, mockLaunch: MagicMock) -> None:
        """Test start command when daemon not supported."""
        from pathlib import Path
        
        with patch("fastapi_launcher.cli.checkDaemonSupport") as mockCheck:
            mockLoadConfig.return_value = MagicMock(runtimeDir=Path("runtime"))
            mockCheck.return_value = (False, "Not supported on Windows")
            
            result = runner.invoke(app, ["start", "--daemon"])
            
            # Should still try to run

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_start_launch_error(self, mockLoadConfig: MagicMock, mockLaunch: MagicMock) -> None:
        """Test start command with launch error."""
        from fastapi_launcher.launcher import LaunchError
        from pathlib import Path
        
        mockLoadConfig.return_value = MagicMock(runtimeDir=Path("runtime"))
        mockLaunch.side_effect = LaunchError("Failed to start")
        
        result = runner.invoke(app, ["start"])
        
        assert result.exit_code == 1


class TestLogsCommand:
    """Tests for logs command."""

    def test_logs_with_lines(self, tempDir: Path) -> None:
        """Test logs command with line count."""
        logsDir = tempDir / "runtime" / "logs"
        logsDir.mkdir(parents=True)
        logFile = logsDir / "fa.log"
        logFile.write_text("\n".join(f"Line {i}" for i in range(100)))
        
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig:
            mockConfig = MagicMock()
            mockConfig.runtimeDir = tempDir / "runtime"
            mockConfig.logFormat = MagicMock()
            mockLoadConfig.return_value = mockConfig
            
            result = runner.invoke(app, ["logs", "--lines", "10"])
            
            # Should succeed and show last 10 lines


class TestCheckCommand:
    """Tests for check command."""

    @patch("fastapi_launcher.cli.runAllChecks")
    @patch("fastapi_launcher.cli.printCheckReport")
    def test_check_all_pass(self, mockPrint: MagicMock, mockRun: MagicMock) -> None:
        """Test check command when all pass."""
        from fastapi_launcher.checker import CheckReport, CheckResult
        
        mockRun.return_value = CheckReport(results=[
            CheckResult("Test", True, "OK")
        ])
        
        result = runner.invoke(app, ["check"])
        
        assert result.exit_code == 0

    @patch("fastapi_launcher.cli.runAllChecks")
    @patch("fastapi_launcher.cli.printCheckReport")
    def test_check_with_failures(self, mockPrint: MagicMock, mockRun: MagicMock) -> None:
        """Test check command with failures."""
        from fastapi_launcher.checker import CheckReport, CheckResult
        
        mockRun.return_value = CheckReport(results=[
            CheckResult("Test", False, "Failed")
        ])
        
        result = runner.invoke(app, ["check"])
        
        assert result.exit_code == 1


class TestConfigCommand:
    """Tests for config command."""

    @patch("fastapi_launcher.cli.showConfig")
    def test_config_show(self, mockShow: MagicMock) -> None:
        """Test config show command."""
        result = runner.invoke(app, ["config"])
        
        mockShow.assert_called_once()
