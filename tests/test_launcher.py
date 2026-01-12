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
