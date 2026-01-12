"""Core launcher for uvicorn server."""

import os
import sys
from pathlib import Path
from typing import Optional

import uvicorn

from .config import loadConfig
from .discover import discoverApp, validateAppPath
from .enums import RunMode
from .port import getPortInfo, isPortInUse, waitForPort
from .process import registerSignalHandlers, writePidFile
from .schemas import LauncherConfig
from .ui import (
    console,
    printErrorPanel,
    printInfoMessage,
    printPortConflict,
    printStartupPanel,
    printSuccessMessage,
)


class LaunchError(Exception):
    """Exception raised when launching fails."""

    pass


def buildUvicornConfig(
    appPath: str,
    config: LauncherConfig,
) -> uvicorn.Config:
    """
    Build uvicorn.Config from LauncherConfig.
    
    Args:
        appPath: App import path (e.g., 'main:app')
        config: Launcher configuration
    
    Returns:
        Configured uvicorn.Config
    """
    kwargs = config.toUvicornKwargs()
    
    return uvicorn.Config(
        app=appPath,
        **kwargs,
    )


def preLaunchChecks(config: LauncherConfig) -> str:
    """
    Perform pre-launch checks.
    
    Args:
        config: Launcher configuration
    
    Returns:
        Resolved app path
    
    Raises:
        LaunchError: If checks fail
    """
    # Check port availability
    if isPortInUse(config.port, config.host):
        portInfo = getPortInfo(config.port)
        printPortConflict(config.port, portInfo.processName, portInfo.pid)
        raise LaunchError(f"Port {config.port} is already in use")
    
    # Resolve app path
    appPath = config.app
    projectDir = config.appDir or Path.cwd()
    
    if appPath is None:
        appPath = discoverApp(projectDir)
        if appPath is None:
            printErrorPanel(
                "App Not Found",
                "Could not auto-discover FastAPI app.",
                suggestions=[
                    "Create a main.py with 'app = FastAPI()'",
                    "Specify app path: fa dev --app main:app",
                    "Add to pyproject.toml: [tool.fastapi-launcher] app = 'main:app'",
                ],
            )
            raise LaunchError("Could not discover FastAPI app")
        printInfoMessage(f"Auto-discovered app: {appPath}")
    
    # Validate app path
    if not validateAppPath(appPath, projectDir):
        printErrorPanel(
            "Invalid App Path",
            f"Cannot import app from '{appPath}'",
            suggestions=[
                "Check that the module exists",
                "Ensure FastAPI is installed",
                "Verify the app variable name",
            ],
        )
        raise LaunchError(f"Cannot validate app path: {appPath}")
    
    return appPath


def launch(
    config: Optional[LauncherConfig] = None,
    cliArgs: Optional[dict] = None,
    mode: Optional[RunMode] = None,
    showBanner: bool = True,
) -> None:
    """
    Launch FastAPI server with uvicorn.
    
    Args:
        config: Pre-built configuration (if None, will load from sources)
        cliArgs: CLI arguments to merge into config
        mode: Override run mode
        showBanner: Whether to show startup banner
    
    Raises:
        LaunchError: If launch fails
    """
    # Load configuration if not provided
    if config is None:
        config = loadConfig(
            projectDir=Path.cwd(),
            cliArgs=cliArgs,
            mode=mode,
        )
    
    # Apply mode override
    if mode is not None:
        config = LauncherConfig(
            **{**config.model_dump(by_alias=False), "mode": mode}
        ).getEffectiveConfig()
    
    # Apply dev mode defaults
    if config.mode == RunMode.DEV and not config.reload:
        config = LauncherConfig(
            **{**config.model_dump(by_alias=False), "reload": True}
        )
    
    # Pre-launch checks
    appPath = preLaunchChecks(config)
    
    # Setup runtime directory
    runtimeDir = config.runtimeDir
    if not runtimeDir.is_absolute():
        runtimeDir = Path.cwd() / runtimeDir
    runtimeDir.mkdir(parents=True, exist_ok=True)
    
    # Write PID file
    pidFile = runtimeDir / "fa.pid"
    writePidFile(pidFile)
    
    # Add project directory to path
    projectDir = config.appDir or Path.cwd()
    projectDirStr = str(projectDir)
    if projectDirStr not in sys.path:
        sys.path.insert(0, projectDirStr)
    
    # Register signal handlers
    registerSignalHandlers()
    
    # Show startup banner
    if showBanner:
        printStartupPanel(
            LauncherConfig(**{**config.model_dump(by_alias=False), "app": appPath})
        )
    
    # Build uvicorn config
    uvicornConfig = buildUvicornConfig(appPath, config)
    
    # Run server
    try:
        server = uvicorn.Server(uvicornConfig)
        server.run()
    except Exception as e:
        printErrorPanel("Server Error", str(e))
        raise LaunchError(f"Server failed: {e}") from e
    finally:
        # Cleanup PID file
        if pidFile.exists():
            pidFile.unlink()


def launchDev(
    app: Optional[str] = None,
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = True,
    reloadDirs: Optional[list[str]] = None,
) -> None:
    """
    Launch in development mode.
    
    Args:
        app: App import path
        host: Bind host
        port: Bind port
        reload: Enable auto-reload
        reloadDirs: Directories to watch for reload
    """
    cliArgs = {
        "app": app,
        "host": host,
        "port": port,
        "reload": reload,
        "reload_dirs": reloadDirs,
    }
    
    launch(cliArgs=cliArgs, mode=RunMode.DEV)


def launchProd(
    app: Optional[str] = None,
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: int = 4,
    daemon: bool = False,
) -> None:
    """
    Launch in production mode.
    
    Args:
        app: App import path
        host: Bind host
        port: Bind port
        workers: Number of worker processes
        daemon: Run as daemon
    """
    cliArgs = {
        "app": app,
        "host": host,
        "port": port,
        "workers": workers,
        "daemon": daemon,
    }
    
    if daemon:
        from .daemon import daemonize
        daemonize()
    
    launch(cliArgs=cliArgs, mode=RunMode.PROD)
