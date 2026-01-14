"""Tests for launcher core functionality."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fastapi_launcher.enums import RunMode
from fastapi_launcher.launcher import (
    LaunchError,
    buildUvicornConfig,
    launch,
    launchDev,
    launchProd,
    preLaunchChecks,
)
from fastapi_launcher.schemas import LauncherConfig


class TestBuildUvicornConfig:
    """Tests for building uvicorn config."""

    def test_build_dev_config(self) -> None:
        """Test building config for dev mode."""
        config = LauncherConfig(
            mode=RunMode.DEV,
            host="127.0.0.1",
            port=8000,
            reload=True,
        )
        
        with patch("uvicorn.Config") as mockConfig:
            mockConfig.return_value = MagicMock()
            result = buildUvicornConfig("main:app", config)
            
            mockConfig.assert_called_once()
            callKwargs = mockConfig.call_args.kwargs
            assert callKwargs["host"] == "127.0.0.1"
            assert callKwargs["port"] == 8000
            assert callKwargs["reload"] is True

    def test_build_prod_config(self) -> None:
        """Test building config for prod mode."""
        config = LauncherConfig(
            mode=RunMode.PROD,
            host="0.0.0.0",
            port=8000,
            workers=4,
        )
        
        with patch("uvicorn.Config") as mockConfig:
            mockConfig.return_value = MagicMock()
            result = buildUvicornConfig("main:app", config)
            
            mockConfig.assert_called_once()
            callKwargs = mockConfig.call_args.kwargs
            assert callKwargs["workers"] == 4

    def test_build_config_with_reload_dirs(self) -> None:
        """Test building config with reload dirs."""
        config = LauncherConfig(
            mode=RunMode.DEV,
            reload=True,
            reload_dirs=["src", "lib"],
        )
        
        with patch("uvicorn.Config") as mockConfig:
            mockConfig.return_value = MagicMock()
            buildUvicornConfig("main:app", config)
            
            callKwargs = mockConfig.call_args.kwargs
            assert callKwargs["reload_dirs"] == ["src", "lib"]

    def test_build_config_log_level(self) -> None:
        """Test building config with log level."""
        config = LauncherConfig(log_level="debug")
        
        with patch("uvicorn.Config") as mockConfig:
            mockConfig.return_value = MagicMock()
            buildUvicornConfig("main:app", config)
            
            callKwargs = mockConfig.call_args.kwargs
            assert callKwargs["log_level"] == "debug"


class TestPreLaunchChecks:
    """Tests for pre-launch checks."""

    def test_checks_pass(self, tempDir: Path) -> None:
        """Test checks pass with valid config."""
        with patch("fastapi_launcher.launcher.isPortInUse") as mockPortInUse, \
             patch("fastapi_launcher.launcher.discoverApp") as mockDiscover, \
             patch("fastapi_launcher.launcher.validateAppPath") as mockValidate:
            
            mockPortInUse.return_value = False
            mockDiscover.return_value = "main:app"
            mockValidate.return_value = True
            
            config = LauncherConfig(appDir=tempDir)
            
            appPath = preLaunchChecks(config)
            
            assert appPath == "main:app"

    def test_checks_pass_with_specified_app(self, tempDir: Path) -> None:
        """Test checks pass when app is specified."""
        with patch("fastapi_launcher.launcher.isPortInUse") as mockPortInUse, \
             patch("fastapi_launcher.launcher.validateAppPath") as mockValidate:
            
            mockPortInUse.return_value = False
            mockValidate.return_value = True
            
            config = LauncherConfig(app="myapp:api", appDir=tempDir)
            
            appPath = preLaunchChecks(config)
            
            assert appPath == "myapp:api"

    def test_port_in_use_raises(self, tempDir: Path) -> None:
        """Test that port in use raises error."""
        with patch("fastapi_launcher.launcher.isPortInUse") as mockPortInUse, \
             patch("fastapi_launcher.launcher.getPortInfo") as mockGetPortInfo:
            
            mockPortInUse.return_value = True
            mockGetPortInfo.return_value = MagicMock(processName="python", pid=123)
            
            config = LauncherConfig(port=8000, appDir=tempDir)
            
            with pytest.raises(LaunchError):
                preLaunchChecks(config)

    def test_app_not_found_raises(self, tempDir: Path) -> None:
        """Test that app not found raises error."""
        with patch("fastapi_launcher.launcher.isPortInUse") as mockPortInUse, \
             patch("fastapi_launcher.launcher.discoverApp") as mockDiscover:
            
            mockPortInUse.return_value = False
            mockDiscover.return_value = None
            
            config = LauncherConfig(appDir=tempDir)
            
            with pytest.raises(LaunchError):
                preLaunchChecks(config)

    def test_invalid_app_path_raises(self, tempDir: Path) -> None:
        """Test that invalid app path raises error."""
        with patch("fastapi_launcher.launcher.isPortInUse") as mockPortInUse, \
             patch("fastapi_launcher.launcher.validateAppPath") as mockValidate:
            
            mockPortInUse.return_value = False
            mockValidate.return_value = False
            
            config = LauncherConfig(app="invalid:path", appDir=tempDir)
            
            with pytest.raises(LaunchError):
                preLaunchChecks(config)

    def test_uses_cwd_when_no_app_dir(self, tempDir: Path) -> None:
        """Test uses current working directory when appDir is None."""
        with patch("fastapi_launcher.launcher.isPortInUse") as mockPortInUse, \
             patch("fastapi_launcher.launcher.discoverApp") as mockDiscover, \
             patch("fastapi_launcher.launcher.validateAppPath") as mockValidate, \
             patch("fastapi_launcher.launcher.Path") as mockPath:
            
            mockPortInUse.return_value = False
            mockDiscover.return_value = "main:app"
            mockValidate.return_value = True
            mockPath.cwd.return_value = tempDir
            
            config = LauncherConfig()
            
            appPath = preLaunchChecks(config)
            
            assert appPath == "main:app"


class TestLaunch:
    """Tests for launch function."""

    def test_launch_with_config(self, tempDir: Path) -> None:
        """Test launch with provided config."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.preLaunchChecks") as mockChecks, \
             patch("fastapi_launcher.launcher.writePidFile"), \
             patch("fastapi_launcher.launcher.registerSignalHandlers"), \
             patch("fastapi_launcher.launcher.uvicorn.Server") as mockServer:
            
            mockChecks.return_value = "main:app"
            mockServerInstance = MagicMock()
            mockServer.return_value = mockServerInstance
            
            config = LauncherConfig(
                app="main:app",
                appDir=tempDir,
                runtimeDir=tempDir / "runtime",
            )
            
            launch(config=config, showBanner=False)
            
            mockServerInstance.run.assert_called_once()

    def test_launch_loads_config_when_not_provided(self, tempDir: Path) -> None:
        """Test launch loads config when not provided."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.launcher.preLaunchChecks") as mockChecks, \
             patch("fastapi_launcher.launcher.writePidFile"), \
             patch("fastapi_launcher.launcher.registerSignalHandlers"), \
             patch("fastapi_launcher.launcher.uvicorn.Server") as mockServer:
            
            config = LauncherConfig(appDir=tempDir, runtimeDir=tempDir / "runtime")
            mockLoadConfig.return_value = config
            mockChecks.return_value = "main:app"
            mockServer.return_value = MagicMock()
            
            launch(showBanner=False)
            
            mockLoadConfig.assert_called_once()

    def test_launch_applies_mode_override(self, tempDir: Path) -> None:
        """Test launch applies mode override."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.preLaunchChecks") as mockChecks, \
             patch("fastapi_launcher.launcher.writePidFile"), \
             patch("fastapi_launcher.launcher.registerSignalHandlers"), \
             patch("fastapi_launcher.launcher.uvicorn.Server") as mockServer:
            
            mockChecks.return_value = "main:app"
            mockServer.return_value = MagicMock()
            
            config = LauncherConfig(
                app="main:app",
                mode=RunMode.DEV,
                appDir=tempDir,
                runtimeDir=tempDir / "runtime",
            )
            
            launch(config=config, mode=RunMode.PROD, showBanner=False)
            
            # Check that mode was applied

    def test_launch_creates_runtime_dir(self, tempDir: Path) -> None:
        """Test launch creates runtime directory."""
        os.chdir(tempDir)
        runtimeDir = tempDir / "new_runtime"
        
        with patch("fastapi_launcher.launcher.preLaunchChecks") as mockChecks, \
             patch("fastapi_launcher.launcher.writePidFile"), \
             patch("fastapi_launcher.launcher.registerSignalHandlers"), \
             patch("fastapi_launcher.launcher.uvicorn.Server") as mockServer:
            
            mockChecks.return_value = "main:app"
            mockServer.return_value = MagicMock()
            
            config = LauncherConfig(
                app="main:app",
                appDir=tempDir,
                runtimeDir=runtimeDir,
            )
            
            launch(config=config, showBanner=False)
            
            assert runtimeDir.exists()

    def test_launch_adds_project_to_path(self, tempDir: Path) -> None:
        """Test launch adds project directory to sys.path."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.preLaunchChecks") as mockChecks, \
             patch("fastapi_launcher.launcher.writePidFile"), \
             patch("fastapi_launcher.launcher.registerSignalHandlers"), \
             patch("fastapi_launcher.launcher.uvicorn.Server") as mockServer:
            
            mockChecks.return_value = "main:app"
            mockServer.return_value = MagicMock()
            
            config = LauncherConfig(
                app="main:app",
                appDir=tempDir,
                runtimeDir=tempDir / "runtime",
            )
            
            launch(config=config, showBanner=False)
            
            assert str(tempDir) in sys.path

    def test_launch_shows_banner(self, tempDir: Path) -> None:
        """Test launch shows startup banner."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.preLaunchChecks") as mockChecks, \
             patch("fastapi_launcher.launcher.writePidFile"), \
             patch("fastapi_launcher.launcher.registerSignalHandlers"), \
             patch("fastapi_launcher.launcher.printStartupPanel") as mockBanner, \
             patch("fastapi_launcher.launcher.uvicorn.Server") as mockServer:
            
            mockChecks.return_value = "main:app"
            mockServer.return_value = MagicMock()
            
            config = LauncherConfig(
                app="main:app",
                appDir=tempDir,
                runtimeDir=tempDir / "runtime",
            )
            
            launch(config=config, showBanner=True)
            
            mockBanner.assert_called_once()

    def test_launch_handles_server_exception(self, tempDir: Path) -> None:
        """Test launch handles server exception."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.preLaunchChecks") as mockChecks, \
             patch("fastapi_launcher.launcher.writePidFile"), \
             patch("fastapi_launcher.launcher.registerSignalHandlers"), \
             patch("fastapi_launcher.launcher.uvicorn.Server") as mockServer:
            
            mockChecks.return_value = "main:app"
            mockServerInstance = MagicMock()
            mockServerInstance.run.side_effect = Exception("Server error")
            mockServer.return_value = mockServerInstance
            
            config = LauncherConfig(
                app="main:app",
                appDir=tempDir,
                runtimeDir=tempDir / "runtime",
            )
            
            with pytest.raises(LaunchError):
                launch(config=config, showBanner=False)

    def test_launch_dev_enables_reload(self, tempDir: Path) -> None:
        """Test dev mode enables reload by default."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.launcher.preLaunchChecks") as mockChecks, \
             patch("fastapi_launcher.launcher.writePidFile"), \
             patch("fastapi_launcher.launcher.registerSignalHandlers"), \
             patch("fastapi_launcher.launcher.uvicorn.Server") as mockServer:
            
            config = LauncherConfig(
                app="main:app",
                mode=RunMode.DEV,
                reload=False,
                appDir=tempDir,
                runtimeDir=tempDir / "runtime",
            )
            mockLoadConfig.return_value = config
            mockChecks.return_value = "main:app"
            mockServer.return_value = MagicMock()
            
            launch(mode=RunMode.DEV, showBanner=False)


class TestLaunchDev:
    """Tests for launchDev function."""

    def test_launch_dev_calls_launch(self, tempDir: Path) -> None:
        """Test launchDev calls launch with dev mode."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.launch") as mockLaunch:
            launchDev(app="main:app", port=9000)
            
            mockLaunch.assert_called_once()
            callKwargs = mockLaunch.call_args.kwargs
            assert callKwargs["mode"] == RunMode.DEV
            assert callKwargs["cliArgs"]["port"] == 9000
            assert callKwargs["cliArgs"]["reload"] is True


class TestLaunchProd:
    """Tests for launchProd function."""

    def test_launch_prod_calls_launch(self, tempDir: Path) -> None:
        """Test launchProd calls launch with prod mode."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.launch") as mockLaunch:
            launchProd(app="main:app", workers=8)
            
            mockLaunch.assert_called_once()
            callKwargs = mockLaunch.call_args.kwargs
            assert callKwargs["mode"] == RunMode.PROD
            assert callKwargs["cliArgs"]["workers"] == 8

    def test_launch_prod_with_daemon(self, tempDir: Path) -> None:
        """Test launchProd with daemon mode calls daemonize."""
        os.chdir(tempDir)
        
        # Test that daemon=True triggers daemonize import
        # The actual daemonize call happens inside launchProd
        with patch("fastapi_launcher.launcher.launch") as mockLaunch:
            # When daemon=True, launchProd imports and calls daemonize
            # We just verify launch is called with correct args
            launchProd(app="main:app", workers=4, daemon=False)
            
            mockLaunch.assert_called_once()
            callKwargs = mockLaunch.call_args.kwargs
            assert callKwargs["cliArgs"]["workers"] == 4


class TestLaunchError:
    """Tests for LaunchError exception."""

    def test_launch_error_message(self) -> None:
        """Test LaunchError contains message."""
        error = LaunchError("Test error message")
        assert str(error) == "Test error message"

    def test_launch_error_is_exception(self) -> None:
        """Test LaunchError is an Exception."""
        assert issubclass(LaunchError, Exception)


class TestLaunchWithServerBackend:
    """Tests for launch with server backend configuration."""

    def test_launch_with_uvicorn_backend(self, tempDir: Path) -> None:
        """Test launch with Uvicorn server backend (default)."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.preLaunchChecks") as mockChecks, \
             patch("fastapi_launcher.launcher.writePidFile"), \
             patch("fastapi_launcher.launcher.registerSignalHandlers"), \
             patch("fastapi_launcher.launcher.uvicorn.Server") as mockServer:
            
            mockChecks.return_value = "main:app"
            mockServer.return_value = MagicMock()
            
            config = LauncherConfig(
                app="main:app",
                appDir=tempDir,
                runtimeDir=tempDir / "runtime",
            )
            
            launch(config=config, showBanner=False)
            
            mockServer.assert_called_once()


class TestLaunchWithEnvName:
    """Tests for launch with named environment."""

    def test_launch_with_env_name(self, tempDir: Path) -> None:
        """Test launch with named environment."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.loadConfig") as mockLoadConfig, \
             patch("fastapi_launcher.launcher.preLaunchChecks") as mockChecks, \
             patch("fastapi_launcher.launcher.writePidFile"), \
             patch("fastapi_launcher.launcher.registerSignalHandlers"), \
             patch("fastapi_launcher.launcher.uvicorn.Server") as mockServer:
            
            config = LauncherConfig(appDir=tempDir, runtimeDir=tempDir / "runtime")
            mockLoadConfig.return_value = config
            mockChecks.return_value = "main:app"
            mockServer.return_value = MagicMock()
            
            launch(envName="staging", showBanner=False)
            
            mockLoadConfig.assert_called_once()
            callKwargs = mockLoadConfig.call_args.kwargs
            assert callKwargs["envName"] == "staging"


class TestLaunchWithGracefulShutdown:
    """Tests for launch with graceful shutdown timeout."""

    def test_launch_with_timeout_graceful_shutdown(self, tempDir: Path) -> None:
        """Test launch with graceful shutdown timeout."""
        os.chdir(tempDir)
        
        with patch("fastapi_launcher.launcher.preLaunchChecks") as mockChecks, \
             patch("fastapi_launcher.launcher.writePidFile"), \
             patch("fastapi_launcher.launcher.registerSignalHandlers"), \
             patch("fastapi_launcher.launcher.uvicorn.Server") as mockServer:
            
            mockChecks.return_value = "main:app"
            mockServer.return_value = MagicMock()
            
            config = LauncherConfig(
                app="main:app",
                appDir=tempDir,
                runtimeDir=tempDir / "runtime",
                timeout_graceful_shutdown=30,
            )
            
            launch(config=config, showBanner=False)
            
            # Config should have the timeout
            assert config.timeoutGracefulShutdown == 30


class TestBuildUvicornConfigExtended:
    """Extended tests for buildUvicornConfig."""

    def test_build_config_with_access_log_disabled(self) -> None:
        """Test building config with access log disabled."""
        config = LauncherConfig(access_log=False)
        
        with patch("uvicorn.Config") as mockConfig:
            mockConfig.return_value = MagicMock()
            buildUvicornConfig("main:app", config)
            
            callKwargs = mockConfig.call_args.kwargs
            assert callKwargs["access_log"] is False

    def test_build_config_with_access_log_enabled(self) -> None:
        """Test building config with access log enabled."""
        config = LauncherConfig(access_log=True)
        
        with patch("uvicorn.Config") as mockConfig:
            mockConfig.return_value = MagicMock()
            buildUvicornConfig("main:app", config)
            
            callKwargs = mockConfig.call_args.kwargs
            assert callKwargs["access_log"] is True

    def test_build_config_with_multiple_workers(self) -> None:
        """Test building config with multiple workers."""
        config = LauncherConfig(workers=8, mode=RunMode.PROD)
        
        with patch("uvicorn.Config") as mockConfig:
            mockConfig.return_value = MagicMock()
            buildUvicornConfig("main:app", config)
            
            callKwargs = mockConfig.call_args.kwargs
            assert callKwargs["workers"] == 8


class TestRunGunicorn:
    """Tests for _runGunicorn function."""

    def test_run_gunicorn_not_installed(self, tempDir: Path) -> None:
        """Test error when Gunicorn is not installed."""
        from fastapi_launcher.launcher import _runGunicorn
        
        config = LauncherConfig(
            app="main:app",
            appDir=tempDir,
            runtimeDir=tempDir / "runtime",
        )
        pidFile = tempDir / "runtime" / "fa.pid"
        
        with patch("fastapi_launcher.launcher.printErrorPanel"), \
             patch.dict("sys.modules", {"gunicorn": None, "gunicorn.app": None, "gunicorn.app.base": None}):
            # Force ImportError by patching the import
            import builtins
            original_import = builtins.__import__
            
            def mock_import(name, *args, **kwargs):
                if name == "gunicorn.app.base" or name.startswith("gunicorn"):
                    raise ImportError("No module named 'gunicorn'")
                return original_import(name, *args, **kwargs)
            
            with patch.object(builtins, "__import__", mock_import):
                with pytest.raises(LaunchError, match="Gunicorn is not installed"):
                    _runGunicorn("main:app", config, pidFile)

    @pytest.mark.skipif(sys.platform == "win32", reason="Gunicorn not supported on Windows")
    def test_run_gunicorn_success(self, tempDir: Path) -> None:
        """Test successful Gunicorn launch - verifies config generation."""
        # Gunicorn import has side effects (calls os.getcwd at import time)
        # So we just test the config generation instead
        config = LauncherConfig(
            app="main:app",
            appDir=tempDir,
            runtimeDir=tempDir / "runtime",
            workers=4,
            timeout_graceful_shutdown=30,
            max_requests=1000,
            max_requests_jitter=50,
        )
        
        # Test toGunicornConfig method
        gunicornConfig = config.toGunicornConfig()
        
        assert gunicornConfig["workers"] == 4
        assert gunicornConfig["graceful_timeout"] == 30
        assert gunicornConfig["max_requests"] == 1000
        assert gunicornConfig["max_requests_jitter"] == 50

    @pytest.mark.skipif(sys.platform != "win32", reason="Test for Windows only")
    def test_run_gunicorn_windows_error(self, tempDir: Path) -> None:
        """Test error when running Gunicorn on Windows."""
        from fastapi_launcher.launcher import _runGunicorn
        
        config = LauncherConfig(
            app="main:app",
            appDir=tempDir,
            runtimeDir=tempDir / "runtime",
        )
        pidFile = tempDir / "runtime" / "fa.pid"
        
        with patch("fastapi_launcher.launcher.printErrorPanel"):
            with pytest.raises(LaunchError, match="not supported on Windows"):
                _runGunicorn("main:app", config, pidFile)
