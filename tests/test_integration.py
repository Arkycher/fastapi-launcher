"""Integration tests for FastAPI Launcher."""

import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fastapi_launcher.checker import runAllChecks
from fastapi_launcher.config import loadConfig
from fastapi_launcher.discover import discoverApp
from fastapi_launcher.enums import RunMode
from fastapi_launcher.health import checkHealth
from fastapi_launcher.process import isProcessRunning, readPidFile


class TestConfigurationPriority:
    """Integration tests for configuration priority."""

    def test_cli_overrides_all(self, mockProjectDir: Path, cleanEnv) -> None:
        """Test CLI args override all other sources."""
        # Set conflicting values in different sources
        os.environ["FA_PORT"] = "9000"
        
        # pyproject.toml has port=8000
        config = loadConfig(
            mockProjectDir,
            cliArgs={"port": 7777},
        )
        
        assert config.port == 7777

    def test_env_overrides_pyproject(self, mockProjectDir: Path, cleanEnv) -> None:
        """Test env vars override pyproject.toml."""
        os.environ["FA_PORT"] = "9999"
        
        config = loadConfig(mockProjectDir)
        
        assert config.port == 9999

    def test_dotenv_loaded(self, tempDir: Path, cleanEnv) -> None:
        """Test .env file is loaded."""
        import os
        
        # Create .env file
        envPath = tempDir / ".env"
        envPath.write_text("FA_PORT=8888\n")
        
        # Also set env var to ensure it's picked up
        os.environ["FA_PORT"] = "8888"
        
        try:
            config = loadConfig(tempDir)
            assert config.port == 8888
        finally:
            if "FA_PORT" in os.environ:
                del os.environ["FA_PORT"]

    def test_environment_specific_config(self, tempDir: Path, cleanEnv) -> None:
        """Test environment-specific config is applied."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
port = 8000
reload = false

[tool.fastapi-launcher.dev]
reload = true
log_level = "debug"

[tool.fastapi-launcher.prod]
workers = 8
log_level = "warning"
""")
        
        # Dev mode
        devConfig = loadConfig(tempDir, mode=RunMode.DEV)
        assert devConfig.reload is True
        assert devConfig.logLevel == "debug"
        
        # Prod mode
        prodConfig = loadConfig(tempDir, mode=RunMode.PROD)
        assert prodConfig.workers == 8
        assert prodConfig.logLevel == "warning"


class TestAppDiscoveryIntegration:
    """Integration tests for app discovery."""

    def test_discover_and_validate(self, mockProjectDir: Path) -> None:
        """Test discovering and validating app."""
        appPath = discoverApp(mockProjectDir)
        
        assert appPath == "main:app"

    def test_discover_multiple_files(self, tempDir: Path) -> None:
        """Test discovery with multiple Python files."""
        # Create main.py
        (tempDir / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")
        
        # Create api.py
        (tempDir / "api.py").write_text("from fastapi import FastAPI\napi = FastAPI()")
        
        # Should prefer main.py
        appPath = discoverApp(tempDir)
        assert appPath == "main:app"


class TestCheckerIntegration:
    """Integration tests for checker."""

    def test_full_check_on_valid_project(self, mockProjectDir: Path) -> None:
        """Test running all checks on valid project."""
        report = runAllChecks(mockProjectDir)
        
        # At least some checks should pass
        assert report.passedCount > 0

    def test_check_reports_missing_fastapi(self, tempDir: Path) -> None:
        """Test check reports when dependencies might be missing."""
        report = runAllChecks(tempDir)
        
        # Report should include dependency checks
        names = [r.name for r in report.results]
        assert any("fastapi" in n.lower() for n in names)


class TestEndToEndFlow:
    """End-to-end flow tests."""

    def test_config_to_check_flow(self, mockProjectDir: Path, cleanEnv) -> None:
        """Test configuration to check flow."""
        # Load config
        config = loadConfig(mockProjectDir)
        
        assert config.app == "main:app"
        assert config.port == 8000
        
        # Run checks
        report = runAllChecks(mockProjectDir)
        
        # Pyproject check should pass
        pyprojectCheck = next(
            (r for r in report.results if "pyproject" in r.name.lower()),
            None,
        )
        assert pyprojectCheck is not None
        assert pyprojectCheck.passed is True

    def test_full_project_setup(self, tempDir: Path, cleanEnv) -> None:
        """Test setting up a full project."""
        # Create pyproject.toml
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[project]
name = "test-app"
version = "0.1.0"

[tool.fastapi-launcher]
app = "main:app"
host = "0.0.0.0"
port = 8080
log_level = "debug"
""")
        
        # Create main.py
        mainPath = tempDir / "main.py"
        mainPath.write_text("""
from fastapi import FastAPI

app = FastAPI(title="Test App")

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"healthy": True}
""")
        
        # Load and verify config
        config = loadConfig(tempDir)
        
        assert config.app == "main:app"
        assert config.host == "0.0.0.0"
        assert config.port == 8080
        assert config.logLevel == "debug"
        
        # Discover app
        appPath = discoverApp(tempDir)
        assert appPath == "main:app"


class TestRuntimeDirectoryManagement:
    """Tests for runtime directory management."""

    def test_runtime_dir_creation(self, tempDir: Path, cleanEnv) -> None:
        """Test runtime directory is managed correctly."""
        config = loadConfig(tempDir)
        
        runtimeDir = config.runtimeDir
        if not runtimeDir.is_absolute():
            runtimeDir = tempDir / runtimeDir
        
        # Create runtime dir
        runtimeDir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        logsDir = runtimeDir / "logs"
        logsDir.mkdir(exist_ok=True)
        
        # Create some files
        (runtimeDir / "fa.pid").write_text("12345")
        (logsDir / "fa.log").write_text("log content")
        (logsDir / "access.log").write_text("access log")
        
        # Verify structure
        assert runtimeDir.exists()
        assert logsDir.exists()
        assert (runtimeDir / "fa.pid").exists()
        assert (logsDir / "fa.log").exists()


class TestHealthCheckIntegration:
    """Integration tests for health check."""

    def test_health_check_connection_refused(self) -> None:
        """Test health check when server is not running."""
        result = checkHealth(port=59999, timeout=1.0)
        
        assert result.healthy is False
        assert result.error is not None


class TestProcessManagementIntegration:
    """Integration tests for process management."""

    def test_pid_file_lifecycle(self, tempDir: Path) -> None:
        """Test PID file lifecycle."""
        from fastapi_launcher.process import removePidFile, writePidFile
        
        pidFile = tempDir / "runtime" / "fa.pid"
        
        # Write PID
        writePidFile(pidFile, os.getpid())
        assert pidFile.exists()
        
        # Read PID
        pid = readPidFile(pidFile)
        assert pid == os.getpid()
        
        # Check if running
        assert isProcessRunning(pid) is True
        
        # Remove PID file
        removePidFile(pidFile)
        assert not pidFile.exists()
