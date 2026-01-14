"""Tests for CLI commands."""

import os
import sys
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


class TestInitCommand:
    """Tests for init command."""

    def test_init_success(self, tempDir: Path) -> None:
        """Test init command success."""
        # Create a pyproject.toml without launcher config
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""[project]
name = "test-project"
version = "0.1.0"
""")
        
        os.chdir(tempDir)
        
        result = runner.invoke(app, ["init"])
        
        assert result.exit_code == 0

    def test_init_already_exists(self, tempDir: Path) -> None:
        """Test init command when config already exists."""
        # Create a pyproject.toml with launcher config
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""[project]
name = "test-project"
version = "0.1.0"

[tool.fastapi-launcher]
app = "main:app"
""")
        
        os.chdir(tempDir)
        
        result = runner.invoke(app, ["init"])
        
        # Should exit with 0 since it's not an error
        assert result.exit_code == 0

    def test_init_with_env(self, tempDir: Path) -> None:
        """Test init command with --env flag."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""[project]
name = "test-project"
version = "0.1.0"
""")
        
        os.chdir(tempDir)
        
        result = runner.invoke(app, ["init", "--env"])
        
        assert result.exit_code == 0
        # Check .env.example was created
        assert (tempDir / ".env.example").exists()

    def test_init_with_force(self, tempDir: Path) -> None:
        """Test init command with --force flag."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""[project]
name = "test-project"
version = "0.1.0"

[tool.fastapi-launcher]
app = "old:app"
""")
        
        os.chdir(tempDir)
        
        result = runner.invoke(app, ["init", "--force"])
        
        assert result.exit_code == 0

    def test_init_no_pyproject(self, tempDir: Path) -> None:
        """Test init command failure when no pyproject.toml."""
        os.chdir(tempDir)
        
        result = runner.invoke(app, ["init"])
        
        assert result.exit_code == 1


class TestRunCommand:
    """Tests for run (smart mode) command."""

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.smartMode.detectEnvironment")
    def test_run_detects_dev(self, mockDetect: MagicMock, mockLaunch: MagicMock) -> None:
        """Test run command detects development."""
        from fastapi_launcher.enums import RunMode
        
        mockDetect.return_value = ("dev", RunMode.DEV)
        
        result = runner.invoke(app, ["run"])
        
        mockLaunch.assert_called_once()
        callKwargs = mockLaunch.call_args.kwargs
        assert callKwargs["mode"] == RunMode.DEV

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.smartMode.detectEnvironment")
    def test_run_detects_prod(self, mockDetect: MagicMock, mockLaunch: MagicMock) -> None:
        """Test run command detects production."""
        from fastapi_launcher.enums import RunMode
        
        mockDetect.return_value = ("prod", RunMode.PROD)
        
        result = runner.invoke(app, ["run"])
        
        mockLaunch.assert_called_once()
        callKwargs = mockLaunch.call_args.kwargs
        assert callKwargs["mode"] == RunMode.PROD

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.smartMode.detectEnvironment")
    def test_run_detects_staging(self, mockDetect: MagicMock, mockLaunch: MagicMock) -> None:
        """Test run command detects staging environment."""
        from fastapi_launcher.enums import RunMode
        
        mockDetect.return_value = ("staging", RunMode.PROD)
        
        result = runner.invoke(app, ["run"])
        
        mockLaunch.assert_called_once()
        callKwargs = mockLaunch.call_args.kwargs
        assert callKwargs["envName"] == "staging"

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.smartMode.detectEnvironment")
    def test_run_with_custom_options(self, mockDetect: MagicMock, mockLaunch: MagicMock) -> None:
        """Test run command with custom options."""
        from fastapi_launcher.enums import RunMode
        
        mockDetect.return_value = ("dev", RunMode.DEV)
        
        result = runner.invoke(app, ["run", "--port", "9000", "--app", "myapp:app"])
        
        mockLaunch.assert_called_once()
        callKwargs = mockLaunch.call_args.kwargs
        assert callKwargs["cliArgs"]["port"] == 9000
        assert callKwargs["cliArgs"]["app"] == "myapp:app"

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.smartMode.detectEnvironment")
    def test_run_keyboard_interrupt(self, mockDetect: MagicMock, mockLaunch: MagicMock) -> None:
        """Test run command handles keyboard interrupt."""
        from fastapi_launcher.enums import RunMode
        
        mockDetect.return_value = ("dev", RunMode.DEV)
        mockLaunch.side_effect = KeyboardInterrupt()
        
        result = runner.invoke(app, ["run"])
        
        assert result.exit_code == 0


class TestReloadCommand:
    """Tests for reload command."""

    def test_reload_no_server(self, tempDir: Path) -> None:
        """Test reload when no server running."""
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid:
            mockLoadConfig.return_value = MagicMock(runtimeDir=tempDir / "runtime")
            mockReadPid.return_value = None
            
            result = runner.invoke(app, ["reload"])
            
            assert result.exit_code == 1

    def test_reload_process_not_running(self, tempDir: Path) -> None:
        """Test reload when process not running."""
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.cli.removePidFile"):
            mockLoadConfig.return_value = MagicMock(runtimeDir=tempDir / "runtime")
            mockReadPid.return_value = 12345
            mockIsRunning.return_value = False
            
            result = runner.invoke(app, ["reload"])
            
            assert result.exit_code == 1

    @pytest.mark.skipif(sys.platform == "win32", reason="Reload uses SIGHUP not available on Windows")
    def test_reload_success_unix(self, tempDir: Path) -> None:
        """Test reload command success on Unix."""
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.process.sendSignal") as mockSendSignal:
            mockLoadConfig.return_value = MagicMock(runtimeDir=tempDir / "runtime")
            mockReadPid.return_value = 12345
            mockIsRunning.return_value = True
            mockSendSignal.return_value = True
            
            result = runner.invoke(app, ["reload"])
            
            # Should succeed or at least not fail with exit 1 due to missing pid
            mockSendSignal.assert_called_once()


class TestMonitorCommand:
    """Tests for monitor command."""

    @patch("fastapi_launcher.monitor.checkTextualInstalled")
    @patch("fastapi_launcher.monitor.runMonitorSimple")
    @patch("fastapi_launcher.cli.isProcessRunning")
    @patch("fastapi_launcher.cli.readPidFile")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_monitor_no_tui(
        self, mockLoadConfig: MagicMock, mockReadPid: MagicMock,
        mockIsRunning: MagicMock, mockRunSimple: MagicMock,
        mockCheckTextual: MagicMock, tempDir: Path
    ) -> None:
        """Test monitor command with --no-tui."""
        mockLoadConfig.return_value = MagicMock(runtimeDir=tempDir / "runtime")
        mockReadPid.return_value = 12345
        mockIsRunning.return_value = True
        mockRunSimple.side_effect = KeyboardInterrupt()
        
        result = runner.invoke(app, ["monitor", "--no-tui"])
        
        mockRunSimple.assert_called_once()

    @patch("fastapi_launcher.monitor.checkTextualInstalled")
    @patch("fastapi_launcher.monitor.runMonitorSimple")
    @patch("fastapi_launcher.cli.isProcessRunning")
    @patch("fastapi_launcher.cli.readPidFile")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_monitor_textual_not_installed(
        self, mockLoadConfig: MagicMock, mockReadPid: MagicMock,
        mockIsRunning: MagicMock, mockRunSimple: MagicMock,
        mockCheckTextual: MagicMock, tempDir: Path
    ) -> None:
        """Test monitor command when textual not installed."""
        mockLoadConfig.return_value = MagicMock(runtimeDir=tempDir / "runtime")
        mockReadPid.return_value = 12345
        mockIsRunning.return_value = True
        mockCheckTextual.return_value = False
        mockRunSimple.side_effect = KeyboardInterrupt()
        
        result = runner.invoke(app, ["monitor"])
        
        # Should fall back to simple mode
        mockRunSimple.assert_called_once()

    @patch("fastapi_launcher.cli.isProcessRunning")
    @patch("fastapi_launcher.cli.readPidFile")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_monitor_server_not_running(
        self, mockLoadConfig: MagicMock, mockReadPid: MagicMock,
        mockIsRunning: MagicMock, tempDir: Path
    ) -> None:
        """Test monitor command when server not running."""
        mockLoadConfig.return_value = MagicMock(runtimeDir=tempDir / "runtime")
        mockReadPid.return_value = None
        mockIsRunning.return_value = False
        
        with patch("fastapi_launcher.monitor.runMonitorSimple") as mockRunSimple:
            mockRunSimple.side_effect = KeyboardInterrupt()
            
            result = runner.invoke(app, ["monitor", "--no-tui"])
            
            # Should still try to start monitor (it will show "not running")


class TestStartWithEnvAndServer:
    """Tests for start command with new options."""

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_start_with_env(
        self, mockLoadConfig: MagicMock, mockLaunch: MagicMock
    ) -> None:
        """Test start command with --env option."""
        mockLoadConfig.return_value = MagicMock(runtimeDir=Path("runtime"))
        
        result = runner.invoke(app, ["start", "--env", "staging"])
        
        mockLaunch.assert_called_once()
        callKwargs = mockLaunch.call_args.kwargs
        assert callKwargs["envName"] == "staging"

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_start_with_server_gunicorn(
        self, mockLoadConfig: MagicMock, mockLaunch: MagicMock
    ) -> None:
        """Test start command with --server gunicorn."""
        from fastapi_launcher.enums import ServerBackend
        
        mockLoadConfig.return_value = MagicMock(runtimeDir=Path("runtime"))
        
        result = runner.invoke(app, ["start", "--server", "gunicorn"])
        
        mockLaunch.assert_called_once()
        callKwargs = mockLaunch.call_args.kwargs
        assert callKwargs["cliArgs"]["server"] == ServerBackend.GUNICORN

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_start_with_invalid_server(
        self, mockLoadConfig: MagicMock, mockLaunch: MagicMock
    ) -> None:
        """Test start command with invalid server backend."""
        mockLoadConfig.return_value = MagicMock(runtimeDir=Path("runtime"))
        
        result = runner.invoke(app, ["start", "--server", "invalid"])
        
        assert result.exit_code == 1
        mockLaunch.assert_not_called()

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_start_with_timeout_graceful_shutdown(
        self, mockLoadConfig: MagicMock, mockLaunch: MagicMock
    ) -> None:
        """Test start command with --timeout-graceful-shutdown."""
        mockLoadConfig.return_value = MagicMock(runtimeDir=Path("runtime"))
        
        result = runner.invoke(app, ["start", "--timeout-graceful-shutdown", "30"])
        
        mockLaunch.assert_called_once()
        callKwargs = mockLaunch.call_args.kwargs
        assert callKwargs["cliArgs"]["timeout_graceful_shutdown"] == 30

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.cli.loadConfig")
    def test_start_with_max_requests(
        self, mockLoadConfig: MagicMock, mockLaunch: MagicMock
    ) -> None:
        """Test start command with --max-requests."""
        mockLoadConfig.return_value = MagicMock(runtimeDir=Path("runtime"))
        
        result = runner.invoke(app, ["start", "--max-requests", "1000"])
        
        mockLaunch.assert_called_once()
        callKwargs = mockLaunch.call_args.kwargs
        assert callKwargs["cliArgs"]["max_requests"] == 1000


class TestDevWithEnv:
    """Tests for dev command with --env option."""

    @patch("fastapi_launcher.cli.launch")
    def test_dev_with_env(self, mockLaunch: MagicMock) -> None:
        """Test dev command with --env option."""
        result = runner.invoke(app, ["dev", "--env", "staging"])
        
        mockLaunch.assert_called_once()
        callKwargs = mockLaunch.call_args.kwargs
        assert callKwargs["envName"] == "staging"


class TestStatusVerbose:
    """Tests for status command with --verbose option."""

    def test_status_verbose(self, tempDir: Path) -> None:
        """Test status command with --verbose."""
        from fastapi_launcher.process import ProcessStatus, WorkerStatus
        
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isPortInUse") as mockIsPortInUse, \
             patch("fastapi_launcher.cli.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.process.getWorkerStatuses") as mockGetWorkers, \
             patch("fastapi_launcher.cli.printStatusTable") as mockPrintStatus:
            
            mockLoadConfig.return_value = MagicMock(
                runtimeDir=tempDir / "runtime",
                host="127.0.0.1",
                port=8000,
            )
            mockReadPid.return_value = 12345
            mockIsRunning.return_value = True
            mockIsPortInUse.return_value = False
            mockGetWorkers.return_value = [
                WorkerStatus(pid=1001, cpuPercent=5.0, memoryMb=100.0, requestsHandled=0, status="running")
            ]
            
            result = runner.invoke(app, ["status", "--verbose"])
            
            assert result.exit_code == 0
            mockPrintStatus.assert_called_once()


class TestStatusServerRunningExternally:
    """Tests for status command when server started externally (no PID file)."""

    def test_status_server_running_externally(self, tempDir: Path) -> None:
        """Test status when server is running but started externally (no PID file)."""
        from fastapi_launcher.process import ProcessStatus
        
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isPortInUse") as mockIsPortInUse, \
             patch("fastapi_launcher.cli.getPortInfo") as mockGetPortInfo, \
             patch("fastapi_launcher.cli.printStatusTable") as mockPrintStatus:
            
            mockLoadConfig.return_value = MagicMock(
                runtimeDir=tempDir / "runtime",
                host="127.0.0.1",
                port=8000,
            )
            mockReadPid.return_value = None  # No PID file
            mockIsPortInUse.return_value = True  # But port is in use
            mockGetPortInfo.return_value = MagicMock(pid=12345, processName="python")
            
            result = runner.invoke(app, ["status"])
            
            assert result.exit_code == 0
            mockPrintStatus.assert_called_once()

    def test_status_server_running_externally_verbose(self, tempDir: Path) -> None:
        """Test verbose status when server is running externally."""
        from fastapi_launcher.process import ProcessStatus, WorkerStatus
        
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isPortInUse") as mockIsPortInUse, \
             patch("fastapi_launcher.cli.getPortInfo") as mockGetPortInfo, \
             patch("fastapi_launcher.process.getWorkerStatuses") as mockGetWorkers, \
             patch("fastapi_launcher.cli.printStatusTable") as mockPrintStatus:
            
            mockLoadConfig.return_value = MagicMock(
                runtimeDir=tempDir / "runtime",
                host="127.0.0.1",
                port=8000,
            )
            mockReadPid.return_value = None
            mockIsPortInUse.return_value = True
            mockGetPortInfo.return_value = MagicMock(pid=12345, processName="python")
            mockGetWorkers.return_value = [
                WorkerStatus(pid=1001, cpuPercent=2.0, memoryMb=50.0, requestsHandled=10, status="idle")
            ]
            
            result = runner.invoke(app, ["status", "--verbose"])
            
            assert result.exit_code == 0


class TestCleanCommandEdgeCases:
    """Edge case tests for clean command."""

    def test_clean_with_running_server(self, tempDir: Path) -> None:
        """Test clean command when server is still running."""
        runtimeDir = tempDir / "runtime"
        runtimeDir.mkdir(parents=True)
        pidFile = runtimeDir / "fa.pid"
        pidFile.write_text("12345")
        
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.cli.printWarningMessage") as mockWarn:
            
            mockLoadConfig.return_value = MagicMock(runtimeDir=runtimeDir)
            mockReadPid.return_value = 12345
            mockIsRunning.return_value = True  # Server is still running
            
            result = runner.invoke(app, ["clean", "--yes"])
            
            # Should warn that server is running
            mockWarn.assert_called()

    def test_clean_pid_file_stale(self, tempDir: Path) -> None:
        """Test clean command when PID file is stale (process not running)."""
        runtimeDir = tempDir / "runtime"
        runtimeDir.mkdir(parents=True)
        pidFile = runtimeDir / "fa.pid"
        pidFile.write_text("12345")
        
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.cli.printSuccessMessage") as mockSuccess:
            
            mockLoadConfig.return_value = MagicMock(runtimeDir=runtimeDir)
            mockReadPid.return_value = 12345
            mockIsRunning.return_value = False  # Process not running (stale PID)
            
            result = runner.invoke(app, ["clean", "--yes"])
            
            # Should clean up the stale PID file
            assert result.exit_code == 0

    def test_clean_nothing_to_clean(self, tempDir: Path) -> None:
        """Test clean command when there's nothing to clean."""
        runtimeDir = tempDir / "runtime"
        runtimeDir.mkdir(parents=True)
        # No logs, no PID file
        
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.cleanLogs") as mockCleanLogs, \
             patch("fastapi_launcher.cli.printInfoMessage") as mockInfo:
            
            mockLoadConfig.return_value = MagicMock(runtimeDir=runtimeDir)
            mockCleanLogs.return_value = 0  # No files cleaned
            
            result = runner.invoke(app, ["clean", "--logs", "--yes"])
            
            assert result.exit_code == 0


class TestRunCommandEdgeCases:
    """Edge case tests for run command."""

    @patch("fastapi_launcher.cli.launch")
    @patch("fastapi_launcher.smartMode.detectEnvironment")
    def test_run_launch_error(self, mockDetect: MagicMock, mockLaunch: MagicMock) -> None:
        """Test run command with launch error."""
        from fastapi_launcher.enums import RunMode
        from fastapi_launcher.launcher import LaunchError
        
        mockDetect.return_value = ("dev", RunMode.DEV)
        mockLaunch.side_effect = LaunchError("Failed to start")
        
        result = runner.invoke(app, ["run"])
        
        assert result.exit_code == 1


class TestMonitorCommandEdgeCases:
    """Edge case tests for monitor command."""

    def test_monitor_server_not_running_no_tui(self, tempDir: Path) -> None:
        """Test monitor command when server is not running (no-tui mode)."""
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.monitor.runMonitorSimple") as mockRunSimple:
            
            mockLoadConfig.return_value = MagicMock(runtimeDir=tempDir / "runtime")
            mockReadPid.return_value = None
            mockIsRunning.return_value = False
            mockRunSimple.side_effect = KeyboardInterrupt()
            
            result = runner.invoke(app, ["monitor", "--no-tui"])
            
            # Should call runMonitorSimple
            mockRunSimple.assert_called_once()


class TestLogsCommandEdgeCases:
    """Edge case tests for logs command."""

    def test_logs_file_not_found(self, tempDir: Path) -> None:
        """Test logs command when log file doesn't exist."""
        logsDir = tempDir / "runtime" / "logs"
        logsDir.mkdir(parents=True)
        # Don't create the log file
        
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.getLogFiles") as mockGetLogFiles, \
             patch("fastapi_launcher.cli.printWarningMessage") as mockWarn:
            
            mockLoadConfig.return_value = MagicMock(
                runtimeDir=tempDir / "runtime",
                logFormat=MagicMock()
            )
            mockGetLogFiles.return_value = {
                "main": logsDir / "fa.log",  # File doesn't exist
                "access": logsDir / "access.log",
                "error": logsDir / "error.log",
            }
            
            result = runner.invoke(app, ["logs"])
            
            # Should warn about missing file
            assert result.exit_code == 0

    def test_logs_keyboard_interrupt(self, tempDir: Path) -> None:
        """Test logs command with keyboard interrupt (follow mode)."""
        logsDir = tempDir / "runtime" / "logs"
        logsDir.mkdir(parents=True)
        logFile = logsDir / "fa.log"
        logFile.write_text("Line 1\nLine 2\n")
        
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.getLogFiles") as mockGetLogFiles, \
             patch("fastapi_launcher.cli.readLogFile") as mockReadLog:
            
            mockLoadConfig.return_value = MagicMock(
                runtimeDir=tempDir / "runtime",
                logFormat=MagicMock()
            )
            mockGetLogFiles.return_value = {
                "main": logFile,
                "access": logFile,
                "error": logFile,
            }
            # Simulate keyboard interrupt during follow
            mockReadLog.return_value = iter(["Line 1"])
            mockReadLog.side_effect = KeyboardInterrupt()
            
            result = runner.invoke(app, ["logs", "--follow"])
            
            # Should exit gracefully
            assert result.exit_code == 0


class TestStatusProcessRunning:
    """Tests for status when process is running."""

    def test_status_process_running_with_info(self, tempDir: Path) -> None:
        """Test status command with running process and full info."""
        from fastapi_launcher.process import ProcessStatus
        
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.cli.getProcessStatus") as mockGetStatus, \
             patch("fastapi_launcher.cli.isPortInUse") as mockIsPortInUse, \
             patch("fastapi_launcher.cli.printStatusTable") as mockPrintStatus:
            
            from datetime import timedelta
            
            mockLoadConfig.return_value = MagicMock(
                runtimeDir=tempDir / "runtime",
                host="127.0.0.1",
                port=8000,
            )
            mockReadPid.return_value = 12345
            mockIsRunning.return_value = True
            mockGetStatus.return_value = ProcessStatus(
                pid=12345,
                isRunning=True,
                name="python",
                memoryMb=256.0,
                cpuPercent=5.0,
                uptime=timedelta(hours=2),
            )
            mockIsPortInUse.return_value = False
            
            result = runner.invoke(app, ["status"])
            
            assert result.exit_code == 0
            mockPrintStatus.assert_called_once()


class TestStopCommandForce:
    """Tests for stop command with force option."""

    def test_stop_force_kill(self, tempDir: Path) -> None:
        """Test stop command with --force flag."""
        with patch("fastapi_launcher.cli.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.cli.readPidFile") as mockReadPid, \
             patch("fastapi_launcher.cli.isProcessRunning") as mockIsRunning, \
             patch("fastapi_launcher.cli.terminateProcess") as mockTerminate, \
             patch("fastapi_launcher.cli.removePidFile"), \
             patch("fastapi_launcher.cli.waitForPortFree") as mockWaitPort, \
             patch("fastapi_launcher.cli.createSpinner") as mockSpinner:
            
            mockLoadConfig.return_value = MagicMock(runtimeDir=tempDir / "runtime", port=8000)
            mockReadPid.return_value = 12345
            mockIsRunning.return_value = True
            mockTerminate.return_value = True
            mockWaitPort.return_value = True
            mockSpinner.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mockSpinner.return_value.__exit__ = MagicMock(return_value=False)
            
            result = runner.invoke(app, ["stop", "--force"])
            
            mockTerminate.assert_called_once()
